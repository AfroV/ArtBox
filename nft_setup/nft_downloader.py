#!/usr/bin/env python3
"""
NFT Downloader and IPFS Pinner
Downloads NFT metadata and images, then pins them to IPFS
"""

import requests
import json
import os
import sys
import subprocess
from urllib.parse import urlparse
import argparse
from pathlib import Path

class NFTDownloader:
    def __init__(self, ipfs_api_url="http://127.0.0.1:5001"):
        self.ipfs_api_url = ipfs_api_url
        self.session = requests.Session()
        
    def get_token_uri(self, contract_address, token_id, rpc_url="https://eth-mainnet.public.blastapi.io"):
        """
        Get token URI from contract using JSON-RPC
        """
        # ERC-721 tokenURI function signature
        function_signature = "0xc87b56dd"  # tokenURI(uint256)
        token_id_hex = hex(int(token_id))[2:].zfill(64)
        data = function_signature + token_id_hex
        
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": [{
                "to": contract_address,
                "data": data
            }, "latest"],
            "id": 1
        }
        
        try:
            response = requests.post(rpc_url, json=payload)
            result = response.json()
            
            if 'result' in result and result['result'] != '0x':
                # Decode the result (remove 0x, convert hex to bytes, decode)
                hex_result = result['result'][2:]
                # Skip the first 64 chars (offset) and next 64 chars (length)
                # Then decode the actual string
                if len(hex_result) > 128:
                    string_hex = hex_result[128:]
                    # Remove trailing zeros and convert to string
                    string_bytes = bytes.fromhex(string_hex)
                    token_uri = string_bytes.decode('utf-8').rstrip('\x00')
                    return token_uri
        except Exception as e:
            print(f"Error getting token URI: {e}")
            
        return None
    
    def download_metadata(self, metadata_url):
        """
        Download NFT metadata from URL
        """
        try:
            # Handle IPFS URLs
            if metadata_url.startswith('ipfs://'):
                ipfs_hash = metadata_url.replace('ipfs://', '')
                metadata_url = f"https://ipfs.io/ipfs/{ipfs_hash}"
            
            response = self.session.get(metadata_url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error downloading metadata: {e}")
            return None
    
    def download_image(self, image_url, filename):
        """
        Download image from URL
        """
        try:
            # Handle IPFS URLs
            if image_url.startswith('ipfs://'):
                ipfs_hash = image_url.replace('ipfs://', '')
                image_url = f"https://ipfs.io/ipfs/{ipfs_hash}"
            
            response = self.session.get(image_url, timeout=60)
            response.raise_for_status()
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            return True
        except Exception as e:
            print(f"Error downloading image: {e}")
            return False
    
    def add_to_ipfs(self, file_path):
        """
        Add file to IPFS and return hash
        """
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{self.ipfs_api_url}/api/v0/add",
                    files=files
                )
                result = response.json()
                return result['Hash']
        except Exception as e:
            print(f"Error adding to IPFS: {e}")
            return None
    
    def pin_hash(self, ipfs_hash):
        """
        Pin IPFS hash
        """
        try:
            response = requests.post(
                f"{self.ipfs_api_url}/api/v0/pin/add",
                params={'arg': ipfs_hash}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error pinning hash: {e}")
            return False
    
    def add_to_mfs(self, ipfs_hash, mfs_path):
        """
        Add IPFS hash to MFS (Mutable File System) for WebUI visibility
        """
        try:
            response = requests.post(
                f"{self.ipfs_api_url}/api/v0/files/cp",
                params={
                    'arg': f'/ipfs/{ipfs_hash}',
                    'arg': mfs_path
                }
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error adding to MFS: {e}")
            return False
    
    def create_mfs_directory(self, dir_path):
        """
        Create directory in MFS
        """
        try:
            response = requests.post(
                f"{self.ipfs_api_url}/api/v0/files/mkdir",
                params={
                    'arg': dir_path,
                    'parents': 'true'
                }
            )
            return response.status_code == 200
        except Exception as e:
            # Directory might already exist, which is fine
            return True
    
    def process_nft(self, contract_address, token_id, output_dir="./nfts"):
        """
        Main function to process NFT: download metadata, image, and pin to IPFS
        """
        print(f"Processing NFT: {contract_address} #{token_id}")
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Create MFS directory for this NFT collection
        collection_name = contract_address[-8:]  # Use last 8 chars of contract address
        mfs_base_path = f"/nft_collections/{collection_name}"
        print(f"Creating MFS directory: {mfs_base_path}")
        self.create_mfs_directory(mfs_base_path)
        
        # Get token URI
        print("Getting token URI...")
        token_uri = self.get_token_uri(contract_address, token_id)
        if not token_uri:
            print("Failed to get token URI")
            return False
        
        print(f"Token URI: {token_uri}")
        
        # Download metadata
        print("Downloading metadata...")
        metadata = self.download_metadata(token_uri)
        if not metadata:
            print("Failed to download metadata")
            return False
        
        # Save metadata
        metadata_filename = f"{contract_address}_{token_id}_metadata.json"
        metadata_path = os.path.join(output_dir, metadata_filename)
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Metadata saved: {metadata_path}")
        
        # Download image if available
        image_hash = None
        if 'image' in metadata:
            image_url = metadata['image']
            print(f"Downloading image from: {image_url}")
            
            # Determine file extension
            parsed_url = urlparse(image_url)
            ext = os.path.splitext(parsed_url.path)[1] or '.png'
            
            image_filename = f"{contract_address}_{token_id}_image{ext}"
            image_path = os.path.join(output_dir, image_filename)
            
            if self.download_image(image_url, image_path):
                print(f"Image saved: {image_path}")
                
                # Add image to IPFS
                print("Adding image to IPFS...")
                image_hash = self.add_to_ipfs(image_path)
                if image_hash:
                    print(f"Image IPFS hash: {image_hash}")
                    
                    # Pin image
                    if self.pin_hash(image_hash):
                        print("Image pinned successfully")
                    else:
                        print("Failed to pin image")
                    
                    # Add image to MFS for WebUI visibility
                    file_ext = os.path.splitext(image_path)[1]
                    mfs_image_path = f"{mfs_base_path}/token_{token_id}_image{file_ext}"
                    if self.add_to_mfs(image_hash, mfs_image_path):
                        print(f"Image added to WebUI at: {mfs_image_path}")
                    else:
                        print("Failed to add image to WebUI")
        
        # Add metadata to IPFS
        print("Adding metadata to IPFS...")
        metadata_hash = self.add_to_ipfs(metadata_path)
        if metadata_hash:
            print(f"Metadata IPFS hash: {metadata_hash}")
            
            # Pin metadata
            if self.pin_hash(metadata_hash):
                print("Metadata pinned successfully")
            else:
                print("Failed to pin metadata")
            
            # Add metadata to MFS for WebUI visibility
            mfs_metadata_path = f"{mfs_base_path}/token_{token_id}_metadata.json"
            if self.add_to_mfs(metadata_hash, mfs_metadata_path):
                print(f"Metadata added to WebUI at: {mfs_metadata_path}")
            else:
                print("Failed to add metadata to WebUI")
        
        # Create summary
        summary = {
            "contract_address": contract_address,
            "token_id": token_id,
            "token_uri": token_uri,
            "metadata_hash": metadata_hash,
            "image_hash": image_hash,
            "metadata": metadata
        }
        
        summary_filename = f"{contract_address}_{token_id}_summary.json"
        summary_path = os.path.join(output_dir, summary_filename)
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"Summary saved: {summary_path}")
        print("✅ NFT processing completed!")
        print(f"🎨 View your NFT in WebUI at: http://127.0.0.1:5001/webui/")
        print(f"📁 Check the Files tab, look in: /nft_collections/{collection_name}/")
        
        return True

def main():
    parser = argparse.ArgumentParser(description='Download and pin NFT to IPFS')
    parser.add_argument('contract_address', help='NFT contract address')
    parser.add_argument('token_id', help='Token ID')
    parser.add_argument('--output-dir', default='./nfts', help='Output directory (default: ./nfts)')
    parser.add_argument('--ipfs-api', default='http://127.0.0.1:5001', help='IPFS API URL')
    parser.add_argument('--rpc-url', default='https://eth-mainnet.public.blastapi.io', help='Ethereum RPC URL')
    
    args = parser.parse_args()
    
    # Validate contract address
    if not args.contract_address.startswith('0x') or len(args.contract_address) != 42:
        print("Error: Contract address should be a valid Ethereum address (0x...)")
        sys.exit(1)
    
    # Create downloader instance
    downloader = NFTDownloader(ipfs_api_url=args.ipfs_api)
    
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