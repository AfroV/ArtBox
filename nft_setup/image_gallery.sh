#!/bin/bash

# IPFS Image Gallery Generator
# Creates an HTML gallery of all your IPFS images

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

show_banner() {
    echo -e "${BLUE}"
    echo "🖼️  IPFS Image Gallery Generator"
    echo "================================"
    echo -e "${NC}"
}

# Get local IP
get_local_ip() {
    LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1")
    echo "$LOCAL_IP"
}

# Find all NFT summary files
find_nft_files() {
    local nft_dirs=(
        "/opt/ipfs-data/nft_data"
        "/mnt/ssd/nft_data"
        "./nfts"
        "$HOME/nfts"
    )
    
    for dir in "${nft_dirs[@]}"; do
        if [ -d "$dir" ]; then
            find "$dir" -name "*summary.json" 2>/dev/null
        fi
    done
}

# Extract image hash from summary file
get_image_hash() {
    local summary_file="$1"
    if [ -f "$summary_file" ]; then
        python3 -c "
import json, sys
try:
    with open('$summary_file', 'r') as f:
        data = json.load(f)
    print(data.get('image_hash', ''))
except:
    pass
" 2>/dev/null
    fi
}

# Get NFT metadata from summary file
get_nft_info() {
    local summary_file="$1"
    if [ -f "$summary_file" ]; then
        python3 -c "
import json, sys
try:
    with open('$summary_file', 'r') as f:
        data = json.load(f)
    
    metadata = data.get('metadata', {})
    contract = data.get('contract_address', 'Unknown')
    token_id = data.get('token_id', 'Unknown')
    name = metadata.get('name', f'Token #{token_id}')
    description = metadata.get('description', 'No description')
    
    print(f'{contract}|{token_id}|{name}|{description}')
except:
    print('Unknown|Unknown|Unknown|Unknown')
" 2>/dev/null || echo "Unknown|Unknown|Unknown|Unknown"
    fi
}

# Create HTML gallery
create_html_gallery() {
    local output_file="$1"
    local gateway_url="$2"
    
    cat > "$output_file" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IPFS NFT Gallery</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            color: #333;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 3em;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            margin: 10px 0;
            opacity: 0.9;
        }
        
        .gallery {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .nft-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .nft-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }
        
        .nft-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s ease;
        }
        
        .nft-card:hover::before {
            left: 100%;
        }
        
        .nft-image {
            width: 100%;
            height: 250px;
            object-fit: cover;
            border-radius: 10px;
            margin-bottom: 15px;
            transition: transform 0.3s ease;
        }
        
        .nft-card:hover .nft-image {
            transform: scale(1.05);
        }
        
        .nft-title {
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #2c3e50;
        }
        
        .nft-description {
            color: #666;
            margin-bottom: 15px;
            line-height: 1.4;
            max-height: 60px;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .nft-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #eee;
        }
        
        .nft-token {
            background: #3498db;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }
        
        .nft-hash {
            font-family: monospace;
            font-size: 0.8em;
            color: #888;
            background: #f8f9fa;
            padding: 4px 8px;
            border-radius: 4px;
            max-width: 120px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .loading {
            text-align: center;
            color: white;
            font-size: 1.2em;
            margin: 50px 0;
        }
        
        .no-images {
            text-align: center;
            color: white;
            font-size: 1.5em;
            margin: 100px 0;
        }
        
        .stats {
            text-align: center;
            color: white;
            margin-bottom: 30px;
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }
        
        .view-options {
            text-align: center;
            margin: 20px 0;
        }
        
        .view-btn {
            background: rgba(255,255,255,0.2);
            color: white;
            border: 2px solid white;
            padding: 10px 20px;
            margin: 0 10px;
            border-radius: 25px;
            text-decoration: none;
            transition: all 0.3s ease;
            display: inline-block;
        }
        
        .view-btn:hover {
            background: white;
            color: #667eea;
            transform: scale(1.05);
        }
        
        @media (max-width: 768px) {
            .gallery {
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            body {
                padding: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🖼️ IPFS NFT Gallery</h1>
        <p>Your Personal NFT Collection</p>
    </div>
    
    <div class="view-options">
        <a href="GATEWAY_URL" class="view-btn" target="_blank">🌍 IPFS Gateway</a>
        <a href="WEBUI_URL" class="view-btn" target="_blank">🖥️ IPFS Web UI</a>
        <a href="#" onclick="location.reload()" class="view-btn">🔄 Refresh Gallery</a>
    </div>
    
    <div class="stats">
        <p>📊 Total NFTs: <span id="nft-count">Loading...</span> | 🖼️ Images: <span id="image-count">Loading...</span></p>
    </div>
    
    <div class="gallery" id="gallery">
        <div class="loading">Loading your NFT collection...</div>
    </div>

    <script>
        // NFT data will be inserted here
        const nftData = [
EOF

    # Add NFT data
    echo "        // NFT Data" >> "$output_file"
    
    local nft_count=0
    local image_count=0
    
    # Find all NFT files and add to HTML
    while IFS= read -r summary_file; do
        if [ -f "$summary_file" ]; then
            image_hash=$(get_image_hash "$summary_file")
            nft_info=$(get_nft_info "$summary_file")
            
            IFS='|' read -r contract token_id name description <<< "$nft_info"
            
            if [ -n "$image_hash" ] && [ "$image_hash" != "null" ]; then
                cat >> "$output_file" << EOF
        {
            contract: '$contract',
            tokenId: '$token_id',
            name: '$name',
            description: '$description',
            imageHash: '$image_hash',
            imageUrl: '${gateway_url}/ipfs/$image_hash'
        },
EOF
                ((image_count++))
            fi
            ((nft_count++))
        fi
    done < <(find_nft_files)
    
    # Continue HTML
    cat >> "$output_file" << EOF
        ];
        
        function renderGallery() {
            const gallery = document.getElementById('gallery');
            const nftCountEl = document.getElementById('nft-count');
            const imageCountEl = document.getElementById('image-count');
            
            nftCountEl.textContent = nftData.length;
            imageCountEl.textContent = nftData.filter(nft => nft.imageHash).length;
            
            if (nftData.length === 0) {
                gallery.innerHTML = '<div class="no-images">No NFTs found. Try downloading some NFTs first!</div>';
                return;
            }
            
            gallery.innerHTML = nftData.map(nft => {
                const shortHash = nft.imageHash ? nft.imageHash.substring(0, 12) + '...' : 'No image';
                const shortDescription = nft.description.length > 100 
                    ? nft.description.substring(0, 100) + '...' 
                    : nft.description;
                
                return \`
                    <div class="nft-card">
                        \${nft.imageHash ? 
                            \`<img src="\${nft.imageUrl}" alt="\${nft.name}" class="nft-image" 
                                onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                             <div style="display:none; height:250px; background:#f0f0f0; border-radius:10px; 
                                        display:flex; align-items:center; justify-content:center; color:#666;">
                                🖼️ Image not available
                             </div>\` :
                            \`<div style="height:250px; background:#f0f0f0; border-radius:10px; 
                                        display:flex; align-items:center; justify-content:center; color:#666;">
                                📄 Metadata Only
                             </div>\`
                        }
                        <div class="nft-title">\${nft.name}</div>
                        <div class="nft-description">\${shortDescription}</div>
                        <div class="nft-info">
                            <div class="nft-token">Token #\${nft.tokenId}</div>
                            <div class="nft-hash" title="\${nft.imageHash}">\${shortHash}</div>
                        </div>
                    </div>
                \`;
            }).join('');
        }
        
        // Render gallery when page loads
        document.addEventListener('DOMContentLoaded', renderGallery);
    </script>
</body>
</html>
EOF
    
    echo "$nft_count,$image_count"
}

# Generate simple list
create_simple_list() {
    print_header "📋 NFT Image List"
    
    local gateway_url="http://$(get_local_ip):8080"
    local count=0
    
    echo "Your IPFS NFT Images:"
    echo "===================="
    
    while IFS= read -r summary_file; do
        if [ -f "$summary_file" ]; then
            image_hash=$(get_image_hash "$summary_file")
            nft_info=$(get_nft_info "$summary_file")
            
            IFS='|' read -r contract token_id name description <<< "$nft_info"
            
            if [ -n "$image_hash" ] && [ "$image_hash" != "null" ]; then
                echo
                echo "🎨 $name (Token #$token_id)"
                echo "   📄 Contract: ${contract:0:10}..."
                echo "   🔗 Image URL: $gateway_url/ipfs/$image_hash"
                echo "   📋 Hash: $image_hash"
                ((count++))
            fi
        fi
    done < <(find_nft_files)
    
    if [ $count -eq 0 ]; then
        echo
        echo "❌ No images found. Try:"
        echo "   • Download an NFT: ipfs-tools download 0xcontract tokenid"
        echo "   • Check Web UI: http://$(get_local_ip):5001/webui/"
    else
        echo
        echo "✅ Found $count NFT images"
        echo "🌍 Gateway: $gateway_url/ipfs/"
        echo "🖥️ Web UI: http://$(get_local_ip):5001/webui/"
    fi
}

# Main execution
show_banner

echo "Choose how to view your IPFS images:"
echo "1. 🌐 Create HTML Gallery (opens in browser)"
echo "2. 📋 Simple list with URLs"
echo "3. 🖥️ Show Web UI and Gateway links"
echo

read -p "Choose option (1-3): " choice

case $choice in
    1)
        print_info "Creating HTML gallery..."
        
        gallery_file="/tmp/ipfs_nft_gallery.html"
        local_ip=$(get_local_ip)
        gateway_url="http://$local_ip:8080"
        webui_url="http://$local_ip:5001/webui/"
        
        # Create gallery
        counts=$(create_html_gallery "$gallery_file" "$gateway_url")
        nft_count=$(echo "$counts" | cut -d',' -f1)
        image_count=$(echo "$counts" | cut -d',' -f2)
        
        # Replace placeholders
        sed -i "s|GATEWAY_URL|$gateway_url|g" "$gallery_file"
        sed -i "s|WEBUI_URL|$webui_url|g" "$gallery_file"
        
        print_success "Gallery created: $gallery_file"
        print_info "Found $nft_count NFTs with $image_count images"
        print_info "Opening gallery in browser..."
        
        # Try to open in browser
        if command -v firefox >/dev/null; then
            firefox "$gallery_file" >/dev/null 2>&1 &
        elif command -v chromium-browser >/dev/null; then
            chromium-browser "$gallery_file" >/dev/null 2>&1 &
        else
            echo "Manual: Open file://$gallery_file in your browser"
        fi
        
        echo "🌐 Gallery URL: file://$gallery_file"
        echo "🔗 Direct access: $gateway_url/ipfs/"
        ;;
        
    2)
        create_simple_list
        ;;
        
    3)
        local_ip=$(get_local_ip)
        print_header "🌐 Access Your IPFS Images"
        echo
        echo "🖥️ IPFS Web UI (Best for browsing):"
        echo "   http://$local_ip:5001/webui/"
        echo "   • Click 'Files' tab"
        echo "   • Browse /nft_collections/"
        echo
        echo "🌍 IPFS Gateway (Direct image access):"
        echo "   http://$local_ip:8080/ipfs/YOUR_IMAGE_HASH"
        echo
        echo "📱 Command line:"
        echo "   ipfs files ls /nft_collections"
        echo
        ;;
        
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac