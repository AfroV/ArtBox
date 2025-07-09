# Create command wrapper scripts
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
        python3 /opt/ipfs-tools/nft_downloader.py "$@"
        ;;
    "csv")
        shift
        python3 /opt/ipfs-tools/process_nft_csv.py "$@"
        ;;
    "cleanup")
        shift
        python3 /opt/ipfs-tools/cleanup_nft.py "$@"
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
        echo "SSD optimization requires root privileges"
        echo "Run: sudo /opt/ipfs-tools/ssd_optimization.sh"
        ;;
    *)
        echo "IPFS Tools for Raspberry Pi"
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
        echo "  backup restore-*        Restore from backup"
        echo ""
        echo "SSD Optimization:"
        echo "  ssd-health              Check SSD health and status"
        echo "  ssd-optimize            Run SSD optimization (requires sudo)"
        echo ""
        echo "Examples:"
        echo "  ipfs-tools status"
        echo "  ipfs-tools ssd-health"
        echo "  ipfs-tools monitor 60"
        echo "  ipfs-tools download 0x1234... 1"
        echo "  ipfs-tools csv nfts.csv"
        echo "  sudo ipfs-tools ssd-optimize"
        ;;
esac
EOF#!/bin/bash

# IPFS Setup Script for Raspberry Pi
# This script installs and configures IPFS (Kubo) on Raspberry Pi OS

set -e

# Configuration
IPFS_VERSION="v0.29.0"
IPFS_USER="ipfs"
IPFS_HOME="/opt/ipfs"
IPFS_DATA_DIR="/mnt/ssd/ipfs"
NFT_DATA_DIR="/mnt/ssd/nft_data"
SCRIPT_DIR="/opt/ipfs-tools"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

# Check if SSD is mounted
if ! mountpoint -q /mnt/ssd; then
    print_error "SSD not mounted at /mnt/ssd"
    print_status "Please mount your SSD first:"
    print_status "1. Create mount point: sudo mkdir -p /mnt/ssd"
    print_status "2. Find your SSD: lsblk"
    print_status "3. Mount: sudo mount /dev/sdX1 /mnt/ssd"
    print_status "4. Add to fstab for permanent mounting"
    exit 1
fi

print_status "Starting IPFS installation..."

# Update system
print_status "Updating system packages..."
apt update && apt upgrade -y

# Install dependencies
print_status "Installing dependencies..."
apt install -y curl wget python3 python3-pip python3-venv git smartmontools

# Create ipfs user
print_status "Creating IPFS user..."
if ! id "$IPFS_USER" &>/dev/null; then
    useradd -r -m -d "$IPFS_HOME" -s /bin/bash "$IPFS_USER"
fi

# Create directories
print_status "Creating directories..."
mkdir -p "$IPFS_HOME" "$IPFS_DATA_DIR" "$NFT_DATA_DIR" "$SCRIPT_DIR"
chown -R "$IPFS_USER:$IPFS_USER" "$IPFS_HOME" "$IPFS_DATA_DIR" "$NFT_DATA_DIR"

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
systemctl start ipfs

# Wait for IPFS to start
print_status "Waiting for IPFS to start..."
sleep 10

# Install Python dependencies for NFT downloader
print_status "Setting up Python environment..."
python3 -m venv "$SCRIPT_DIR/venv"
source "$SCRIPT_DIR/venv/bin/activate"
pip install requests psutil

# Copy NFT downloader script
print_status "Installing NFT management tools..."
if [ -f "nft_downloader.py" ]; then
    cp "nft_downloader.py" "$SCRIPT_DIR/"
else
    print_warning "nft_downloader.py not found in current directory"
    print_status "Please copy your NFT downloader script to $SCRIPT_DIR/nft_downloader.py"
fi

# Copy health monitor if available
if [ -f "ipfs_health_monitor.py" ]; then
    cp "ipfs_health_monitor.py" "$SCRIPT_DIR/"
    print_status "Health monitor installed"
fi

# Copy backup script if available  
if [ -f "ipfs_backup_restore.sh" ]; then
    cp "ipfs_backup_restore.sh" "$SCRIPT_DIR/"
    chmod +x "$SCRIPT_DIR/ipfs_backup_restore.sh"
    ln -sf "$SCRIPT_DIR/ipfs_backup_restore.sh" /usr/local/bin/ipfs-backup
    print_status "Backup tools installed"
fi

# Copy SSD optimization script if available
if [ -f "ssd_optimization.sh" ]; then
    cp "ssd_optimization.sh" "$SCRIPT_DIR/"
    chmod +x "$SCRIPT_DIR/ssd_optimization.sh"
    print_status "SSD optimization tools installed"
fi

# Create management scripts
print_status "Creating management scripts..."

# IPFS status script
cat > "$SCRIPT_DIR/ipfs_status.py" << 'EOF'
#!/usr/bin/env python3
import subprocess
import sys
import requests
import json

def check_ipfs_daemon():
    try:
        response = requests.get('http://127.0.0.1:5001/api/v0/version', timeout=5)
        if response.status_code == 200:
            version_info = response.json()
            print(f"✅ IPFS daemon is running")
            print(f"Version: {version_info['Version']}")
            return True
    except:
        pass
    
    print("❌ IPFS daemon is not running")
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
        response = requests.get('http://127.0.0.1:5001/api/v0/stats/repo', timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"📊 Repository stats:")
            print(f"  Storage: {stats.get('RepoSize', 0) / 1024 / 1024:.2f} MB")
            print(f"  Objects: {stats.get('NumObjects', 0)}")
        
        response = requests.get('http://127.0.0.1:5001/api/v0/swarm/peers', timeout=5)
        if response.status_code == 200:
            peers = response.json()
            print(f"  Connected peers: {len(peers.get('Peers', []))}")
    except:
        print("❌ Could not get IPFS stats")

if __name__ == "__main__":
    print("🔍 IPFS Status Check")
    print("=" * 30)
    
    daemon_ok = check_ipfs_daemon()
    service_ok = check_ipfs_service()
    
    if daemon_ok:
        get_ipfs_stats()
        print("\n🌐 Web UI: http://127.0.0.1:5001/webui/")
    
    if not daemon_ok or not service_ok:
        print("\n🔧 Troubleshooting:")
        print("  Start service: sudo systemctl start ipfs")
        print("  Check logs: sudo journalctl -u ipfs -f")
        sys.exit(1)
EOF

# CSV NFT processor
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
    from nft_downloader import NFTDownloader
except ImportError:
    print("❌ nft_downloader.py not found. Please ensure it's in /opt/ipfs-tools/")
    sys.exit(1)

def process_csv_file(csv_file, output_dir="/mnt/ssd/nft_data"):
    """Process NFTs from CSV file"""
    print(f"📁 Processing CSV file: {csv_file}")
    print(f"📂 Output directory: {output_dir}")
    
    downloader = NFTDownloader()
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

# NFT cleanup script
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

def remove_from_mfs(mfs_path, ipfs_api_url="http://127.0.0.1:5001"):
    """Remove file from MFS"""
    try:
        response = requests.post(
            f"{ipfs_api_url}/api/v0/files/rm",
            params={'arg': mfs_path}
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Error removing from MFS {mfs_path}: {e}")
        return False

def cleanup_nft(contract_address, token_id, data_dir="/mnt/ssd/nft_data"):
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
            
            # Remove from MFS
            collection_name = contract_address[-8:]
            mfs_base_path = f"/nft_collections/{collection_name}"
            
            metadata_mfs_path = f"{mfs_base_path}/token_{token_id}_metadata.json"
            print(f"📁 Removing from MFS: {metadata_mfs_path}")
            remove_from_mfs(metadata_mfs_path)
            
            # Try to determine image extension and remove
            for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
                image_mfs_path = f"{mfs_base_path}/token_{token_id}_image{ext}"
                if remove_from_mfs(image_mfs_path):
                    print(f"📁 Removed from MFS: {image_mfs_path}")
                    break
            
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

def list_nfts(data_dir="/mnt/ssd/nft_data"):
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
    parser.add_argument('--data-dir', default='/mnt/ssd/nft_data', 
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

# Make scripts executable
chmod +x "$SCRIPT_DIR"/*.py
find "$SCRIPT_DIR" -name "*.sh" -exec chmod +x {} \;

# Create convenience aliases
mkdir -p /etc/bash.bashrc.d/
cat > /etc/bash.bashrc.d/ipfs-tools << 'EOF'
# IPFS Tools aliases
alias ipfs-status='python3 /opt/ipfs-tools/ipfs_status.py'
alias ipfs-nft='python3 /opt/ipfs-tools/nft_downloader.py'
alias ipfs-csv='python3 /opt/ipfs-tools/process_nft_csv.py'
alias ipfs-cleanup='python3 /opt/ipfs-tools/cleanup_nft.py'
EOF

# Create command wrapper scripts
cat > /usr/local/bin/ipfs-tools << 'EOF'
#!/bin/bash
source /opt/ipfs-tools/venv/bin/activate
case "$1" in
    "status")
        python3 /opt/ipfs-tools/ipfs_status.py
        ;;
    "download")
        shift
        python3 /opt/ipfs-tools/nft_downloader.py "$@"
        ;;
    "csv")
        shift
        python3 /opt/ipfs-tools/process_nft_csv.py "$@"
        ;;
    "cleanup")
        shift
        python3 /opt/ipfs-tools/cleanup_nft.py "$@"
        ;;
    *)
        echo "IPFS Tools for Raspberry Pi"
        echo "Usage: ipfs-tools [command] [options]"
        echo ""
        echo "Commands:"
        echo "  status              Check IPFS daemon status"
        echo "  download <contract> <token_id>  Download single NFT"
        echo "  csv <file.csv>      Process NFTs from CSV file"
        echo "  cleanup --list      List all stored NFTs"
        echo "  cleanup --cleanup <contract> <token_id>  Remove NFT"
        echo ""
        echo "Examples:"
        echo "  ipfs-tools status"
        echo "  ipfs-tools download 0x1234... 1"
        echo "  ipfs-tools csv nfts.csv"
        echo "  ipfs-tools cleanup --list"
        ;;
esac
EOF

chmod +x /usr/local/bin/ipfs-tools

# Set ownership
chown -R "$IPFS_USER:$IPFS_USER" "$SCRIPT_DIR"

print_status "Installation completed successfully!"
print_status ""
print_status "📁 Data directories:"
print_status "  IPFS data: $IPFS_DATA_DIR"
print_status "  NFT data: $NFT_DATA_DIR"
print_status "  Scripts: $SCRIPT_DIR"
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

# Run initial status check
print_status "Running initial status check..."
sleep 5
python3 "$SCRIPT_DIR/ipfs_status.py"

print_status "🎉 Setup complete! Your IPFS node is ready to use."