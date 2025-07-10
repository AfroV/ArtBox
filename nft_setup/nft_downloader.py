#!/usr/bin/env python3
"""
Advanced NFT Downloader with Multi-Asset Support
Handles complex metadata with multiple URIs, layered images, and dynamic NFTs
"""

import requests
import json
import os
import sys
import subprocess
import time
import random
from urllib.parse import urlparse
import argparse
from pathlib import Path
import re

class AdvancedNFTDownloader:
    def __init__(self, ipfs_api_url="http://127.0.0.1:5001"):
        self.ipfs_api_url = ipfs_api_url
        self.session = requests.Session()
        self.downloaded_hashes = set()  # Track downloaded hashes to avoid duplicates
        
        # Setup retry logic
        from requests.adapters import HTTPAdapter
        try:
            from urllib3.util.retry import Retry
            
            retry_strategy = Retry(
                total=3,
                status_forcelist=[429, 500, 502, 503, 504, 530],
                method_whitelist=["HEAD", "GET", "OPTIONS"],
                backoff_factor=1
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)
        except ImportError:
            pass  # Fallback for older urllib3 versions
        
        # Set browser-like headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
    def extract_all_uris(self, data, uris=None):
        """
        Recursively extract all IPFS URIs from metadata
        Handles nested structures, arrays, and various URI formats
        """
        if uris is None:
            uris = set()
        
        if isinstance(data, dict):
            for key, value in data.items():
                # Check if this looks like an IPFS hash or URI
                if isinstance(value, str):
                    if self.is_ipfs_reference(value):
                        uris.add(value)
                else:
                    # Recursively search nested structures
                    self.extract_all_uris(value, uris)
                    
        elif isinstance(data, list):
            for item in data:
                self.extract_all_uris(item, uris)
                
        elif isinstance(data, str):
            if self.is_ipfs_reference(data):
                uris.add(data)
        
        return uris
    
    def is_ipfs_reference(self, value):
        """
        Check if a string is an IPFS hash or URI
        """
        if not isinstance(value, str):
            return False
            
        # Check for ipfs:// URIs
        if value.startswith('ipfs://'):
            return True
            
        # Check for bare IPFS hashes (Qm... or other CID formats)
        if re.match(r'^Qm[1-9A-HJ-NP-Za-km-z]{44}$', value):
            return True
            
        # Check for newer CID formats (base32, base58)
        if re.match(r'^[a-z2-7]{59}$', value) or re.match(r'^[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{46,59}$', value):
            return True
            
        return False
    
    def normalize_ipfs_uri(self, uri):
        """
        Convert various IPFS URI formats to consistent hash
        """
        if uri.startswith('ipfs://'):
            return uri.replace('ipfs://', '')
        return uri
    
    def get_token_uri(self, contract_address, token_id):
        """Get token URI from contract using multiple RPC endpoints"""
        function_signature = "0xc87b56dd"  # tokenURI(uint256)
        token_id_hex = hex(int(token_id))[2:].zfill(64)
        data = function_signature + token_id_hex
        
        rpc_endpoints = [
            "https://eth-mainnet.public.blastapi.io",
            "https://ethereum.publicnode.com",
            "https://rpc.ankr.com/eth",
            "https://eth.llamarpc.com"
        ]
        
        for rpc_url in rpc_endpoints:
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_call",
                    "params": [{
                        "to": contract_address,
                        "data": data
                    }, "latest"],
                    "id": 1
                }
                
                response = self.session.post(rpc_url, json=payload, timeout=15)
                result = response.json()
                
                if 'result' in result and result['result'] != '0x':
                    hex_result = result['result'][2:]
                    if len(hex_result) > 128:
                        string_hex = hex_result[128:]
                        string_bytes = bytes.fromhex(string_hex)
                        token_uri = string_bytes.decode('utf-8').rstrip('\x00')
                        return token_uri
                        
            except Exception as e:
                print(f"   ⚠️  RPC {rpc_url} failed: {e}")
                continue
                
        return None
    
    def download_from_uri(self, uri, filename, retries=3):
        """
        Download content from URI with multiple gateway fallbacks
        """
        # Normalize the URI
        ipfs_hash = self.normalize_ipfs_uri(uri)
        
        # Multiple IPFS gateways
        if self.is_ipfs_reference(uri):
            gateways = [
                f"https://ipfs.io/ipfs/{ipfs_hash}",
                f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}",
                f"https://cloudflare-ipfs.com/ipfs/{ipfs_hash}",
                f"https://dweb.link/ipfs/{ipfs_hash}",
                f"https://gateway.ipfs.io/ipfs/{ipfs_hash}"
            ]
        else:
            gateways = [uri]
        
        for attempt in range(retries):
            for gateway_url in gateways:
                try:
                    if attempt > 0:
                        delay = random.uniform(0.5, 2.0)
                        time.sleep(delay)
                    
                    response = self.session.get(gateway_url, timeout=30)
                    
                    if response.status_code == 200:
                        with open(filename, 'wb') as f:
                            f.write(response.content)
                        return True, ipfs_hash
                    elif response.status_code in [530, 503, 502]:
                        print(f"   ⚠️  Server error ({response.status_code}), trying next gateway...")
                        continue
                    else:
                        print(f"   ⚠️  HTTP {response.status_code}, trying next gateway...")
                        continue
                        
                except requests.exceptions.Timeout:
                    print(f"   ⚠️  Timeout, trying next gateway...")
                    continue
                except Exception as e:
                    print(f"   ⚠️  Error: {e}")
                    continue
        
        return False, None
    
    def download_metadata(self, metadata_url, retries=3):
            # Handle bare IPFS hashes

        if metadata_url and not '://' in metadata_url:
         if re.match(r'^Qm[1-9A-HJ-NP-Za-km-z]{44}$', metadata_url):
            metadata_url = f"ipfs://{metadata_url}"
        """Download NFT metadata with retry logic"""
        for attempt in range(retries):
            success, _ = self.download_from_uri(metadata_url, '/tmp/temp_metadata.json', retries=1)
            if success:
                try:
                    with open('/tmp/temp_metadata.json', 'r') as f:
                        metadata = json.load(f)
                    os.remove('/tmp/temp_metadata.json')
                    return metadata
                except json.JSONDecodeError:
                    print(f"   ⚠️  Invalid JSON, attempt {attempt + 1}")
                    continue
                except Exception as e:
                    print(f"   ⚠️  Error reading metadata: {e}")
                    continue
        
        return None
    
    def add_to_ipfs(self, file_path):
        """Add file to IPFS and return hash"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{self.ipfs_api_url}/api/v0/add",
                    files=files,
                    timeout=30
                )
                result = response.json()
                return result['Hash']
        except Exception as e:
            print(f"   ⚠️  IPFS add error: {e}")
            return None
    
    def pin_hash(self, ipfs_hash):
        """Pin IPFS hash"""
        try:
            response = requests.post(
                f"{self.ipfs_api_url}/api/v0/pin/add",
                params={'arg': ipfs_hash},
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            print(f"   ⚠️  IPFS pin error: {e}")
            return False
    
    def ensure_writable_output_dir(self, output_dir):
        """Ensure output directory is writable"""
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            test_file = os.path.join(output_dir, 'test_write.tmp')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            return output_dir
        except PermissionError:
            fallback_dir = os.path.expanduser("~/nft_data")
            print(f"   ⚠️  Permission denied for {output_dir}, using {fallback_dir}")
            Path(fallback_dir).mkdir(parents=True, exist_ok=True)
            return fallback_dir
    
    def determine_file_extension(self, uri, content_type=None, default='.png'):
        """
        Determine appropriate file extension for downloaded content
        """
        # Try to get extension from URI
        parsed_uri = urlparse(uri)
        ext = os.path.splitext(parsed_uri.path)[1]
        if ext and ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.mp4', '.mov', '.json']:
            return ext
        
        # Try to determine from content type
        if content_type:
            content_type_map = {
                'image/png': '.png',
                'image/jpeg': '.jpg',
                'image/gif': '.gif',
                'image/svg+xml': '.svg',
                'image/webp': '.webp',
                'video/mp4': '.mp4',
                'video/quicktime': '.mov',
                'application/json': '.json'
            }
            if content_type in content_type_map:
                return content_type_map[content_type]
        
        return default
    
    def process_nft(self, contract_address, token_id, output_dir="./nfts"):
        """
        Main function to process NFT with multi-asset support
        """
        print(f"🎨 Processing NFT: {contract_address} #{token_id}")
        
        # Ensure output directory is writable
        output_dir = self.ensure_writable_output_dir(output_dir)
        
        # Get token URI
        print("   📡 Getting token URI...")
        token_uri = self.get_token_uri(contract_address, token_id)
        if not token_uri:
            print("   ❌ Failed to get token URI")
            return False
        
        print(f"   📋 Token URI: {token_uri}")
        
        # Download metadata
        print("   📥 Downloading metadata...")
        metadata = self.download_metadata(token_uri)
        if not metadata:
            print("   ❌ Failed to download metadata")
            return False
        
        # Save metadata
        metadata_filename = f"{contract_address}_{token_id}_metadata.json"
        metadata_path = os.path.join(output_dir, metadata_filename)
        
        try:
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"   💾 Metadata saved: {metadata_path}")
        except Exception as e:
            print(f"   ❌ Failed to save metadata: {e}")
            return False
        
        # Extract all URIs from metadata
        print("   🔍 Extracting all asset URIs...")
        all_uris = self.extract_all_uris(metadata)
        print(f"   📊 Found {len(all_uris)} unique asset URIs")
        
        downloaded_assets = {}
        asset_hashes = {}
        
        # Download all assets
        for i, uri in enumerate(all_uris, 1):
            ipfs_hash = self.normalize_ipfs_uri(uri)
            
            # Skip if already downloaded
            if ipfs_hash in self.downloaded_hashes:
                print(f"   ⏭️  Asset {i}/{len(all_uris)}: {ipfs_hash[:12]}... (already downloaded)")
                continue
            
            print(f"   📥 Asset {i}/{len(all_uris)}: {ipfs_hash[:12]}...")
            
            # Try to determine file type
            ext = self.determine_file_extension(uri)
            asset_filename = f"{contract_address}_{token_id}_asset_{i:03d}_{ipfs_hash[:12]}{ext}"
            asset_path = os.path.join(output_dir, asset_filename)
            
            success, actual_hash = self.download_from_uri(uri, asset_path)
            
            if success:
                print(f"   💾 Saved: {asset_filename}")
                downloaded_assets[uri] = {
                    'filename': asset_filename,
                    'path': asset_path,
                    'hash': actual_hash or ipfs_hash
                }
                
                # Add to IPFS and pin
                print(f"   📎 Adding to IPFS...")
                local_hash = self.add_to_ipfs(asset_path)
                if local_hash:
                    print(f"   🔗 IPFS hash: {local_hash}")
                    asset_hashes[uri] = local_hash
                    if self.pin_hash(local_hash):
                        print(f"   📌 Pinned successfully")
                    self.downloaded_hashes.add(ipfs_hash)
                else:
                    print(f"   ⚠️  Failed to add to IPFS")
            else:
                print(f"   ❌ Failed to download: {uri[:50]}...")
        
        # Add metadata to IPFS
        print("   📎 Adding metadata to IPFS...")
        metadata_hash = self.add_to_ipfs(metadata_path)
        if metadata_hash:
            print(f"   🔗 Metadata IPFS hash: {metadata_hash}")
            if self.pin_hash(metadata_hash):
                print("   📌 Metadata pinned successfully")
        
        # Create comprehensive summary
        summary = {
            "contract_address": contract_address,
            "token_id": token_id,
            "token_uri": token_uri,
            "metadata_hash": metadata_hash,
            "metadata": metadata,
            "assets": downloaded_assets,
            "asset_hashes": asset_hashes,
            "total_assets": len(all_uris),
            "downloaded_assets": len(downloaded_assets),
            "download_timestamp": time.time(),
            "all_uris": list(all_uris)  # For reference
        }
        
        # Extract primary image for compatibility
        primary_image_hash = None
        if 'image' in metadata:
            primary_image_hash = asset_hashes.get(metadata['image'])
        
        if primary_image_hash:
            summary['image_hash'] = primary_image_hash
        
        summary_filename = f"{contract_address}_{token_id}_summary.json"
        summary_path = os.path.join(output_dir, summary_filename)
        
        try:
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            print(f"   📋 Summary saved: {summary_path}")
        except Exception as e:
            print(f"   ⚠️  Failed to save summary: {e}")
        
        print(f"   ✅ NFT processing completed!")
        print(f"   📊 Downloaded {len(downloaded_assets)}/{len(all_uris)} assets")
        
        if len(downloaded_assets) < len(all_uris):
            failed_count = len(all_uris) - len(downloaded_assets)
            print(f"   ⚠️  {failed_count} assets failed to download")
        
        return True

def main():
    parser = argparse.ArgumentParser(description='Advanced NFT downloader with multi-asset support')
    parser.add_argument('contract_address', help='NFT contract address')
    parser.add_argument('token_id', help='Token ID')
    parser.add_argument('--output-dir', default='/opt/ipfs-data/nft_data', help='Output directory')
    parser.add_argument('--ipfs-api', default='http://127.0.0.1:5001', help='IPFS API URL')
    
    args = parser.parse_args()
    
    # Validate contract address
    if not args.contract_address.startswith('0x') or len(args.contract_address) != 42:
        print("❌ Error: Contract address should be a valid Ethereum address (0x...)")
        sys.exit(1)
    
    # Create downloader instance
    downloader = AdvancedNFTDownloader(ipfs_api_url=args.ipfs_api)
    
    # Process NFT
    success = downloader.process_nft(
        args.contract_address,
        args.token_id,
        args.output_dir
    )
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()