#!/bin/bash

# Script to locate IPFS NFT files and show access methods
# Helps users find their uploaded NFT files

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

show_banner() {
    echo -e "${BLUE}"
    echo "🔍 IPFS NFT File Locator"
    echo "========================"
    echo -e "${NC}"
}

check_ipfs_status() {
    print_header "📡 Checking IPFS Status"
    
    if ! curl -s http://127.0.0.1:5001/api/v0/version >/dev/null; then
        echo "❌ IPFS API not accessible"
        echo "Try: sudo systemctl start ipfs"
        exit 1
    fi
    
    print_success "IPFS API is accessible"
    echo
}

find_local_nft_files() {
    print_header "📁 Checking Local NFT Files"
    
    # Check possible locations
    locations=(
        "/opt/ipfs-data/nft_data"
        "/mnt/ssd/nft_data"
        "./nfts"
        "$HOME/nfts"
    )
    
    found_files=false
    
    for location in "${locations[@]}"; do
        if [ -d "$location" ]; then
            echo "📂 Checking: $location"
            files=$(find "$location" -name "*summary.json" 2>/dev/null | head -10)
            if [ -n "$files" ]; then
                found_files=true
                echo "$files" | while read -r file; do
                    if [ -f "$file" ]; then
                        echo "  📄 $(basename "$file")"
                        # Extract contract and token from filename
                        basename_file=$(basename "$file")
                        if [[ "$basename_file" =~ ^0x[a-fA-F0-9]+_[0-9]+_summary\.json$ ]]; then
                            # Extract contract and token from filename
                            contract=$(echo "$basename_file" | cut -d'_' -f1)
                            token_id=$(echo "$basename_file" | cut -d'_' -f2)
                            echo "      Contract: $contract"
                            echo "      Token ID: $token_id"
                        fi
                    fi
                done
            else
                echo "  (no NFT files found)"
            fi
            echo
        fi
    done
    
    if [ "$found_files" = false ]; then
        print_warning "No local NFT summary files found"
    fi
}

check_ipfs_mfs() {
    print_header "🗂️  Checking IPFS MFS (Web UI Files)"
    
    print_info "Checking IPFS MFS root directory..."
    
    # List MFS root
    mfs_response=$(curl -s -X POST "http://127.0.0.1:5001/api/v0/files/ls?arg=/" 2>/dev/null || echo "")
    
    if [ -n "$mfs_response" ]; then
        echo "MFS Root contents:"
        echo "$mfs_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'Entries' in data:
        for entry in data['Entries']:
            print(f\"  📁 {entry['Name']} ({entry['Type']})\"")
    else:
        print('  (empty or error)')
except:
    print('  (could not parse response)')
" 2>/dev/null || echo "  (could not parse MFS response)"
    else
        print_warning "Could not access MFS"
    fi
    
    echo
    
    # Check for nft_collections directory
    print_info "Checking for nft_collections directory..."
    nft_collections_response=$(curl -s -X POST "http://127.0.0.1:5001/api/v0/files/ls?arg=/nft_collections" 2>/dev/null || echo "error")
    
    if [[ "$nft_collections_response" != "error" ]] && [[ "$nft_collections_response" != *"file does not exist"* ]]; then
        echo "📁 NFT Collections found:"
        echo "$nft_collections_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'Entries' in data:
        for entry in data['Entries']:
            print(f\"  📂 {entry['Name']}/\")
            # Try to list contents of each collection
            import subprocess
            try:
                result = subprocess.run([
                    'curl', '-s', '-X', 'POST', 
                    f'http://127.0.0.1:5001/api/v0/files/ls?arg=/nft_collections/{entry[\"Name\"]}'
                ], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    collection_data = json.loads(result.stdout)
                    if 'Entries' in collection_data:
                        for item in collection_data['Entries']:
                            print(f\"    📄 {item['Name']}\")
            except:
                pass
    else:
        print('  (no collections found)')
except Exception as e:
    print(f'  (error reading collections: {e})')
" 2>/dev/null || echo "  (could not parse collections)"
    else
        print_warning "No nft_collections directory found in MFS"
    fi
    
    echo
}

check_pinned_hashes() {
    print_header "📌 Checking Pinned IPFS Hashes"
    
    print_info "Recent pinned hashes (last 10):"
    
    # Get pinned hashes
    pins_response=$(curl -s -X POST "http://127.0.0.1:5001/api/v0/pin/ls?type=recursive" 2>/dev/null || echo "")
    
    if [ -n "$pins_response" ]; then
        echo "$pins_response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'Keys' in data:
        count = 0
        for hash_key, info in data['Keys'].items():
            if count >= 10:
                break
            print(f\"  📎 {hash_key}\")
            count += 1
        if len(data['Keys']) > 10:
            print(f\"  ... and {len(data['Keys']) - 10} more\")
    else:
        print('  (no pinned hashes found)')
except:
    print('  (could not parse pinned hashes)')
" 2>/dev/null || echo "  (could not parse pins response)"
    else
        print_warning "Could not retrieve pinned hashes"
    fi
    
    echo
}

show_access_methods() {
    print_header "🌐 How to Access Your NFT Files"
    
    # Get local IP
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    
    echo "1. 🖥️  IPFS Web UI (Recommended):"
    echo "   • Open: http://$LOCAL_IP:5001/webui/"
    echo "   • Or: http://127.0.0.1:5001/webui/"
    echo "   • Click 'Files' tab"
    echo "   • Look in /nft_collections/ folder"
    echo
    
    echo "2. 🌍 IPFS Gateway (for images):"
    echo "   • Base URL: http://$LOCAL_IP:8080/ipfs/"
    echo "   • Add IPFS hash after the URL"
    echo "   • Example: http://$LOCAL_IP:8080/ipfs/QmYourHashHere"
    echo
    
    echo "3. 📱 Command Line Access:"
    echo "   • List MFS: ipfs files ls /"
    echo "   • List collections: ipfs files ls /nft_collections"
    echo "   • Get file: ipfs files read /path/to/file"
    echo
    
    echo "4. 🔍 Search Commands:"
    echo "   • Find NFT files: ipfs-tools cleanup --list"
    echo "   • Show status: ipfs-tools status"
    echo "   • Manual search: find /opt/ipfs-data/nft_data -name '*summary.json'"
    echo
}

provide_troubleshooting() {
    print_header "🔧 Troubleshooting"
    
    echo "If you can't find your NFT files:"
    echo
    echo "1. ✅ Check if IPFS is running:"
    echo "   sudo systemctl status ipfs"
    echo
    echo "2. 🔄 Restart IPFS if needed:"
    echo "   sudo systemctl restart ipfs"
    echo
    echo "3. 📋 Check recent downloads:"
    echo "   ls -la /opt/ipfs-data/nft_data/"
    echo "   ls -la /mnt/ssd/nft_data/"
    echo
    echo "4. 🔍 Search for any JSON files:"
    echo "   find / -name '*0xbf182081*' 2>/dev/null"
    echo "   find / -name '*summary.json' 2>/dev/null"
    echo
    echo "5. 📱 Check IPFS logs:"
    echo "   sudo journalctl -u ipfs -f"
    echo
    echo "6. 🎨 Re-download the NFT:"
    echo "   ipfs-tools download 0xbf182081a47e7fe15896e7b6eb2c6ba5c7be5b8c 1"
    echo
}

# Main execution
show_banner
check_ipfs_status
find_local_nft_files
check_ipfs_mfs
check_pinned_hashes
show_access_methods
provide_troubleshooting

echo "🎯 Quick Access Links:"
echo "================================"
LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1")
echo "🖥️  Web UI: http://$LOCAL_IP:5001/webui/"
echo "🌍 Gateway: http://$LOCAL_IP:8080/ipfs/"
echo "📁 Files Tab: Click 'Files' in Web UI, then browse /nft_collections/"