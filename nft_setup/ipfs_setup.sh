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

# ——————————————————————————————————————————————————————————————
# Install the new, complete, never-stuck CSV backup processor
# ——————————————————————————————————————————————————————————————

print_status "Installing enhanced CSV backup processor (process_nft_csv.py)..."

cat > "$SCRIPT_DIR/process_nft_csv.py" << 'EOF'
#!/usr/bin/env python3
"""
XCOPY FINAL – short, complete, never stuck, with --workers support
"""

import csv
import json
import re
import time
from pathlib import Path
import requests
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed

class XCOPYDownloader:
    def __init__(self, output_dir="ipfs_backup"):
        self.files_dir = Path(output_dir) / "files"
        self.files_dir.mkdir(parents=True, exist_ok=True)
        self.downloaded = set()
        self.lock = Lock()
        self.progress_file = Path(output_dir) / "download_progress.json"
        self.session = requests.Session()
        # Match valid IPFS CIDs: CIDv0 (Qm...) or CIDv1 (baf..., bae..., etc)
        self.cid_pattern = re.compile(r'(?:https?://[^/\s]*ipfs[^/\s]*/(?:ipfs/)?|ipfs://)?(?:(Qm[a-zA-Z0-9]{44})|(baf[a-z0-9]{50,}))', re.I)
        self._load_progress()

    def _load_progress(self):
        if self.progress_file.exists():
            try:
                self.downloaded = set(json.load(open(self.progress_file)).get("downloaded", []))
                print(f"Progress loaded – {len(self.downloaded)} files already done")
            except: pass

    def _save_progress(self):
        json.dump({"downloaded": list(self.downloaded)}, open(self.progress_file, "w"), indent=2)

    def _download(self, cid):
        url = f"http://127.0.0.1:8080/ipfs/{cid}"
        print(f"  → {cid[:20]}...", end="", flush=True)
        for _ in range(40):                                    # ~13 minutes max
            try:
                r = self.session.get(url, timeout=30)
                if r.status_code == 200 and len(r.content) > 1000:
                    print(f" SUCCESS ({len(r.content)/1048576:.2f} MB)")
                    return r.content
            except:
                pass
            print(".", end="", flush=True)
            time.sleep(20)
        print(" timeout – open this CID in IPFS Desktop to speed it up")
        return None

    def _exists(self, cid):
        return any((self.files_dir / f"{cid}{e}").exists() for e in [".json",".gif",".png",".jpg",".mp4",".glb",".html",".bin",".webp"])

    def _extract_all_cids(self, obj, parent_cid):
        cids = []
        if isinstance(obj, str):
            for match in self.cid_pattern.finditer(obj):
                cid = match.group(1) or match.group(2)
                if cid and cid != parent_cid:
                    cids.append(cid)
        elif isinstance(obj, dict):
            for value in obj.values():
                cids.extend(self._extract_all_cids(value, parent_cid))
        elif isinstance(obj, list):
            for item in obj:
                cids.extend(self._extract_all_cids(item, parent_cid))
        return cids

    def download_cid(self, cid, name=""):
        cid = cid.strip()
        already_exists = self._exists(cid)

        if already_exists:
            for ext in [".json",".gif",".png",".jpg",".mp4",".glb",".html",".bin",".webp"]:
                file_path = self.files_dir / f"{cid}{ext}"
                if file_path.exists() and ext in [".json", ".html"]:
                    try:
                        data = file_path.read_bytes()
                        text = data.decode("utf-8", errors="ignore")
                        if ext == ".json":
                            meta = json.loads(text)
                            nested = self._extract_all_cids(meta, cid)
                        else:
                            nested = [m.group(1) or m.group(2) for m in self.cid_pattern.finditer(text) if (m.group(1) or m.group(2)) != cid]
                        if nested:
                            print(f"  ✓ Existing {ext[1:].upper()} contains {len(nested)} nested hashes")
                            for n in nested:
                                if not self._exists(n):
                                    print(f"      → Downloading nested: {n[:20]}...")
                                    self.download_cid(n)
                    except: pass
            return True

        data = self._download(cid)
        if not data:
            return False

        # Detect file type
        ext = ".bin"
        if data.startswith(b'<!DOCTYPE html'): ext = ".html"
        elif data.startswith(b'\x89PNG'): ext = ".png"
        elif data.startswith(b'\xff\xd8\xff'): ext = ".jpg"
        elif data.startswith(b'GIF8'): ext = ".gif"
        elif len(data) >= 12 and data[:4] == b'RIFF' and data[8:12] == b'WEBP': ext = ".webp"
        elif len(data) >= 8 and data[4:8] in [b'ftyp', b'mdat', b'moov', b'wide']: ext = ".mp4"
        elif data.startswith(b'glTF'): ext = ".glb"
        else:
            try: json.loads(data); ext = ".json"
            except: pass

        (self.files_dir / f"{cid}{ext}").write_bytes(data)
        with self.lock:
            self.downloaded.add(cid)
            self._save_progress()

        # Recursively handle nested hashes in JSON/HTML
        if ext in [".json", ".html"]:
            try:
                text = data.decode("utf-8", errors="ignore")
                if ext == ".json":
                    meta = json.loads(text)
                    nested = self._extract_all_cids(meta, cid)
                else:
                    nested = [m.group(1) or m.group(2) for m in self.cid_pattern.finditer(text) if (m.group(1) or m.group(2)) != cid]
                if nested:
                    print(f"    → Found {len(nested)} nested hashes")
                    for n in nested:
                        if not self._exists(n):
                            print(f"      → Downloading: {n[:20]}...")
                            self.download_cid(n)
            except: pass
        return True

    def run(self, csv_file, workers=1):
        items = []
        with open(csv_file, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cid = (row.get("cid") or row.get("CID") or "").strip()
                if not cid:
                    url = (row.get("metadata_url") or row.get("metadataUrl") or "").strip()
                    m = self.cid_pattern.search(url)
                    if m:
                        cid = m.group(1) or m.group(2)
                if cid and cid not in ["See CSV","On-Chain","Arweave","--"]:
                    title = row.get("title") or row.get("name") or row.get("filename") or ""
                    items.append((title, cid))

        print(f"\nStarting download of {len(items)} items (workers = {workers})\n")

        def task(item):
            title, cid = item
            self.download_cid(cid, title)

        if workers == 1:
            for item in items:
                task(item)
        else:
            with ThreadPoolExecutor(max_workers=workers) as exe:
                for future in as_completed([exe.submit(task, i) for i in items]):
                    future.result()

        print("\nALL DONE – your archive is complete!")
        print(f"   Total unique files: {len(self.downloaded)}")
        print(f"   Folder: {self.files_dir.resolve()}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ultimate CSV → IPFS backup tool")
    parser.add_argument("csv", help="CSV file")
    parser.add_argument("--output", "-o", default="ipfs_backup", help="Output folder")
    parser.add_argument("--workers", type=int, default=1, help="Parallel workers (1 = safest)")
    args = parser.parse_args()
    XCOPYDownloader(args.output).run(args.csv, workers=args.workers)
EOF

chmod +x "$SCRIPT_DIR/process_nft_csv.py"
chown ipfs:ipfs "$SCRIPT_DIR/process_nft_csv.py"
print_success "Enhanced CSV backup processor installed (supports --workers, resumable, nested hashes)"



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
"""
Enhanced CSV NFT Processor with Progress Bar and Status Tracking
Processes NFTs from CSV file with visual progress indication
"""

import csv
import sys
import os
import json
import time
from pathlib import Path

# Add the script directory to path to import nft_downloader
sys.path.insert(0, '/opt/ipfs-tools')

try:
    from nft_downloader import EnhancedNFTDownloader
except ImportError:
    print("❌ Enhanced nft_downloader.py not found. Please ensure it's in /opt/ipfs-tools/")
    sys.exit(1)

class ProgressBar:
    """Simple progress bar for console output"""
    
    def __init__(self, total, width=50):
        self.total = total
        self.width = width
        self.current = 0
        self.start_time = time.time()
        
    def update(self, current, status="Processing"):
        self.current = current
        
        # Calculate progress
        percent = (current / self.total) * 100 if self.total > 0 else 0
        filled = int(self.width * current // self.total) if self.total > 0 else 0
        bar = '█' * filled + '░' * (self.width - filled)
        
        # Calculate time estimates
        elapsed = time.time() - self.start_time
        if current > 0:
            rate = current / elapsed
            eta = (self.total - current) / rate if rate > 0 else 0
            eta_str = f"{int(eta//60):02d}:{int(eta%60):02d}"
        else:
            eta_str = "--:--"
        
        # Format the progress line
        progress_line = f"\r📊 [{bar}] {current}/{self.total} ({percent:.1f}%) | ETA: {eta_str} | {status}"
        
        # Print with proper padding to clear previous line
        print(progress_line.ljust(120), end='', flush=True)
        
        if current >= self.total:
            print()  # New line when complete

def count_csv_rows(csv_file):
    """Count the number of data rows in CSV file (excluding header)"""
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            return sum(1 for row in reader)
    except Exception as e:
        print(f"❌ Error counting CSV rows: {e}")
        return 0

def validate_csv_format(csv_file):
    """Validate CSV file format and return column info"""
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            # Check for required columns
            required_cols = ['contract_address', 'token_id']
            missing_cols = [col for col in required_cols if col not in fieldnames]
            
            if missing_cols:
                print(f"❌ Missing required columns: {missing_cols}")
                print(f"📋 Available columns: {fieldnames}")
                return False, fieldnames
            
            return True, fieldnames
    except Exception as e:
        print(f"❌ Error validating CSV: {e}")
        return False, []

def format_time(seconds):
    """Format seconds into readable time string"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{int(seconds//60)}m {int(seconds%60)}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def process_csv_file(csv_file, output_dir="/opt/ipfs-data/nft_data"):
    """Process NFTs from CSV file with progress tracking"""
    
    print(f"🚀 Enhanced CSV NFT Processor Starting")
    print("=" * 60)
    print(f"📁 Input file: {csv_file}")
    print(f"📂 Output directory: {output_dir}")
    
    # Validate CSV format
    print("🔍 Validating CSV format...")
    is_valid, fieldnames = validate_csv_format(csv_file)
    if not is_valid:
        return False
    
    print(f"✅ CSV validation passed")
    print(f"📋 Columns found: {', '.join(fieldnames)}")
    
    # Count total rows
    print("📊 Counting NFTs to process...")
    total_rows = count_csv_rows(csv_file)
    if total_rows == 0:
        print("❌ No NFTs found in CSV file")
        return False
    
    print(f"📈 Total NFTs to process: {total_rows}")
    print()
    
    # Initialize downloader and progress tracking
    downloader = EnhancedNFTDownloader()
    processed = 0
    failed = 0
    skipped = 0
    start_time = time.time()
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Initialize progress bar
    progress = ProgressBar(total_rows)
    
    # Process CSV file
    current_row = 0
    failed_nfts = []
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            current_row += 1
            
            contract_address = row.get('contract_address', '').strip()
            token_id = row.get('token_id', '').strip()
            
            # Update progress bar with current NFT info
            status = f"Processing {contract_address[:8]}...#{token_id}"
            progress.update(current_row, status)
            
            # Validate row data
            if not contract_address or not token_id:
                skipped += 1
                failed_nfts.append({
                    'contract_address': contract_address,
                    'token_id': token_id,
                    'error': 'Missing contract address or token ID'
                })
                continue
            
            # Validate contract address format
            if not contract_address.startswith('0x') or len(contract_address) != 42:
                skipped += 1
                failed_nfts.append({
                    'contract_address': contract_address,
                    'token_id': token_id,
                    'error': 'Invalid contract address format'
                })
                continue
            
            try:
                # Update progress with current processing status
                status = f"Downloading {contract_address[:8]}...#{token_id}"
                progress.update(current_row, status)
                
                # Process the NFT
                success = downloader.process_nft(contract_address, token_id, output_dir)
                
                if success:
                    processed += 1
                    status = f"✅ Completed {contract_address[:8]}...#{token_id}"
                else:
                    failed += 1
                    failed_nfts.append({
                        'contract_address': contract_address,
                        'token_id': token_id,
                        'error': 'Processing failed'
                    })
                    status = f"❌ Failed {contract_address[:8]}...#{token_id}"
                
                # Brief pause to show status
                progress.update(current_row, status)
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print(f"\n\n⚠️ Process interrupted by user at NFT {current_row}/{total_rows}")
                break
            except Exception as e:
                failed += 1
                failed_nfts.append({
                    'contract_address': contract_address,
                    'token_id': token_id,
                    'error': str(e)
                })
                status = f"❌ Error {contract_address[:8]}...#{token_id}"
                progress.update(current_row, status)
                time.sleep(0.1)
    
    # Final progress update
    progress.update(current_row, "Complete!")
    
    # Calculate final statistics
    total_time = time.time() - start_time
    
    print("\n")
    print("🎉 CSV Processing Complete!")
    print("=" * 60)
    print(f"📊 Final Statistics:")
    print(f"  • Total NFTs in CSV: {total_rows}")
    print(f"  • Successfully processed: {processed}")
    print(f"  • Failed: {failed}")
    print(f"  • Skipped (invalid data): {skipped}")
    print(f"  • Processing time: {format_time(total_time)}")
    
    if processed > 0:
        avg_time = total_time / processed
        print(f"  • Average time per NFT: {format_time(avg_time)}")
    
    success_rate = (processed / total_rows) * 100 if total_rows > 0 else 0
    print(f"  • Success rate: {success_rate:.1f}%")
    print(f"  📁 Files saved to: {output_dir}")
    
    # Show failed NFTs if any
    if failed_nfts:
        print(f"\n⚠️ Failed NFTs ({len(failed_nfts)}):")
        print("-" * 60)
        for i, nft in enumerate(failed_nfts[:10]):  # Show first 10 failures
            print(f"  {i+1}. {nft['contract_address']} #{nft['token_id']}: {nft['error']}")
        
        if len(failed_nfts) > 10:
            print(f"  ... and {len(failed_nfts) - 10} more")
        
        # Save failed NFTs to file for retry
        failed_log = os.path.join(output_dir, 'failed_nfts.json')
        try:
            with open(failed_log, 'w') as f:
                json.dump(failed_nfts, f, indent=2)
            print(f"\n📝 Failed NFTs saved to: {failed_log}")
            print("   You can review and retry these later.")
        except Exception as e:
            print(f"❌ Could not save failed NFTs log: {e}")
    
    print(f"\n💡 Quick commands:")
    print(f"  • Check storage: df -h /opt/ipfs-data")
    print(f"  • View files: ls -la {output_dir}")
    print(f"  • IPFS status: ipfs-tools status")
    
    return processed > 0

def main():
    if len(sys.argv) != 2:
        print("Enhanced CSV NFT Processor")
        print("=" * 40)
        print("Usage: python3 process_nft_csv.py <csv_file>")
        print("")
        print("CSV format requirements:")
        print("  • Must have 'contract_address' column (0x... format)")
        print("  • Must have 'token_id' column (numeric)")
        print("  • First row should be headers")
        print("")
        print("Example CSV:")
        print("  contract_address,token_id,name")
        print("  0x1234...,1,My NFT")
        print("  0x5678...,42,Another NFT")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    # Check if CSV file exists
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        print(f"📍 Current directory: {os.getcwd()}")
        print(f"📋 Available files: {', '.join(os.listdir('.'))}")
        sys.exit(1)
    
    # Check file size
    file_size = os.path.getsize(csv_file)
    print(f"📄 CSV file size: {file_size:,} bytes")
    
    if file_size == 0:
        print("❌ CSV file is empty")
        sys.exit(1)
    
    # Process the file
    try:
        success = process_csv_file(csv_file)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
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
        if [ -z "$2" ]; then
            echo "Usage: ipfs-tools csv <file.csv> [--workers N] [--output folder]"
            echo "Example: ipfs-tools csv xcopy.csv --workers 4 --output xcopy_backup"
            exit 1
        fi
        shift
        python3 /opt/ipfs-tools/process_nft_csv.py "$@"
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