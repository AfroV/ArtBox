#!/bin/bash

# Final Installation Validation Script
# Comprehensive test of all IPFS node components

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

print_header() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED_TESTS++))
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED_TESTS++))
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    ((TOTAL_TESTS++))
    echo -n "Testing $test_name... "
    
    if eval "$test_command" &>/dev/null; then
        print_success "$test_name"
        return 0
    else
        print_error "$test_name"
        return 1
    fi
}

show_banner() {
    echo -e "${PURPLE}"
    echo "  ██╗   ██╗ █████╗ ██╗     ██╗██████╗  █████╗ ████████╗██╗ ██████╗ ███╗   ██╗"
    echo "  ██║   ██║██╔══██╗██║     ██║██╔══██╗██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║"
    echo "  ██║   ██║███████║██║     ██║██║  ██║███████║   ██║   ██║██║   ██║██╔██╗ ██║"
    echo "  ╚██╗ ██╔╝██╔══██║██║     ██║██║  ██║██╔══██║   ██║   ██║██║   ██║██║╚██╗██║"
    echo "   ╚████╔╝ ██║  ██║███████╗██║██████╔╝██║  ██║   ██║   ██║╚██████╔╝██║ ╚████║"
    echo "    ╚═══╝  ╚═╝  ╚═╝╚══════╝╚═╝╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝"
    echo -e "${NC}"
    echo -e "${BLUE}🧪 IPFS Node Installation Validation${NC}"
    echo
}

test_prerequisites() {
    print_header "🔍 Testing Prerequisites"
    
    run_test "SSD Mount" "mountpoint -q /mnt/ssd"
    run_test "IPFS User Exists" "id ipfs"
    run_test "Python3 Available" "command -v python3"
    run_test "Systemctl Available" "command -v systemctl"
    run_test "Smart Tools Available" "command -v smartctl"
    
    echo
}

test_ipfs_installation() {
    print_header "📦 Testing IPFS Installation"
    
    run_test "IPFS Binary" "command -v ipfs"
    run_test "IPFS Config Exists" "[ -f /mnt/ssd/ipfs/config ]"
    run_test "IPFS Service File" "[ -f /etc/systemd/system/ipfs.service ]"
    run_test "IPFS Service Enabled" "systemctl is-enabled ipfs"
    run_test "IPFS Data Directory" "[ -d /mnt/ssd/ipfs ]"
    
    echo
}

test_ipfs_functionality() {
    print_header "🔧 Testing IPFS Functionality"
    
    run_test "IPFS Service Running" "systemctl is-active ipfs"
    run_test "IPFS API Responding" "curl -s http://127.0.0.1:5001/api/v0/version"
    run_test "IPFS Version Check" "sudo -u ipfs IPFS_PATH=/mnt/ssd/ipfs ipfs version"
    run_test "IPFS ID Command" "sudo -u ipfs IPFS_PATH=/mnt/ssd/ipfs ipfs id"
    
    # Test basic IPFS operations
    echo -n "Testing IPFS Add/Pin... "
    if echo "validation test" | sudo -u ipfs IPFS_PATH=/mnt/ssd/ipfs ipfs add -q &>/dev/null; then
        print_success "IPFS Add/Pin"
        ((PASSED_TESTS++))
    else
        print_error "IPFS Add/Pin"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    echo
}

test_management_tools() {
    print_header "🛠️ Testing Management Tools"
    
    run_test "Tools Directory" "[ -d /opt/ipfs-tools ]"
    run_test "Python Virtual Env" "[ -f /opt/ipfs-tools/venv/bin/activate ]"
    run_test "NFT Downloader" "[ -f /opt/ipfs-tools/nft_downloader.py ]"
    run_test "Health Monitor" "[ -f /opt/ipfs-tools/ipfs_health_monitor.py ]"
    run_test "Backup Script" "[ -f /opt/ipfs-tools/ipfs_backup_restore.sh ]"
    run_test "SSD Optimization" "[ -f /opt/ipfs-tools/ssd_optimization.sh ]"
    run_test "Main Command Wrapper" "[ -f /usr/local/bin/ipfs-tools ]"
    
    # Test Python imports
    echo -n "Testing Python Dependencies... "
    if source /opt/ipfs-tools/venv/bin/activate && python3 -c "import requests, psutil" &>/dev/null; then
        print_success "Python Dependencies"
        ((PASSED_TESTS++))
    else
        print_error "Python Dependencies"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    echo
}

test_commands() {
    print_header "⚡ Testing Commands"
    
    run_test "ipfs-tools Command" "[ -x /usr/local/bin/ipfs-tools ]"
    
    # Test command outputs
    echo -n "Testing ipfs-tools status... "
    if timeout 10 ipfs-tools status &>/dev/null; then
        print_success "ipfs-tools status"
        ((PASSED_TESTS++))
    else
        print_error "ipfs-tools status"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    echo -n "Testing ipfs-tools help... "
    if ipfs-tools help &>/dev/null || ipfs-tools &>/dev/null; then
        print_success "ipfs-tools help"
        ((PASSED_TESTS++))
    else
        print_error "ipfs-tools help"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    echo
}

test_directories() {
    print_header "📁 Testing Directory Structure"
    
    required_dirs=(
        "/mnt/ssd"
        "/mnt/ssd/ipfs"
        "/mnt/ssd/nft_data"
        "/mnt/ssd/backups"
        "/opt/ipfs-tools"
    )
    
    for dir in "${required_dirs[@]}"; do
        run_test "Directory: $dir" "[ -d '$dir' ]"
    done
    
    echo
}

test_permissions() {
    print_header "🔐 Testing Permissions"
    
    run_test "IPFS Data Ownership" "[ \$(stat -c '%U' /mnt/ssd/ipfs) = 'ipfs' ]"
    run_test "NFT Data Directory" "[ -w /mnt/ssd/nft_data ]"
    run_test "Backup Directory" "[ -w /mnt/ssd/backups ]"
    run_test "Scripts Executable" "[ -x /opt/ipfs-tools/nft_downloader.py ]"
    
    echo
}

test_ssd_optimization() {
    print_header "🚀 Testing SSD Optimization"
    
    # Check mount options
    echo -n "Testing noatime mount option... "
    if mount | grep "/mnt/ssd" | grep -q "noatime"; then
        print_success "noatime mount option"
        ((PASSED_TESTS++))
    else
        print_error "noatime mount option"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    echo -n "Testing discard mount option... "
    if mount | grep "/mnt/ssd" | grep -q "discard"; then
        print_success "discard mount option"
        ((PASSED_TESTS++))
    else
        print_error "discard mount option"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    # Check TRIM timer
    run_test "TRIM Timer Available" "systemctl list-unit-files | grep -q fstrim.timer"
    
    # Check SSD health monitor
    echo -n "Testing SSD health monitor... "
    if source /opt/ipfs-tools/venv/bin/activate 2>/dev/null && timeout 5 python3 /opt/ipfs-tools/ssd_health_monitor.py &>/dev/null; then
        print_success "SSD health monitor"
        ((PASSED_TESTS++))
    else
        print_error "SSD health monitor"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    echo
}

test_nft_functionality() {
    print_header "🎨 Testing NFT Functionality"
    
    # Test NFT downloader import
    echo -n "Testing NFT downloader import... "
    if source /opt/ipfs-tools/venv/bin/activate && python3 -c "
import sys
sys.path.insert(0, '/opt/ipfs-tools')
from nft_downloader import NFTDownloader
downloader = NFTDownloader()
print('Import successful')
" &>/dev/null; then
        print_success "NFT downloader import"
        ((PASSED_TESTS++))
    else
        print_error "NFT downloader import"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    # Test CSV processor
    run_test "CSV Processor Script" "[ -f /opt/ipfs-tools/process_nft_csv.py ]"
    run_test "Cleanup Script" "[ -f /opt/ipfs-tools/cleanup_nft.py ]"
    
    echo
}

test_backup_functionality() {
    print_header "💾 Testing Backup Functionality"
    
    run_test "Backup Script Exists" "[ -f /opt/ipfs-tools/ipfs_backup_restore.sh ]"
    run_test "Backup Script Executable" "[ -x /opt/ipfs-tools/ipfs_backup_restore.sh ]"
    
    # Test backup directory creation
    echo -n "Testing backup directory creation... "
    if mkdir -p /mnt/ssd/backups/test && rmdir /mnt/ssd/backups/test; then
        print_success "backup directory creation"
        ((PASSED_TESTS++))
    else
        print_error "backup directory creation"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    echo
}

test_network_connectivity() {
    print_header "🌐 Testing Network Connectivity"
    
    run_test "Internet Connectivity" "ping -c 1 8.8.8.8"
    run_test "HTTPS Connectivity" "curl -s https://ipfs.io"
    
    # Test IPFS swarm
    echo -n "Testing IPFS swarm connectivity... "
    peer_count=$(sudo -u ipfs IPFS_PATH=/mnt/ssd/ipfs ipfs swarm peers 2>/dev/null | wc -l)
    if [ "$peer_count" -gt 0 ]; then
        print_success "IPFS swarm connectivity ($peer_count peers)"
        ((PASSED_TESTS++))
    else
        print_error "IPFS swarm connectivity (0 peers)"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    echo
}

create_test_csv() {
    print_header "📄 Creating Test Files"
    
    # Create test CSV
    cat > /tmp/validation_test.csv << 'EOF'
contract_address,token_id
0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb,1
EOF
    
    run_test "Test CSV Creation" "[ -f /tmp/validation_test.csv ]"
    
    echo
}

run_performance_check() {
    print_header "🏃 Performance Check"
    
    # Basic disk performance test
    echo -n "Testing disk write performance... "
    if dd if=/dev/zero of=/mnt/ssd/test_write bs=1M count=10 &>/dev/null && rm -f /mnt/ssd/test_write; then
        print_success "disk write performance"
        ((PASSED_TESTS++))
    else
        print_error "disk write performance"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    # IPFS performance test
    echo -n "Testing IPFS add performance... "
    if echo "performance test data" | sudo -u ipfs IPFS_PATH=/mnt/ssd/ipfs timeout 10 ipfs add -q &>/dev/null; then
        print_success "IPFS add performance"
        ((PASSED_TESTS++))
    else
        print_error "IPFS add performance"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))
    
    echo
}

show_system_info() {
    print_header "💻 System Information"
    
    echo "Hostname: $(hostname)"
    echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '\"')"
    echo "Kernel: $(uname -r)"
    echo "Architecture: $(uname -m)"
    echo "Memory: $(free -h | grep Mem | awk '{print $2}')"
    
    if [ -f "/sys/firmware/devicetree/base/model" ]; then
        echo "Hardware: $(cat /sys/firmware/devicetree/base/model 2>/dev/null | tr -d '\0')"
    fi
    
    # IPFS version
    if command -v ipfs &>/dev/null; then
        echo "IPFS Version: $(ipfs version --number 2>/dev/null || echo 'Unknown')"
    fi
    
    # Disk usage
    echo "SSD Usage: $(df -h /mnt/ssd | tail -1 | awk '{print $3 "/" $2 " (" $5 ")"}')"
    
    echo
}

generate_report() {
    print_header "📊 Validation Report"
    
    echo "Test Results Summary:"
    echo "===================="
    echo "Total Tests: $TOTAL_TESTS"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"
    echo "Success Rate: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"
    echo
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}🎉 ALL TESTS PASSED! Your IPFS node is fully functional.${NC}"
        echo
        echo "🚀 Quick Start Commands:"
        echo "  ipfs-tools status           - Check node status"
        echo "  ipfs-tools ssd-health       - Check SSD health"
        echo "  ipfs-tools download <contract> <token_id> - Download NFT"
        echo "  ipfs-tools csv /tmp/validation_test.csv - Test CSV processing"
        echo
        echo "🌐 Web Interfaces:"
        echo "  IPFS WebUI: http://$(hostname -I | awk '{print $1}'):5001/webui/"
        echo "  IPFS Gateway: http://$(hostname -I | awk '{print $1}'):8080/ipfs/"
        echo
        echo "🔧 Advanced Commands:"
        echo "  sudo ipfs-tools ssd-optimize - Optimize SSD (if not done)"
        echo "  ipfs-tools backup backup     - Create full backup"
        echo "  ipfs-tools monitor 60        - Continuous monitoring"
        
        return 0
    else
        echo -e "${RED}❌ $FAILED_TESTS TEST(S) FAILED${NC}"
        echo
        echo "🔧 Troubleshooting Steps:"
        
        if ! systemctl is-active ipfs &>/dev/null; then
            echo "  1. Start IPFS service: sudo systemctl start ipfs"
        fi
        
        if ! mountpoint -q /mnt/ssd; then
            echo "  2. Mount SSD: sudo mount /dev/sdX1 /mnt/ssd"
        fi
        
        if [ ! -f /opt/ipfs-tools/venv/bin/activate ]; then
            echo "  3. Reinstall Python environment: sudo ./setup_verification.sh"
        fi
        
        echo "  4. Check logs: sudo journalctl -u ipfs -f"
        echo "  5. Re-run setup: sudo ./ipfs_setup.sh"
        echo "  6. Get help: ipfs-tools"
        
        return 1
    fi
}

cleanup_test_files() {
    # Clean up test files
    rm -f /tmp/validation_test.csv
}

# Main execution
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Running as root. Some tests may not reflect normal user experience.${NC}"
    echo
fi

show_banner
show_system_info

test_prerequisites
test_directories
test_permissions
test_ipfs_installation
test_ipfs_functionality
test_management_tools
test_commands
test_ssd_optimization
test_nft_functionality
test_backup_functionality
test_network_connectivity
create_test_csv
run_performance_check

echo
generate_report
cleanup_test_files

exit $?