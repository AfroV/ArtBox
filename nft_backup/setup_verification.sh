test_nft_functionality() {
    print_header "🎨 Testing NFT Functionality"
    
    if [ -f "/opt/ipfs-tools/nft_downloader.py" ] && [ -f "/opt/ipfs-tools/venv/bin/activate" ]; then
        source /opt/ipfs-tools/venv/bin/activate
        
        # Test import
        python3 -c "
import sys
sys.path.insert(0, '/opt/ipfs-tools')
try:
    from nft_downloader import NFTDownloader
    print('✅ NFT downloader can be imported')
except ImportError as e:
    print(f'❌ Import error: {e}')
except Exception as e:
    print(f'⚠️ Other error: {e}')
"
    else
        print_warning "NFT downloader not available for testing"
    fi
}

check_ssd_optimization() {
    print_header "🚀 Checking SSD Optimization"
    
    # Check mount options
    mount_line=$(mount | grep "/mnt/ssd")
    if [[ "$mount_line" == *"noatime"* ]]; then
        print_status "noatime mount option enabled"
    else
        print_warning "noatime mount option not enabled"
    fi
    
    if [[ "$mount_line" == *"discard"* ]]; then
        print_status "discard (TRIM) mount option enabled"
    else
        print_warning "discard (TRIM) mount option not enabled"
    fi
    
    # Check I/O scheduler
    ssd_device=$(df /mnt/ssd | tail -1 | awk '{print $1}' | sed 's/[0-9]*$//')
    if [ -f "/sys/block/$(basename $ssd_device)/queue/scheduler" ]; then
        scheduler=$(cat "/sys/block/$(basename $ssd_device)/queue/scheduler" | grep -o '\[.*\]' | tr -d '[]' 2>/dev/null || echo "unknown")
        if [[ "$scheduler" == "none" ]] || [[ "$scheduler" == "noop" ]]; then
            print_status "Optimal I/O scheduler: $scheduler"
        else
            print_warning "I/O scheduler not optimized: $scheduler"
        fi
    else
        print_warning "Cannot check I/O scheduler"
    fi
    
    # Check TRIM timer
    if systemctl is-enabled fstrim.timer &>/dev/null; then
        print_status "TRIM timer enabled"
    else
        print_warning "TRIM timer not enabled"
    fi
    
    # Check SSD optimization script
    if [ -f "/opt/ipfs-tools/ssd_optimization.sh" ]; then
        print_status "SSD optimization script available"
    else
        print_warning "SSD optimization script not found"
    fi
}#!/bin/bash

# IPFS Setup Verification and Fix Script
# Checks installation and fixes common issues

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

check_and_fix_permissions() {
    print_header "🔐 Checking and Fixing Permissions"
    
    # Fix script permissions
    if [ -d "/opt/ipfs-tools" ]; then
        find /opt/ipfs-tools -name "*.py" -exec chmod +x {} \;
        find /opt/ipfs-tools -name "*.sh" -exec chmod +x {} \;
        chown -R ipfs:ipfs /opt/ipfs-tools 2>/dev/null || true
        print_status "Script permissions fixed"
    fi
    
    # Fix data directory permissions
    if [ -d "/mnt/ssd/ipfs" ]; then
        chown -R ipfs:ipfs /mnt/ssd/ipfs
        print_status "IPFS data permissions fixed"
    fi
    
    if [ -d "/mnt/ssd/nft_data" ]; then
        chown -R ipfs:ipfs /mnt/ssd/nft_data
        print_status "NFT data permissions fixed"
    fi
    
    if [ -d "/mnt/ssd/backups" ]; then
        chown -R ipfs:ipfs /mnt/ssd/backups 2>/dev/null || true
        print_status "Backup directory permissions fixed"
    fi
}

check_python_dependencies() {
    print_header "🐍 Checking Python Dependencies"
    
    if [ -f "/opt/ipfs-tools/venv/bin/activate" ]; then
        source /opt/ipfs-tools/venv/bin/activate
        
        # Check for required packages
        python3 -c "import requests; print('✅ requests installed')" 2>/dev/null || {
            print_warning "Installing requests..."
            pip install requests
        }
        
        python3 -c "import psutil; print('✅ psutil installed')" 2>/dev/null || {
            print_warning "Installing psutil..."
            pip install psutil
        }
        
        print_status "Python dependencies verified"
    else
        print_error "Python virtual environment not found"
        return 1
    fi
}

check_ipfs_installation() {
    print_header "📦 Checking IPFS Installation"
    
    if command -v ipfs &> /dev/null; then
        print_status "IPFS binary found: $(which ipfs)"
        print_status "IPFS version: $(ipfs version --number)"
    else
        print_error "IPFS binary not found"
        return 1
    fi
    
    if id "ipfs" &>/dev/null; then
        print_status "IPFS user exists"
    else
        print_error "IPFS user not found"
        return 1
    fi
    
    if [ -f "/etc/systemd/system/ipfs.service" ]; then
        print_status "IPFS systemd service exists"
    else
        print_error "IPFS systemd service not found"
        return 1
    fi
}

check_ipfs_config() {
    print_header "⚙️ Checking IPFS Configuration"
    
    if [ -f "/mnt/ssd/ipfs/config" ]; then
        print_status "IPFS config file exists"
        
        # Check API configuration
        api_addr=$(sudo -u ipfs IPFS_PATH=/mnt/ssd/ipfs ipfs config Addresses.API 2>/dev/null || echo "error")
        if [[ "$api_addr" == *"0.0.0.0"* ]]; then
            print_status "API configured for external access"
        else
            print_warning "API may not be configured for external access"
            print_status "Current API address: $api_addr"
        fi
    else
        print_error "IPFS config file not found"
        return 1
    fi
}

check_service_status() {
    print_header "🔧 Checking Service Status"
    
    if systemctl is-enabled ipfs &>/dev/null; then
        print_status "IPFS service is enabled (auto-start)"
    else
        print_warning "IPFS service not enabled for auto-start"
        print_status "Enabling service..."
        systemctl enable ipfs
    fi
    
    if systemctl is-active ipfs &>/dev/null; then
        print_status "IPFS service is running"
    else
        print_warning "IPFS service not running"
        print_status "Starting service..."
        systemctl start ipfs
        sleep 5
    fi
    
    # Test API access
    if curl -s http://127.0.0.1:5001/api/v0/version &>/dev/null; then
        print_status "IPFS API is accessible"
    else
        print_error "IPFS API not accessible"
        return 1
    fi
}

check_directory_structure() {
    print_header "📁 Checking Directory Structure"
    
    required_dirs=(
        "/mnt/ssd"
        "/mnt/ssd/ipfs"
        "/mnt/ssd/nft_data"
        "/mnt/ssd/backups"
        "/opt/ipfs-tools"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_status "Directory exists: $dir"
        else
            print_warning "Creating directory: $dir"
            mkdir -p "$dir"
            if [[ "$dir" == "/mnt/ssd"* ]]; then
                chown ipfs:ipfs "$dir" 2>/dev/null || true
            fi
        fi
    done
}

check_management_tools() {
    print_header "🛠️ Checking Management Tools"
    
    required_scripts=(
        "/opt/ipfs-tools/nft_downloader.py"
        "/opt/ipfs-tools/ipfs_status.py"
        "/opt/ipfs-tools/process_nft_csv.py"
        "/opt/ipfs-tools/cleanup_nft.py"
    )
    
    for script in "${required_scripts[@]}"; do
        if [ -f "$script" ]; then
            print_status "Script exists: $(basename $script)"
        else
            print_warning "Script missing: $(basename $script)"
        fi
    done
    
    if [ -f "/usr/local/bin/ipfs-tools" ]; then
        print_status "Management wrapper installed"
    else
        print_warning "Management wrapper missing"
    fi
}

check_ssd_optimization() {
    print_header "🚀 Checking SSD Optimization"
    
    # Check mount options
    mount_line=$(mount | grep "/mnt/ssd")
    if [[ "$mount_line" == *"noatime"* ]]; then
        print_status "noatime mount option enabled"
    else
        print_warning "noatime mount option not enabled"
    fi
    
    if [[ "$mount_line" == *"discard"* ]]; then
        print_status "discard (TRIM) mount option enabled"
    else
        print_warning "discard (TRIM) mount option not enabled"
    fi
    
    # Check I/O scheduler
    ssd_device=$(df /mnt/ssd | tail -1 | awk '{print $1}' | sed 's/[0-9]*$//')
    if [ -f "/sys/block/$(basename $ssd_device)/queue/scheduler" ]; then
        scheduler=$(cat "/sys/block/$(basename $ssd_device)/queue/scheduler" | grep -o '\[.*\]' | tr -d '[]')
        if [[ "$scheduler" == "none" ]] || [[ "$scheduler" == "noop" ]]; then
            print_status "Optimal I/O scheduler: $scheduler"
        else
            print_warning "I/O scheduler not optimized: $scheduler"
        fi
    fi
    
    # Check TRIM timer
    if systemctl is-enabled fstrim.timer &>/dev/null; then
        print_status "TRIM timer enabled"
    else
        print_warning "TRIM timer not enabled"
    fi
    
    # Check SSD optimization script
    if [ -f "/opt/ipfs-tools/ssd_optimization.sh" ]; then
        print_status "SSD optimization script available"
    else
        print_warning "SSD optimization script not found"
    fi
}

create_test_csv() {
    print_header "📄 Creating Test CSV File"
    
    test_csv="/tmp/test_nfts.csv"
    cat > "$test_csv" << 'EOF'
contract_address,token_id
0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb,1
0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d,1
EOF
    
    print_status "Test CSV created: $test_csv"
    print_status "You can test with: ipfs-tools csv $test_csv"
}

fix_common_issues() {
    print_header "🔧 Fixing Common Issues"
    
    # Restart IPFS service if it's not responding
    if ! curl -s http://127.0.0.1:5001/api/v0/version &>/dev/null; then
        print_warning "IPFS API not responding, restarting service..."
        systemctl restart ipfs
        sleep 10
    fi
    
    # Fix file descriptor limits
    if ! grep -q "ipfs.*nofile" /etc/security/limits.conf; then
        print_status "Adding file descriptor limits for IPFS user..."
        echo "ipfs soft nofile 65536" >> /etc/security/limits.conf
        echo "ipfs hard nofile 65536" >> /etc/security/limits.conf
    fi
    
    # Ensure IPFS PATH is set in service
    if ! grep -q "IPFS_PATH" /etc/systemd/system/ipfs.service; then
        print_warning "IPFS_PATH may not be set in service file"
    fi
}

show_summary() {
    print_header "📋 Setup Summary"
    
    echo "IPFS Node Status:"
    if systemctl is-active ipfs &>/dev/null; then
        echo "  ✅ Service: Running"
    else
        echo "  ❌ Service: Not running"
    fi
    
    if curl -s http://127.0.0.1:5001/api/v0/version &>/dev/null; then
        echo "  ✅ API: Accessible"
    else
        echo "  ❌ API: Not accessible"
    fi
    
    echo
    echo "Web Interfaces:"
    echo "  🌐 IPFS WebUI: http://$(hostname -I | awk '{print $1}'):5001/webui/"
    echo "  🌐 IPFS Gateway: http://$(hostname -I | awk '{print $1}'):8080/ipfs/"
    
    echo
    echo "Management Commands:"
    echo "  ipfs-tools status           - Check node status"
    echo "  ipfs-tools download <contract> <token_id> - Download NFT"
    echo "  ipfs-tools csv <file.csv>   - Process CSV file"
    echo "  ipfs-tools cleanup --list   - List stored NFTs"
    
    echo
    echo "Service Management:"
    echo "  sudo systemctl start ipfs   - Start IPFS"
    echo "  sudo systemctl stop ipfs    - Stop IPFS"
    echo "  sudo systemctl status ipfs  - Check status"
    echo "  sudo journalctl -u ipfs -f  - View logs"
}

# Main execution
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

print_header "🔍 IPFS Setup Verification and Fix"
echo "This script will check your IPFS installation and fix common issues."
echo

check_directory_structure
check_ipfs_installation
check_ipfs_config
check_service_status
check_and_fix_permissions
check_python_dependencies
check_management_tools
test_nft_functionality
check_ssd_optimization
fix_common_issues
create_test_csv

echo
show_summary

print_status "✅ Verification and fixes completed!"
print_status "Your IPFS node should now be ready to use."