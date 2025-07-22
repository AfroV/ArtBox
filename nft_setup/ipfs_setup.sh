#!/bin/bash

# IPFS Setup Script for Raspberry Pi - Single SSD Version with Improved File Copying
# This script installs and configures IPFS (Kubo) on Raspberry Pi OS
# Designed for setups where everything runs from one SSD

set -e

# Configuration - Paths adjusted for single SSD setup
IPFS_VERSION="v0.35.0"
IPFS_USER="ipfs"
IPFS_HOME="/opt/ipfs"
IPFS_BASE_DIR="/opt/ipfs-data"
IPFS_DATA_DIR="/opt/ipfs-data/ipfs"
NFT_DATA_DIR="/opt/ipfs-data/nft_data"
BACKUP_DIR="/opt/ipfs-data/backups"
SCRIPT_DIR="/opt/ipfs-tools"

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
    echo -e "${BLUE}$1${NC}"
}

# Improved file copying function
copy_management_script() {
    local script_name="$1"
    local description="$2"
    local is_required="${3:-false}"
    
    print_status "Looking for $script_name..."
    
    # Check multiple possible locations
    local script_path=""
    local search_paths=(
        "./$script_name"                    # Current directory
        "$(dirname "$0")/$script_name"      # Same directory as setup script
        "$HOME/nft_setup/$script_name"      # Common location
        "/tmp/$script_name"                 # Temporary location
    )
    
    for path in "${search_paths[@]}"; do
        if [ -f "$path" ]; then
            script_path="$path"
            print_status "Found $script_name at: $path"
            break
        fi
    done
    
    if [ -n "$script_path" ]; then
        # Attempt to copy the file
        if cp "$script_path" "$SCRIPT_DIR/"; then
            chmod +x "$SCRIPT_DIR/$script_name"
            chown ipfs:ipfs "$SCRIPT_DIR/$script_name"
            print_status "✅ $description installed successfully"
            return 0
        else
            print_error "Failed to copy $script_name to $SCRIPT_DIR/"
            if [ "$is_required" = "true" ]; then
                return 1
            fi
        fi
    else
        if [ "$is_required" = "true" ]; then
            print_error "$script_name not found in any expected location"
            print_status "Searched in:"
            for path in "${search_paths[@]}"; do
                print_status "  - $path"
            done
            return 1
        else
            print_warning "$script_name not found - will create basic version"
        fi
    fi
    
    return 0
}

# Function to create a basic NFT downloader if original not found
create_basic_nft_downloader() {
    print_status "Creating basic NFT downloader..."
    
    cat > "$SCRIPT_DIR/nft_downloader.py" << 'EOF'
#!/usr/bin/env python3
"""
Basic NFT Downloader and IPFS Pinner
Downloads NFT metadata and images, then pins them to IPFS
"""

import requests
import json
import os
import sys
import argparse
from pathlib import Path
from urllib.parse import urlparse

class NFTDownloader:
    def __init__(self, ipfs_api_url="http://127.0.0.1:5001"):
        self.ipfs_api_url = ipfs_api_url
        self.session = requests.Session()
        
    def get_token_uri(self, contract_address, token_id):
        """Get token URI from contract - simplified version"""
        # This is a basic implementation - the full version has more robust RPC calls
        print(f"Note: Using basic token URI detection for {contract_address} #{token_id}")
        print("For full functionality, copy the complete nft_downloader.py")
        return None
        
    def process_nft(self, contract_address, token_id, output_dir="/opt/ipfs-data/nft_data"):
        """Basic NFT processing"""
        print(f"Basic NFT processor - processing {contract_address} #{token_id}")
        print("This is a placeholder. Copy the full nft_downloader.py for complete functionality.")
        return False

def main():
    parser = argparse.ArgumentParser(description='Basic NFT downloader (placeholder)')
    parser.add_argument('contract_address', help='NFT contract address')
    parser.add_argument('token_id', help='Token ID')
    parser.add_argument('--output-dir', default='/opt/ipfs-data/nft_data', help='Output directory')
    
    args = parser.parse_args()
    
    print("⚠️  This is a basic placeholder NFT downloader.")
    print("To get full functionality:")
    print("1. Copy the complete nft_downloader.py to /opt/ipfs-tools/")
    print("2. Run: sudo chmod +x /opt/ipfs-tools/nft_downloader.py")
    print("3. Run: sudo chown ipfs:ipfs /opt/ipfs-tools/nft_downloader.py")

if __name__ == "__main__":
    main()
EOF
    
    chmod +x "$SCRIPT_DIR/nft_downloader.py"
    chown ipfs:ipfs "$SCRIPT_DIR/nft_downloader.py"
    print_status "Basic NFT downloader created (copy full version for complete functionality)"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Show where we're running from
print_status "Setup script location: $(realpath "$0")"
print_status "Current working directory: $(pwd)"
print_status "Looking for management scripts..."

# Check available space and confirm we're on SSD
print_status "Checking storage setup..."
ROOT_DEVICE=$(df / | tail -1 | awk '{print $1}' | sed 's/[0-9]*$//')
AVAILABLE_GB=$(df / | tail -1 | awk '{print $4}')
AVAILABLE_GB_HUMAN=$(df -h / | tail -1 | awk '{print $4}')

print_status "Root device: $ROOT_DEVICE"
print_status "Available space: $AVAILABLE_GB_HUMAN"

# Check if it's an SSD (non-rotational)
if [ -f "/sys/block/$(basename $ROOT_DEVICE)/queue/rotational" ]; then
    ROTATIONAL=$(cat "/sys/block/$(basename $ROOT_DEVICE)/queue/rotational")
    if [ "$ROTATIONAL" = "0" ]; then
        print_status "Confirmed: Running on SSD storage"
    else
        print_warning "Warning: Storage appears to be rotational (HDD/SD card)"
    fi
fi

# Check minimum space requirement (10GB)
if [ "$AVAILABLE_GB" -lt 10485760 ]; then  # Less than 10GB in KB
    print_warning "Less than 10GB available space ($AVAILABLE_GB_HUMAN)"
    print_warning "IPFS works better with more storage space"
    echo -n "Continue anyway? (y/N): "
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

print_status "Starting IPFS installation..."

# Update system
print_status "Updating system packages..."
apt update && apt upgrade -y

# Install dependencies
print_status "Installing dependencies..."
apt install -y curl wget python3 python3-pip python3-venv python3-full git smartmontools

# Create ipfs user
print_status "Creating IPFS user..."
if ! id "$IPFS_USER" &>/dev/null; then
    useradd -r -m -d "$IPFS_HOME" -s /bin/bash "$IPFS_USER"
fi

# Create directories
print_status "Creating directories..."
mkdir -p "$IPFS_HOME" "$IPFS_BASE_DIR" "$IPFS_DATA_DIR" "$NFT_DATA_DIR" "$BACKUP_DIR" "$SCRIPT_DIR"
chown -R "$IPFS_USER:$IPFS_USER" "$IPFS_HOME" "$IPFS_BASE_DIR"

# Create compatibility symlink for scripts that expect /mnt/ssd
print_status "Creating compatibility symlink..."
if [ ! -e "/mnt/ssd" ]; then
    mkdir -p /mnt
    ln -sf "$IPFS_BASE_DIR" "/mnt/ssd"
    print_status "Created symlink: /mnt/ssd -> $IPFS_BASE_DIR"
elif [ ! -L "/mnt/ssd" ]; then
    print_warning "/mnt/ssd exists but is not a symlink - leaving as is"
fi

# Download and install IPFS
print_status "Downloading IPFS Kubo $IPFS_VERSION..."
cd /tmp
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ]; then
    IPFS_ARCH="linux-arm64"
elif [ "$ARCH" = "armv7l" ]; then
    IPFS_ARCH="linux-arm"
else
    IPFS_ARCH="linux-amd64"
fi

IPFS_FILE="kubo_${IPFS_VERSION}_${IPFS_ARCH}.tar.gz"
wget "https://github.com/ipfs/kubo/releases/download/${IPFS_VERSION}/${IPFS_FILE}"

print_status "Installing IPFS..."
tar -xzf "$IPFS_FILE"
mv kubo/ipfs /usr/local/bin/
chmod +x /usr/local/bin/ipfs
rm -rf kubo "$IPFS_FILE"

# Initialize IPFS as the ipfs user
print_status "Initializing IPFS..."
sudo -u "$IPFS_USER" bash << EOF
export IPFS_PATH="$IPFS_DATA_DIR"
/usr/local/bin/ipfs init
/usr/local/bin/ipfs config Addresses.API /ip4/0.0.0.0/tcp/5001
/usr/local/bin/ipfs config Addresses.Gateway /ip4/0.0.0.0/tcp/8080
/usr/local/bin/ipfs config --json API.HTTPHeaders.Access-Control-Allow-Origin '["*"]'
/usr/local/bin/ipfs config --json API.HTTPHeaders.Access-Control-Allow-Methods '["PUT", "GET", "POST"]'
EOF

# Create systemd service
print_status "Creating systemd service..."
cat > /etc/systemd/system/ipfs.service << EOF
[Unit]
Description=IPFS daemon
After=network.target

[Service]
Type=notify
User=$IPFS_USER
Group=$IPFS_USER
Environment=IPFS_PATH=$IPFS_DATA_DIR
ExecStart=/usr/local/bin/ipfs daemon --enable-gc
Restart=always
RestartSec=5
KillSignal=SIGINT

[Install]
WantedBy=multi-user.target
EOF

# Enable and start IPFS service
print_status "Enabling IPFS service..."
systemctl daemon-reload
systemctl enable ipfs

# Try to start IPFS service
print_status "Starting IPFS service..."
if systemctl start ipfs; then
    print_status "IPFS service started successfully"
else
    print_warning "IPFS service failed to start - will continue with setup"
fi

# Wait for IPFS to start
print_status "Waiting for IPFS to initialize..."
sleep 10

# Install Python dependencies
print_status "Setting up Python environment..."
python3 -m venv "$SCRIPT_DIR/venv"

# Activate virtual environment and install packages
print_status "Installing Python dependencies..."
"$SCRIPT_DIR/venv/bin/pip" install requests psutil

# Copy management scripts using improved function
print_header "Installing Management Scripts"

# Try to copy advanced scripts first
copy_management_script "nft_downloader.py" "NFT Downloader" false
if [ ! -f "$SCRIPT_DIR/nft_downloader.py" ]; then
    create_basic_nft_downloader
fi

copy_management_script "ipfs_health_monitor.py" "Advanced Health Monitor" false
copy_management_script "ipfs_backup_restore.sh" "Backup & Restore Tools" false
copy_management_script "ssd_optimization.sh" "SSD Optimization Tools" false
copy_management_script "ssd_health_monitor.py" "SSD Health Monitor" false

# List what was found and copied
print_status "Management scripts status:"
ls -la "$SCRIPT_DIR"/*.py "$SCRIPT_DIR"/*.sh 2>/dev/null | while read -r line; do
    print_status "  $line"
done

# Create IPFS status script
print_status "Creating IPFS status script..."
cat > "$SCRIPT_DIR/ipfs_status.py" << 'EOF'
#!/usr/bin/env python3
import subprocess
import sys
import requests
import json

def check_ipfs_daemon():
    try:
        # Use POST instead of GET, just like the working curl command
        response = requests.post('http://127.0.0.1:5001/api/v0/version', timeout=15)
        if response.status_code == 200:
            version_info = response.json()
            print(f"✅ IPFS daemon is running")
            print(f"Version: {version_info['Version']}")
            print(f"System: {version_info.get('System', 'Unknown')}")
            print(f"Golang: {version_info.get('Golang', 'Unknown')}")
            return True
    except requests.exceptions.ConnectionError:
        print("❌ IPFS daemon is not running (connection refused)")
    except requests.exceptions.Timeout:
        print("❌ IPFS daemon is not responding (timeout)")
    except Exception as e:
        print(f"❌ IPFS daemon error: {e}")
    
    return False

def check_ipfs_service():
    try:
        result = subprocess.run(['systemctl', 'is-active', 'ipfs'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ IPFS service is active")
            return True
        else:
            print("❌ IPFS service is not active")
            return False
    except:
        print("❌ Could not check IPFS service status")
        return False

def get_ipfs_stats():
    try:
        # Use POST for stats endpoints too
        response = requests.post('http://127.0.0.1:5001/api/v0/stats/repo', timeout=15)
        if response.status_code == 200:
            stats = response.json()
            print(f"📊 Repository stats:")
            print(f"  Storage: {stats.get('RepoSize', 0) / 1024 / 1024:.2f} MB")
            print(f"  Objects: {stats.get('NumObjects', 0):,}")
        
        response = requests.post('http://127.0.0.1:5001/api/v0/swarm/peers', timeout=15)
        if response.status_code == 200:
            peers = response.json()
            peer_count = len(peers.get('Peers', []))
            print(f"  Connected peers: {peer_count}")
            
            # Show connection status
            if peer_count > 0:
                print("  🌐 Connected to IPFS network")
            else:
                print("  ⚠️  Not connected to any peers yet (this is normal at startup)")
    except Exception as e:
        print(f"❌ Could not get IPFS stats: {e}")

def get_storage_info():
    try:
        result = subprocess.run(['df', '-h', '/opt/ipfs-data'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                print(f"💾 Storage info:")
                print(f"  Total: {parts[1]}")
                print(f"  Used: {parts[2]} ({parts[4]})")
                print(f"  Available: {parts[3]}")
    except:
        print("❌ Could not get storage info")

def test_ipfs_id():
    """Test IPFS ID command to verify full functionality"""
    try:
        response = requests.post('http://127.0.0.1:5001/api/v0/id', timeout=15)
        if response.status_code == 200:
            id_info = response.json()
            print(f"🆔 Node ID: {id_info.get('ID', 'Unknown')[:12]}...")
            addresses = id_info.get('Addresses', [])
            print(f"📡 Listening on {len(addresses)} addresses")
            return True
    except Exception as e:
        print(f"⚠️  Could not get node ID: {e}")
    return False

if __name__ == "__main__":
    print("🔍 IPFS Status Check")
    print("=" * 30)
    
    daemon_ok = check_ipfs_daemon()
    service_ok = check_ipfs_service()
    
    if daemon_ok:
        get_ipfs_stats()
        test_ipfs_id()
    
    get_storage_info()
    
    if daemon_ok:
        print("\n🌐 Web Interfaces:")
        print("  WebUI: http://127.0.0.1:5001/webui/")
        print("  Gateway: http://127.0.0.1:8080/ipfs/")
        print("\n✨ IPFS is ready to use!")
    else:
        print("\n🔧 Troubleshooting:")
        print("  Check service: sudo systemctl status ipfs")
        print("  View logs: sudo journalctl -u ipfs -f")
        print("  Restart: sudo systemctl restart ipfs")
        sys.exit(1)
EOF

# Create CSV NFT processor and cleanup scripts if NFT downloader exists
if [ -f "$SCRIPT_DIR/nft_downloader.py" ]; then
    # CSV processor
    cat > "$SCRIPT_DIR/process_nft_csv.py" << 'EOF'
#!/usr/bin/env python3
import csv
import sys
import os
import json
from pathlib import Path

# Add the script directory to path to import nft_downloader
sys.path.insert(0, '/opt/ipfs-tools')

try:
    from nft_downloader import EnhancedNFTDownloader
except ImportError:
    print("❌ Enhanced nft_downloader.py not found. Please ensure it's in /opt/ipfs-tools/")
    sys.exit(1)

def process_csv_file(csv_file, output_dir="/opt/ipfs-data/nft_data"):
    """Process NFTs from CSV file"""
    print(f"📁 Processing CSV file: {csv_file}")
    print(f"📂 Output directory: {output_dir}")
    
    downloader = EnhancedNFTDownloader()
    processed = 0
    failed = 0
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Read CSV file
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        
        # Expected columns: contract_address, token_id
        for row in reader:
            contract_address = row.get('contract_address', '').strip()
            token_id = row.get('token_id', '').strip()
            
            if not contract_address or not token_id:
                print(f"⚠️  Skipping row with missing data: {row}")
                continue
            
            print(f"\n🎨 Processing NFT: {contract_address} #{token_id}")
            
            try:
                success = downloader.process_nft(contract_address, token_id, output_dir)
                if success:
                    processed += 1
                    print(f"✅ Success: {contract_address} #{token_id}")
                else:
                    failed += 1
                    print(f"❌ Failed: {contract_address} #{token_id}")
            except Exception as e:
                failed += 1
                print(f"❌ Error processing {contract_address} #{token_id}: {e}")
    
    print(f"\n📊 Summary:")
    print(f"  ✅ Processed: {processed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  📁 Files saved to: {output_dir}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 process_nft_csv.py <csv_file>")
        print("\nCSV format should have columns: contract_address, token_id")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        sys.exit(1)
    
    process_csv_file(csv_file)
EOF

    # Cleanup script
    cat > "$SCRIPT_DIR/cleanup_nft.py" << 'EOF'
#!/usr/bin/env python3
import os
import sys
import json
import requests
from pathlib import Path
import argparse

def unpin_hash(ipfs_hash, ipfs_api_url="http://127.0.0.1:5001"):
    """Unpin IPFS hash"""
    try:
        response = requests.post(
            f"{ipfs_api_url}/api/v0/pin/rm",
            params={'arg': ipfs_hash}
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Error unpinning hash {ipfs_hash}: {e}")
        return False

def cleanup_nft(contract_address, token_id, data_dir="/opt/ipfs-data/nft_data"):
    """Clean up NFT files and IPFS pins"""
    print(f"🧹 Cleaning up NFT: {contract_address} #{token_id}")
    
    # Find summary file
    summary_file = os.path.join(data_dir, f"{contract_address}_{token_id}_summary.json")
    
    if os.path.exists(summary_file):
        try:
            with open(summary_file, 'r') as f:
                summary = json.load(f)
            
            # Unpin hashes
            if summary.get('metadata_hash'):
                print(f"📄 Unpinning metadata hash: {summary['metadata_hash']}")
                unpin_hash(summary['metadata_hash'])
            
            if summary.get('image_hash'):
                print(f"🖼️  Unpinning image hash: {summary['image_hash']}")
                unpin_hash(summary['image_hash'])
            
        except Exception as e:
            print(f"❌ Error reading summary file: {e}")
    
    # Remove local files
    patterns = [
        f"{contract_address}_{token_id}_metadata.json",
        f"{contract_address}_{token_id}_summary.json",
        f"{contract_address}_{token_id}_image.*"
    ]
    
    for pattern in patterns:
        if '*' in pattern:
            # Handle wildcard patterns
            base_pattern = pattern.replace('*', '')
            for file in Path(data_dir).glob(f"{base_pattern}*"):
                print(f"🗑️  Removing file: {file}")
                file.unlink()
        else:
            file_path = os.path.join(data_dir, pattern)
            if os.path.exists(file_path):
                print(f"🗑️  Removing file: {file_path}")
                os.remove(file_path)
    
    print(f"✅ Cleanup completed for {contract_address} #{token_id}")

def list_nfts(data_dir="/opt/ipfs-data/nft_data"):
    """List all NFTs in the data directory"""
    print("📋 NFTs in storage:")
    print("-" * 50)
    
    summary_files = list(Path(data_dir).glob("*_summary.json"))
    
    if not summary_files:
        print("No NFTs found")
        return
    
    for summary_file in summary_files:
        try:
            with open(summary_file, 'r') as f:
                summary = json.load(f)
            
            contract = summary.get('contract_address', 'Unknown')
            token_id = summary.get('token_id', 'Unknown')
            metadata_hash = summary.get('metadata_hash', 'N/A')
            image_hash = summary.get('image_hash', 'N/A')
            
            print(f"Contract: {contract}")
            print(f"Token ID: {token_id}")
            print(f"Metadata Hash: {metadata_hash}")
            print(f"Image Hash: {image_hash}")
            print("-" * 50)
            
        except Exception as e:
            print(f"Error reading {summary_file}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='NFT cleanup utility')
    parser.add_argument('--list', action='store_true', help='List all NFTs')
    parser.add_argument('--cleanup', nargs=2, metavar=('CONTRACT', 'TOKEN_ID'), 
                       help='Cleanup specific NFT')
    parser.add_argument('--data-dir', default='/opt/ipfs-data/nft_data', 
                       help='NFT data directory')
    
    args = parser.parse_args()
    
    if args.list:
        list_nfts(args.data_dir)
    elif args.cleanup:
        contract_address, token_id = args.cleanup
        cleanup_nft(contract_address, token_id, args.data_dir)
    else:
        parser.print_help()
EOF
fi

# Make scripts executable
chmod +x "$SCRIPT_DIR"/*.py
find "$SCRIPT_DIR" -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true

# Create command wrapper
cat > /usr/local/bin/ipfs-tools << 'EOF'
#!/bin/bash
source /opt/ipfs-tools/venv/bin/activate 2>/dev/null || true
case "$1" in
    "status")
        if [ -f "/opt/ipfs-tools/ipfs_health_monitor.py" ]; then
            python3 /opt/ipfs-tools/ipfs_health_monitor.py
        else
            python3 /opt/ipfs-tools/ipfs_status.py
        fi
        ;;
    "monitor")
        shift
        if [ -f "/opt/ipfs-tools/ipfs_health_monitor.py" ]; then
            python3 /opt/ipfs-tools/ipfs_health_monitor.py --continuous "$@"
        else
            echo "Health monitor not available"
        fi
        ;;
    "alerts")
        if [ -f "/opt/ipfs-tools/ipfs_health_monitor.py" ]; then
            python3 /opt/ipfs-tools/ipfs_health_monitor.py --alerts
        else
            echo "Health monitor not available"
        fi
        ;;
    "download")
        shift
        if [ -f "/opt/ipfs-tools/nft_downloader.py" ]; then
            python3 /opt/ipfs-tools/nft_downloader.py "$@"
        else
            echo "NFT downloader not installed"
        fi
        ;;
    "csv")
        shift
        if [ -f "/opt/ipfs-tools/process_nft_csv.py" ]; then
            python3 /opt/ipfs-tools/process_nft_csv.py "$@"
        else
            echo "CSV processor not installed"
        fi
        ;;
    "cleanup")
        shift
        if [ -f "/opt/ipfs-tools/cleanup_nft.py" ]; then
            python3 /opt/ipfs-tools/cleanup_nft.py "$@"
        else
            echo "Cleanup tool not installed"
        fi
        ;;
    "backup")
        shift
        if [ -f "/opt/ipfs-tools/ipfs_backup_restore.sh" ]; then
            /opt/ipfs-tools/ipfs_backup_restore.sh "$@"
        else
            echo "Backup script not available"
        fi
        ;;
    "ssd-health")
        if [ -f "/opt/ipfs-tools/ssd_health_monitor.py" ]; then
            python3 /opt/ipfs-tools/ssd_health_monitor.py
        else
            echo "SSD health monitor not available"
        fi
        ;;
    "ssd-optimize")
        if [ -f "/opt/ipfs-tools/ssd_optimization.sh" ]; then
            echo "SSD optimization requires root privileges"
            echo "Run: sudo /opt/ipfs-tools/ssd_optimization.sh"
        else
            echo "SSD optimization script not available"
        fi
        ;;
    *)
        echo "IPFS Tools for Raspberry Pi (Single SSD)"
        echo "Usage: ipfs-tools [command] [options]"
        echo ""
        echo "Status & Monitoring:"
        echo "  status                  Check IPFS node health"
        echo "  monitor <interval>      Continuous monitoring"
        echo "  alerts                  Check for alerts only"
        echo "  ssd-health              Check SSD health status"
        echo ""
        echo "NFT Management:"
        echo "  download <contract> <token_id>  Download single NFT"
        echo "  csv <file.csv>          Process NFTs from CSV file"
        echo "  cleanup --list          List all stored NFTs"
        echo "  cleanup --cleanup <contract> <token_id>  Remove NFT"
        echo ""
        echo "Backup & Restore:"
        echo "  backup backup           Create full backup"
        echo "  backup list             List available backups"
        echo ""
        echo "SSD Optimization:"
        echo "  ssd-health              Check SSD health and status"
        echo "  ssd-optimize            Run SSD optimization (requires sudo)"
        echo ""
        echo "Data Locations:"
        echo "  IPFS data: /opt/ipfs-data/ipfs"
        echo "  NFT data: /opt/ipfs-data/nft_data"
        echo "  Backups: /opt/ipfs-data/backups"
        echo "  Compatibility: /mnt/ssd -> /opt/ipfs-data"
        echo ""
        echo "Examples:"
        echo "  ipfs-tools status"
        echo "  ipfs-tools ssd-health"
        echo "  ipfs-tools monitor 60"
        echo "  ipfs-tools download 0x1234... 1"
        echo "  ipfs-tools csv nfts.csv"
        ;;
esac
EOF

chmod +x /usr/local/bin/ipfs-tools

# Set ownership
chown -R "$IPFS_USER:$IPFS_USER" "$SCRIPT_DIR" "$IPFS_BASE_DIR"

print_header "Installation Summary"
print_status "Installation completed successfully!"
print_status ""
print_status "📁 Data directories:"
print_status "  Base: $IPFS_BASE_DIR"
print_status "  IPFS data: $IPFS_DATA_DIR"
print_status "  NFT data: $NFT_DATA_DIR"
print_status "  Backups: $BACKUP_DIR"
print_status "  Scripts: $SCRIPT_DIR"
print_status ""
print_status "🔗 Compatibility:"
print_status "  /mnt/ssd -> $IPFS_BASE_DIR (symlink for other scripts)"
print_status ""

# Show what scripts were installed
print_status "📜 Installed Management Scripts:"
if [ -f "$SCRIPT_DIR/nft_downloader.py" ]; then
    if grep -q "Basic NFT processor" "$SCRIPT_DIR/nft_downloader.py"; then
        print_warning "  NFT Downloader: Basic version (copy full version for complete functionality)"
    else
        print_status "  ✅ NFT Downloader: Full version"
    fi
else
    print_warning "  NFT Downloader: Not installed"
fi

if [ -f "$SCRIPT_DIR/ipfs_health_monitor.py" ]; then
    print_status "  ✅ Advanced Health Monitor"
else
    print_status "  ⚠️  Basic Health Monitor only"
fi

if [ -f "$SCRIPT_DIR/ipfs_backup_restore.sh" ]; then
    print_status "  ✅ Backup & Restore Tools"
else
    print_warning "  Backup & Restore Tools: Not installed"
fi

if [ -f "$SCRIPT_DIR/ssd_optimization.sh" ]; then
    print_status "  ✅ SSD Optimization Tools"
else
    print_warning "  SSD Optimization Tools: Not installed"
fi

if [ -f "$SCRIPT_DIR/ssd_health_monitor.py" ]; then
    print_status "  ✅ SSD Health Monitor"
else
    print_warning "  SSD Health Monitor: Not installed"
fi

print_status ""
print_status "🔧 Management commands:"
print_status "  ipfs-tools status              - Check IPFS status"
print_status "  ipfs-tools download <contract> <token_id> - Download single NFT"
print_status "  ipfs-tools csv <file.csv>      - Process CSV file"
print_status "  ipfs-tools cleanup --list      - List stored NFTs"
print_status ""
print_status "🌐 Web interfaces:"
print_status "  IPFS WebUI: http://127.0.0.1:5001/webui/"
print_status "  IPFS Gateway: http://127.0.0.1:8080/ipfs/"
print_status ""
print_status "📋 Service management:"
print_status "  sudo systemctl start ipfs      - Start IPFS"
print_status "  sudo systemctl stop ipfs       - Stop IPFS"
print_status "  sudo systemctl restart ipfs    - Restart IPFS"
print_status "  sudo journalctl -u ipfs -f     - View logs"

# Try to start IPFS service again if it's not running
if ! systemctl is-active --quiet ipfs; then
    print_status "Attempting to restart IPFS service..."
    systemctl restart ipfs
    sleep 5
fi

# Run initial status check
print_status "Running initial status check..."
sleep 5
if [ -f "$SCRIPT_DIR/venv/bin/python3" ]; then
    "$SCRIPT_DIR/venv/bin/python3" "$SCRIPT_DIR/ipfs_status.py"
else
    python3 "$SCRIPT_DIR/ipfs_status.py"
fi

if systemctl is-active --quiet ipfs; then
    print_status "🎉 Setup complete! Your IPFS node is ready to use."
    print_status ""
    print_status "💡 Next Steps:"
    print_status "  1. Test: ipfs-tools status"
    if [ -f "$SCRIPT_DIR/ssd_health_monitor.py" ]; then
        print_status "  2. Check SSD: ipfs-tools ssd-health"
    fi
    if [ -f "$SCRIPT_DIR/nft_downloader.py" ] && ! grep -q "Basic NFT processor" "$SCRIPT_DIR/nft_downloader.py"; then
        print_status "  3. Download NFT: ipfs-tools download 0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb 1"
    fi
    print_status ""
    print_status "🌐 Access your IPFS node:"
    print_status "  Web UI: http://$(hostname -I | awk '{print $1}'):5001/webui/"
    print_status "  Gateway: http://$(hostname -I | awk '{print $1}'):8080/ipfs/"
    
    # Show missing scripts and how to add them
    if [ -f "$SCRIPT_DIR/nft_downloader.py" ] && grep -q "Basic NFT processor" "$SCRIPT_DIR/nft_downloader.py"; then
        print_status ""
        print_warning "📝 To get full NFT functionality:"
        print_status "  sudo cp ~/nft_setup/nft_downloader.py /opt/ipfs-tools/"
        print_status "  sudo chmod +x /opt/ipfs-tools/nft_downloader.py"
        print_status "  sudo chown ipfs:ipfs /opt/ipfs-tools/nft_downloader.py"
    fi
    
    missing_scripts=()
    [ ! -f "$SCRIPT_DIR/ipfs_health_monitor.py" ] && missing_scripts+=("ipfs_health_monitor.py")
    [ ! -f "$SCRIPT_DIR/ssd_optimization.sh" ] && missing_scripts+=("ssd_optimization.sh")
    [ ! -f "$SCRIPT_DIR/ipfs_backup_restore.sh" ] && missing_scripts+=("ipfs_backup_restore.sh")
    
    if [ ${#missing_scripts[@]} -gt 0 ]; then
        print_status ""
        print_warning "📝 To install additional scripts (if available):"
        for script in "${missing_scripts[@]}"; do
            print_status "  sudo cp ~/nft_setup/$script /opt/ipfs-tools/ && sudo chmod +x /opt/ipfs-tools/$script"
        done
    fi
    
else
    print_warning "Setup completed but IPFS service is not running"
    print_status "Check logs with: sudo journalctl -u ipfs -f"
    print_status "Try restarting: sudo systemctl restart ipfs"
fi