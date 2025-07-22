#!/usr/bin/env python3
"""
Enhanced NFT Downloader for Complex Metadata with Nested IPFS Hashes
Complete version with bare IPFS hash fix
"""

import requests
import json
import os
import sys
import time
import random
from urllib.parse import urlparse
import argparse
from pathlib import Path
import re

class EnhancedNFTDownloader:
    def __init__(self, ipfs_api_url="http://127.0.0.1:5001"):
        self.ipfs_api_url = ipfs_api_url
        self.session = requests.Session()
        self.downloaded_hashes = set()
        self.uri_context = {}
        
        # Setup session with headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        })
        
    def extract_all_uris(self, data, uris=None, context_path=""):
        """Recursively extract all IPFS URIs with context tracking"""
        if uris is None:
            uris = set()
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{context_path}.{key}" if context_path else key
                
                if isinstance(value, str):
                    if self.is_ipfs_reference(value):
                        uris.add(value)
                        self.uri_context[value] = {
                            'path': current_path,
                            'type': self.classify_uri_type(key, current_path)
                        }
                else:
                    self.extract_all_uris(value, uris, current_path)
                    
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{context_path}[{i}]" if context_path else f"[{i}]"
                self.extract_all_uris(item, uris, current_path)
                
        elif isinstance(data, str):
            if self.is_ipfs_reference(data):
                uris.add(data)
                self.uri_context[data] = {'path': context_path, 'type': 'unknown'}
        
        return uris
    
    def classify_uri_type(self, key, path):
        """Classify URI type based on key and path"""
        key_lower = key.lower()
        path_lower = path.lower()
        
        if 'image' in key_lower or 'image' in path_lower:
            return 'primary_image'
        elif 'background' in path_lower:
            return 'background_layer'
        elif 'layer' in path_lower or 'states' in path_lower:
            return 'layer_asset'
        elif 'animation' in key_lower or 'video' in key_lower:
            return 'animation'
        elif 'uri' in key_lower and 'options' in path_lower:
            return 'layer_option'
        else:
            return 'metadata_asset'
    
    def is_ipfs_reference(self, value):
        """Enhanced IPFS hash detection"""
        if not isinstance(value, str):
            return False
            
        if value.startswith('ipfs://'):
            return True
            
        # Check for Qm... hashes (most common)
        if re.match(r'^Qm[1-9A-HJ-NP-Za-km-z]{44}$', value):
            return True
            
        # Check for newer CID formats
        if re.match(r'^b[a-z2-7]{58}$', value):
            return True
            
        return False
    
    def normalize_ipfs_uri(self, uri):
        """Convert IPFS URI formats to hash"""
        if uri.startswith('ipfs://'):
            return uri.replace('ipfs://', '')
        return uri
    
    def get_token_uri(self, contract_address, token_id):
        """Get token URI using multiple RPC endpoints"""
        function_signature = "0xc87b56dd"
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
                    "params": [{"to": contract_address, "data": data}, "latest"],
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
        """Download content with multiple gateway fallbacks and bare hash fix"""
        # CRITICAL FIX: Handle bare IPFS hashes
        if uri and '://' not in uri and self.is_ipfs_reference(uri):
            uri = f"ipfs://{uri}"
            
        ipfs_hash = self.normalize_ipfs_uri(uri)
        
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
                        time.sleep(random.uniform(0.5, 2.0))
                    
                    response = self.session.get(gateway_url, timeout=30)
                    
                    if response.status_code == 200:
                        with open(filename, 'wb') as f:
                            f.write(response.content)
                        return True, ipfs_hash, response.headers.get('content-type')
                    elif response.status_code in [530, 503, 502]:
                        continue
                        
                except Exception:
                    continue
        
        return False, None, None
    
    def download_metadata(self, metadata_url, retries=3):
        """Download NFT metadata with retry logic and bare hash fix"""
        # Handle bare IPFS hashes
        if metadata_url and '://' not in metadata_url:
            if re.match(r'^Qm[1-9A-HJ-NP-Za-km-z]{44}$', metadata_url):
                metadata_url = f"ipfs://{metadata_url}"
        
        for attempt in range(retries):
            success, _, _ = self.download_from_uri(metadata_url, '/tmp/temp_metadata.json', retries=1)
            if success:
                try:
                    with open('/tmp/temp_metadata.json', 'r') as f:
                        metadata = json.load(f)
                    os.remove('/tmp/temp_metadata.json')
                    return metadata
                except Exception:
                    continue
        
        return None
    
    def add_to_ipfs(self, file_path):
        """Add file to IPFS and return hash"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(f"{self.ipfs_api_url}/api/v0/add", files=files, timeout=30)
                result = response.json()
                return result['Hash']
        except Exception as e:
            print(f"   ⚠️  IPFS add error: {e}")
            return None
    
    def pin_hash(self, ipfs_hash):
        """Pin IPFS hash"""
        try:
            response = requests.post(f"{self.ipfs_api_url}/api/v0/pin/add", 
                                   params={'arg': ipfs_hash}, timeout=30)
            return response.status_code == 200
        except Exception:
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
        """Determine appropriate file extension"""
        parsed_uri = urlparse(uri)
        ext = os.path.splitext(parsed_uri.path)[1]
        if ext and ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.mp4', '.mov', '.json']:
            return ext
        
        if content_type:
            content_type_map = {
                'image/png': '.png', 'image/jpeg': '.jpg', 'image/gif': '.gif',
                'image/svg+xml': '.svg', 'image/webp': '.webp', 'video/mp4': '.mp4',
                'video/quicktime': '.mov', 'application/json': '.json'
            }
            if content_type in content_type_map:
                return content_type_map[content_type]
        
        return default
    
    def generate_asset_filename(self, contract_address, token_id, uri, asset_index, context_info=None):
        """Generate descriptive filename based on context"""
        ipfs_hash = self.normalize_ipfs_uri(uri)
        hash_short = ipfs_hash[:12]
        
        if context_info and 'type' in context_info:
            asset_type = context_info['type']
            
            if asset_type == 'primary_image':
                base_name = f"{contract_address}_{token_id}_primary_image_{hash_short}"
            elif asset_type == 'background_layer':
                base_name = f"{contract_address}_{token_id}_background_{asset_index:03d}_{hash_short}"
            elif asset_type in ['layer_asset', 'layer_option']:
                base_name = f"{contract_address}_{token_id}_layer_{asset_index:03d}_{hash_short}"
            elif asset_type == 'animation':
                base_name = f"{contract_address}_{token_id}_animation_{hash_short}"
            else:
                base_name = f"{contract_address}_{token_id}_asset_{asset_index:03d}_{hash_short}"
        else:
            base_name = f"{contract_address}_{token_id}_asset_{asset_index:03d}_{hash_short}"
        
        return base_name
    
    def analyze_metadata_structure(self, metadata):
        """Analyze and report on metadata structure"""
        analysis = {
            'has_async_attributes': 'async-attributes' in metadata,
            'has_layout': 'layout' in metadata,
            'has_layers': False,
            'layer_count': 0,
            'structure_type': 'simple'
        }
        
        if 'layout' in metadata and 'layers' in metadata['layout']:
            analysis['has_layers'] = True
            analysis['layer_count'] = len(metadata['layout']['layers'])
            analysis['structure_type'] = 'layered'
            
            uri_count = 0
            for layer in metadata['layout']['layers']:
                if 'states' in layer and 'options' in layer['states']:
                    uri_count += len(layer['states']['options'])
            analysis['layer_uri_count'] = uri_count
        
        return analysis
    
    def process_nft(self, contract_address, token_id, output_dir="./nfts"):
        """Enhanced NFT processing with better organization"""
        print(f"🎨 Processing Enhanced NFT: {contract_address} #{token_id}")
        
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
        
        # Analyze metadata structure
        analysis = self.analyze_metadata_structure(metadata)
        print(f"   🔍 Metadata Analysis:")
        print(f"       Structure Type: {analysis['structure_type']}")
        if analysis['has_layers']:
            print(f"       Layer Count: {analysis['layer_count']}")
        if analysis['has_async_attributes']:
            print(f"       Has Async Attributes: Yes")
        
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
        
        # Clear context for this NFT
        self.uri_context = {}
        
        # Extract all URIs
        print("   🔍 Extracting all asset URIs with context...")
        all_uris = self.extract_all_uris(metadata)
        print(f"   📊 Found {len(all_uris)} unique asset URIs")
        
        # Group URIs by type
        uri_types = {}
        for uri in all_uris:
            context = self.uri_context.get(uri, {})
            uri_type = context.get('type', 'unknown')
            if uri_type not in uri_types:
                uri_types[uri_type] = []
            uri_types[uri_type].append(uri)
        
        print("   📊 URI Distribution:")
        for uri_type, uris in uri_types.items():
            print(f"       {uri_type}: {len(uris)} URIs")
        
        downloaded_assets = {}
        asset_hashes = {}
        failed_downloads = []
        
        # Download all assets
        for i, uri in enumerate(all_uris, 1):
            ipfs_hash = self.normalize_ipfs_uri(uri)
            
            if ipfs_hash in self.downloaded_hashes:
                print(f"   ⏭️  Asset {i}/{len(all_uris)}: {ipfs_hash[:12]}... (already downloaded)")
                continue
            
            context_info = self.uri_context.get(uri, {})
            asset_type = context_info.get('type', 'unknown')
            
            print(f"   📥 Asset {i}/{len(all_uris)}: {ipfs_hash[:12]}... ({asset_type})")
            
            # Generate filename
            base_filename = self.generate_asset_filename(contract_address, token_id, uri, i, context_info)
            temp_path = os.path.join(output_dir, f"temp_{base_filename}")
            success, actual_hash, content_type = self.download_from_uri(uri, temp_path)
            
            if success:
                # Determine extension and rename
                ext = self.determine_file_extension(uri, content_type)
                final_filename = f"{base_filename}{ext}"
                final_path = os.path.join(output_dir, final_filename)
                os.rename(temp_path, final_path)
                
                print(f"   💾 Saved: {final_filename}")
                downloaded_assets[uri] = {
                    'filename': final_filename,
                    'path': final_path,
                    'hash': actual_hash or ipfs_hash,
                    'type': asset_type,
                    'content_type': content_type
                }
                
                # Add to IPFS and pin
                print(f"   📎 Adding to IPFS...")
                local_hash = self.add_to_ipfs(final_path)
                if local_hash:
                    print(f"   🔗 IPFS hash: {local_hash}")
                    asset_hashes[uri] = local_hash
                    if self.pin_hash(local_hash):
                        print(f"   📌 Pinned successfully")
                    self.downloaded_hashes.add(ipfs_hash)
            else:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                print(f"   ❌ Failed to download: {uri[:50]}...")
                failed_downloads.append({'uri': uri, 'type': asset_type})
        
        # Add metadata to IPFS
        print("   📎 Adding metadata to IPFS...")
        metadata_hash = self.add_to_ipfs(metadata_path)
        if metadata_hash:
            print(f"   🔗 Metadata IPFS hash: {metadata_hash}")
            if self.pin_hash(metadata_hash):
                print("   📌 Metadata pinned successfully")
        
        # Create summary
        summary = {
            "contract_address": contract_address,
            "token_id": token_id,
            "token_uri": token_uri,
            "metadata_hash": metadata_hash,
            "metadata": metadata,
            "metadata_analysis": analysis,
            "assets": downloaded_assets,
            "asset_hashes": asset_hashes,
            "failed_downloads": failed_downloads,
            "total_uris_found": len(all_uris),
            "successful_downloads": len(downloaded_assets),
            "failed_downloads_count": len(failed_downloads),
            "download_timestamp": time.time(),
            "all_uris": list(all_uris),
            "uri_context_map": self.uri_context
        }
        
        # Extract primary image hash for compatibility
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
        
        if failed_downloads:
            print(f"   ⚠️  {len(failed_downloads)} assets failed to download")
        
        # Report by asset type
        if downloaded_assets:
            type_counts = {}
            for asset in downloaded_assets.values():
                asset_type = asset.get('type', 'unknown')
                type_counts[asset_type] = type_counts.get(asset_type, 0) + 1
            
            print("   📊 Downloaded by type:")
            for asset_type, count in type_counts.items():
                print(f"       {asset_type}: {count} assets")
        
        return True

def main():
    parser = argparse.ArgumentParser(description='Enhanced NFT downloader for complex/dynamic NFTs')
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
    downloader = EnhancedNFTDownloader(ipfs_api_url=args.ipfs_api)
    
    # Process NFT
    success = downloader.process_nft(args.contract_address, args.token_id, args.output_dir)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()