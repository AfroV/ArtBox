#!/bin/bash

# NFT Downloader Troubleshooting Script
# This script diagnoses and fixes the NFT downloader setup
# Especially for Async files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_header "NFT Downloader Diagnosis"

# Check current setup
print_status "Checking current NFT downloader setup..."

# 1. Check if enhanced downloader exists
if [ -f "/opt/ipfs-tools/nft_downloader.py" ]; then
    print_status "✅ NFT downloader exists at /opt/ipfs-tools/nft_downloader.py"
    
    # Check if it's the enhanced version
    if grep -q "EnhancedNFTDownloader" /opt/ipfs-tools/nft_downloader.py; then
        print_status "✅ Enhanced version detected"
        ENHANCED_VERSION=true
    elif grep -q "Basic NFT processor" /opt/ipfs-tools/nft_downloader.py; then
        print_warning "⚠️  Basic placeholder version detected"
        ENHANCED_VERSION=false
    else
        print_warning "⚠️  Unknown version detected"
        ENHANCED_VERSION=false
    fi
else
    print_error "❌ NFT downloader not found at /opt/ipfs-tools/nft_downloader.py"
    ENHANCED_VERSION=false
fi

# 2. Check ipfs-tools wrapper
print_status "Checking ipfs-tools wrapper..."
if [ -f "/usr/local/bin/ipfs-tools" ]; then
    print_status "✅ ipfs-tools wrapper exists"
    
    # Check what it's calling
    if grep -q "nft_downloader.py" /usr/local/bin/ipfs-tools; then
        print_status "✅ Wrapper references nft_downloader.py"
    else
        print_warning "⚠️  Wrapper may not be configured correctly"
    fi
else
    print_error "❌ ipfs-tools wrapper not found"
fi

# 3. Check Python environment
print_status "Checking Python environment..."
if [ -f "/opt/ipfs-tools/venv/bin/python3" ]; then
    print_status "✅ Virtual environment exists"
    PYTHON_CMD="/opt/ipfs-tools/venv/bin/python3"
elif command -v python3 &> /dev/null; then
    print_status "✅ System Python3 available"
    PYTHON_CMD="python3"
else
    print_error "❌ No Python3 found"
    exit 1
fi

# 4. Test the current downloader
print_status "Testing current downloader with simple command..."
echo "Running: $PYTHON_CMD /opt/ipfs-tools/nft_downloader.py --help"
if $PYTHON_CMD /opt/ipfs-tools/nft_downloader.py --help 2>/dev/null; then
    print_status "✅ Downloader responds to --help"
else
    print_error "❌ Downloader failed to respond"
fi

# 5. Check IPFS connection
print_status "Checking IPFS connection..."
if curl -s -X POST http://127.0.0.1:5001/api/v0/version >/dev/null 2>&1; then
    print_status "✅ IPFS daemon is accessible"
else
    print_warning "⚠️  IPFS daemon may not be running"
fi

print_header "Diagnosis Results"

if [ "$ENHANCED_VERSION" = true ]; then
    print_status "✅ Enhanced NFT downloader is installed"
    print_status "The issue may be with execution or environment"
    
    print_header "Testing Enhanced Downloader"
    print_status "Let's test the enhanced version directly..."
    
    echo "Testing with the problematic NFT..."
    echo "Command: $PYTHON_CMD /opt/ipfs-tools/nft_downloader.py 0xb6dae651468e9593e4581705a09c10a76ac1e0c8 343 --output-dir /tmp/nft_test"
    
    # Create test directory
    mkdir -p /tmp/nft_test
    chown $USER:$USER /tmp/nft_test 2>/dev/null || true
    
    if $PYTHON_CMD /opt/ipfs-tools/nft_downloader.py 0xb6dae651468e9593e4581705a09c10a76ac1e0c8 343 --output-dir /tmp/nft_test; then
        print_status "✅ Enhanced downloader works directly!"
        print_status "Issue is with the ipfs-tools wrapper"
        
        print_header "Fixing ipfs-tools Wrapper"
        
        # Backup current wrapper
        cp /usr/local/bin/ipfs-tools /usr/local/bin/ipfs-tools.backup
        
        # Create fixed wrapper
        cat > /usr/local/bin/ipfs-tools << 'EOF'
#!/bin/bash
# Fixed ipfs-tools wrapper

# Activate virtual environment if it exists
if [ -f "/opt/ipfs-tools/venv/bin/activate" ]; then
    source /opt/ipfs-tools/venv/bin/activate 2>/dev/null || true
fi

# Set Python command
if [ -f "/opt/ipfs-tools/venv/bin/python3" ]; then
    PYTHON_CMD="/opt/ipfs-tools/venv/bin/python3"
else
    PYTHON_CMD="python3"
fi

case "$1" in
    "status")
        if [ -f "/opt/ipfs-tools/ipfs_health_monitor.py" ]; then
            $PYTHON_CMD /opt/ipfs-tools/ipfs_health_monitor.py
        else
            $PYTHON_CMD /opt/ipfs-tools/ipfs_status.py
        fi
        ;;
    "download")
        shift
        if [ -f "/opt/ipfs-tools/nft_downloader.py" ]; then
            $PYTHON_CMD /opt/ipfs-tools/nft_downloader.py "$@"
        else
            echo "NFT downloader not installed"
            exit 1
        fi
        ;;
    "csv")
        shift
        if [ -f "/opt/ipfs-tools/process_nft_csv.py" ]; then
            $PYTHON_CMD /opt/ipfs-tools/process_nft_csv.py "$@"
        else
            echo "CSV processor not installed"
            exit 1
        fi
        ;;
    *)
        echo "IPFS Tools for Raspberry Pi"
        echo "Usage: ipfs-tools [command] [options]"
        echo ""
        echo "Commands:"
        echo "  status              Check IPFS node health"
        echo "  download <contract> <token_id>  Download single NFT"
        echo "  csv <file.csv>      Process NFTs from CSV file"
        echo ""
        echo "Examples:"
        echo "  ipfs-tools status"
        echo "  ipfs-tools download 0x1234... 1"
        echo "  ipfs-tools csv nfts.csv"
        ;;
esac
EOF
        
        chmod +x /usr/local/bin/ipfs-tools
        print_status "✅ Fixed ipfs-tools wrapper"
        
    else
        print_error "❌ Enhanced downloader failed - need to install/fix it"
        NEED_INSTALL=true
    fi
    
else
    print_warning "Basic or missing NFT downloader detected"
    NEED_INSTALL=true
fi

if [ "${NEED_INSTALL:-false}" = true ]; then
    print_header "Installing Enhanced NFT Downloader"
    
    # Check if we have the enhanced version in current directory
    if [ -f "./enhanced_nft_downloader.py" ]; then
        print_status "Found enhanced_nft_downloader.py in current directory"
        cp ./enhanced_nft_downloader.py /opt/ipfs-tools/nft_downloader.py
    elif [ -f "./nft_downloader.py" ] && grep -q "EnhancedNFTDownloader" ./nft_downloader.py; then
        print_status "Found enhanced nft_downloader.py in current directory"
        cp ./nft_downloader.py /opt/ipfs-tools/nft_downloader.py
    else
        print_status "Creating enhanced NFT downloader..."
        
        # Create the enhanced downloader directly
        cat > /opt/ipfs-tools/nft_downloader.py << 'ENHANCED_EOF'
#!/usr/bin/env python3
"""
Enhanced NFT Downloader for Complex Metadata with Nested IPFS Hashes
Quick fix version for immediate deployment
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
        
        # Set headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
        })
        
    def is_ipfs_reference(self, value):
        """Check if string is IPFS hash or URI"""
        if not isinstance(value, str):
            return False
        if value.startswith('ipfs://'):
            return True
        if re.match(r'^Qm[1-9A-HJ-NP-Za-km-z]{44}$', value):
            return True
        return False
    
    def normalize_ipfs_uri(self, uri):
        """Convert IPFS URI to hash"""
        if uri.startswith('ipfs://'):
            return uri.replace('ipfs://', '')
        return uri
    
    def get_token_uri(self, contract_address, token_id):
        """Get token URI from contract"""
        function_signature = "0xc87b56dd"
        token_id_hex = hex(int(token_id))[2:].zfill(64)
        data = function_signature + token_id_hex
        
        rpc_endpoints = [
            "https://eth-mainnet.public.blastapi.io",
            "https://ethereum.publicnode.com",
            "https://rpc.ankr.com/eth"
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
    
    def download_from_uri(self, uri, filename):
        """Download content from URI with gateway fallbacks"""
        # Fix the URI format issue
        if uri and '://' not in uri and self.is_ipfs_reference(uri):
            uri = f"ipfs://{uri}"
        
        ipfs_hash = self.normalize_ipfs_uri(uri)
        
        gateways = [
            f"https://ipfs.io/ipfs/{ipfs_hash}",
            f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}",
            f"https://cloudflare-ipfs.com/ipfs/{ipfs_hash}",
        ]
        
        for gateway_url in gateways:
            try:
                response = self.session.get(gateway_url, timeout=30)
                if response.status_code == 200:
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    return True
            except Exception:
                continue
        return False
    
    def extract_all_uris(self, data, uris=None):
        """Extract all IPFS URIs from metadata"""
        if uris is None:
            uris = set()
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and self.is_ipfs_reference(value):
                    uris.add(value)
                else:
                    self.extract_all_uris(value, uris)
        elif isinstance(data, list):
            for item in data:
                self.extract_all_uris(item, uris)
        elif isinstance(data, str) and self.is_ipfs_reference(data):
            uris.add(data)
        
        return uris
    
    def process_nft(self, contract_address, token_id, output_dir="./nfts"):
        """Process NFT with enhanced URI handling"""
        print(f"🎨 Processing Enhanced NFT: {contract_address} #{token_id}")
        
        # Ensure output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Get token URI
        print("   📡 Getting token URI...")
        token_uri = self.get_token_uri(contract_address, token_id)
        if not token_uri:
            print("   ❌ Failed to get token URI")
            return False
        
        print(f"   📋 Token URI: {token_uri}")
        
        # Download metadata
        print("   📥 Downloading metadata...")
        metadata_path = os.path.join(output_dir, f"{contract_address}_{token_id}_metadata.json")
        
        if self.download_from_uri(token_uri, metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                print("   ✅ Metadata downloaded successfully")
            except Exception as e:
                print(f"   ❌ Failed to parse metadata: {e}")
                return False
        else:
            print("   ❌ Failed to download metadata")
            return False
        
        # Extract all URIs
        print("   🔍 Extracting all asset URIs...")
        all_uris = self.extract_all_uris(metadata)
        print(f"   📊 Found {len(all_uris)} unique asset URIs")
        
        # Download all assets
        downloaded_count = 0
        for i, uri in enumerate(all_uris, 1):
            ipfs_hash = self.normalize_ipfs_uri(uri)
            print(f"   📥 Asset {i}/{len(all_uris)}: {ipfs_hash[:12]}...")
            
            # Determine extension
            ext = '.png'  # Default
            if 'json' in uri.lower():
                ext = '.json'
            elif any(x in uri.lower() for x in ['.jpg', '.jpeg']):
                ext = '.jpg'
            elif '.gif' in uri.lower():
                ext = '.gif'
            
            asset_filename = f"{contract_address}_{token_id}_asset_{i:03d}_{ipfs_hash[:12]}{ext}"
            asset_path = os.path.join(output_dir, asset_filename)
            
            if self.download_from_uri(uri, asset_path):
                print(f"   💾 Saved: {asset_filename}")
                downloaded_count += 1
            else:
                print(f"   ❌ Failed to download asset {i}")
        
        print(f"   ✅ Processing completed!")
        print(f"   📊 Downloaded {downloaded_count}/{len(all_uris)} assets")
        
        return True

def main():
    parser = argparse.ArgumentParser(description='Enhanced NFT downloader')
    parser.add_argument('contract_address', help='NFT contract address')
    parser.add_argument('token_id', help='Token ID')
    parser.add_argument('--output-dir', default='/opt/ipfs-data/nft_data', help='Output directory')
    
    args = parser.parse_args()
    
    if not args.contract_address.startswith('0x') or len(args.contract_address) != 42:
        print("❌ Error: Invalid contract address")
        sys.exit(1)
    
    downloader = EnhancedNFTDownloader()
    success = downloader.process_nft(args.contract_address, args.token_id, args.output_dir)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
ENHANCED_EOF
    fi
    
    # Set permissions
    chmod +x /opt/ipfs-tools/nft_downloader.py
    chown ipfs:ipfs /opt/ipfs-tools/nft_downloader.py 2>/dev/null || true
    
    print_status "✅ Enhanced NFT downloader installed"
fi

print_header "Final Test"
print_status "Testing the fixed setup..."

# Test the problematic NFT again
mkdir -p /tmp/nft_test_final
echo "Running: ipfs-tools download 0xb6dae651468e9593e4581705a09c10a76ac1e0c8 343"

if sudo ipfs-tools download 0xb6dae651468e9593e4581705a09c10a76ac1e0c8 343; then
    print_status "🎉 SUCCESS! Enhanced downloader is working"
    print_status ""
    print_status "You can now:"
    print_status "  - Process single NFTs: ipfs-tools download <contract> <token_id>"
    print_status "  - Process your CSV: ipfs-tools csv nfts.csv"
    print_status "  - Check status: ipfs-tools status"
else
    print_error "❌ Still having issues. Manual debugging needed."
    print_status ""
    print_status "For manual debugging:"
    print_status "  1. Check IPFS: sudo systemctl status ipfs"
    print_status "  2. Test Python: $PYTHON_CMD /opt/ipfs-tools/nft_downloader.py --help"
    print_status "  3. Check permissions: ls -la /opt/ipfs-tools/"
fi

print_header "Diagnosis Complete"