create_backup() {
    print_header "💾 Creating Backup"
    
    if [ "$EUID" -ne 0 ]; then
        print_error "Backup requires root privileges"
        echo "Please run: sudo $0 backup"
        return 1
    fi
    
    ipfs-tools backup backup
}

optimize_ssd() {
    print_header "🚀 SSD Optimization"
    
    if [ "$EUID" -ne 0 ]; then
        print_error "SSD optimization requires root privileges"
        echo "Please run: sudo $0 optimize-ssd"
        return 1
    fi
    
    if [ -f "/opt/ipfs-tools/ssd_optimization.sh" ]; then
        print_info "Running SSD optimization script..."
        /opt/ipfs-tools/ssd_optimization.sh
    else
        print_error "SSD optimization script not found"
        echo "Please ensure ssd_optimization.sh is installed"
        return 1
    fi
}

check_ssd_health() {
    print_header "💾 SSD Health Check"
    
    if [ -f "/opt/ipfs-tools/ssd_health_monitor.py" ]; then
        if [ -f "/opt/ipfs-tools/venv/bin/activate" ]; then
            source /opt/ipfs-tools/venv/bin/activate
        fi
        python3 /opt/ipfs-tools/ssd_health_monitor.py
    else
        print_warning "SSD health monitor not available"
        print_info "Basic disk usage check:"
        df -h /mnt/ssd
    fi
}#!/bin/bash

# IPFS Node Quick Start Script
# This script provides a convenient interface for managing your IPFS node

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

show_banner() {
    echo -e "${PURPLE}"
    echo "  ██╗██████╗ ███████╗███████╗    ███╗   ██╗ ██████╗ ██████╗ ███████╗"
    echo "  ██║██╔══██╗██╔════╝██╔════╝    ████╗  ██║██╔═══██╗██╔══██╗██╔════╝"
    echo "  ██║██████╔╝█████╗  ███████╗    ██╔██╗ ██║██║   ██║██║  ██║█████╗  "
    echo "  ██║██╔═══╝ ██╔══╝  ╚════██║    ██║╚██╗██║██║   ██║██║  ██║██╔══╝  "
    echo "  ██║██║     ██║     ███████║    ██║ ╚████║╚██████╔╝██████╔╝███████╗"
    echo "  ╚═╝╚═╝     ╚═╝     ╚══════╝    ╚═╝  ╚═══╝ ╚═════╝ ╚═════╝ ╚══════╝"
    echo -e "${NC}"
    echo -e "${CYAN}🏴‍☠️ Raspberry Pi IPFS Node Management System${NC}"
    echo -e "${CYAN}📡 NFT Download, Pin & Backup Solution${NC}"
    echo
}

check_prerequisites() {
    print_header "🔍 Checking Prerequisites"
    
    # Check if running on Raspberry Pi
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        print_warning "Not running on Raspberry Pi hardware"
    else
        print_success "Running on Raspberry Pi"
    fi
    
    # Check SSD mount
    if mountpoint -q /mnt/ssd; then
        print_success "SSD mounted at /mnt/ssd"
        df -h /mnt/ssd | tail -1 | awk '{print "  Available space: " $4}'
    else
        print_error "SSD not mounted at /mnt/ssd"
        echo "  Please mount your SSD first:"
        echo "  1. sudo mkdir -p /mnt/ssd"
        echo "  2. sudo mount /dev/sdX1 /mnt/ssd"
        echo "  3. Add to /etc/fstab for permanent mounting"
        return 1
    fi
    
    # Check if IPFS is installed
    if command -v ipfs &> /dev/null; then
        print_success "IPFS installed"
        ipfs version --number 2>/dev/null || echo "  Version check failed"
    else
        print_warning "IPFS not installed"
    fi
    
    # Check if scripts are available
    if [ -d "/opt/ipfs-tools" ]; then
        print_success "IPFS tools directory exists"
    else
        print_warning "IPFS tools not installed"
    fi
    
    echo
}

show_status() {
    print_header "📊 Current Status"
    
    # Run health monitor if available
    if [ -f "/opt/ipfs-tools/ipfs_health_monitor.py" ]; then
        source /opt/ipfs-tools/venv/bin/activate 2>/dev/null || true
        python3 /opt/ipfs-tools/ipfs_health_monitor.py
    elif command -v ipfs-tools &> /dev/null; then
        ipfs-tools status
    else
        # Fallback status check
        if systemctl is-active --quiet ipfs; then
            print_success "IPFS service is running"
        else
            print_error "IPFS service is not running"
        fi
        
        if curl -s http://127.0.0.1:5001/api/v0/version &>/dev/null; then
            print_success "IPFS API accessible"
        else
            print_error "IPFS API not accessible"
        fi
    fi
}

install_ipfs() {
    print_header "🔧 Installing IPFS Node"
    
    if [ "$EUID" -ne 0 ]; then
        print_error "Installation requires root privileges"
        echo "Please run: sudo $0 install"
        return 1
    fi
    
    if [ ! -f "./ipfs_setup.sh" ]; then
        print_error "ipfs_setup.sh not found in current directory"
        echo "Please ensure the setup script is available"
        return 1
    fi
    
    print_info "Starting IPFS installation..."
    ./ipfs_setup.sh
    
    if [ $? -eq 0 ]; then
        print_success "IPFS installation completed"
        # Install additional scripts
        install_additional_tools
    else
        print_error "IPFS installation failed"
        return 1
    fi
}

install_additional_tools() {
    print_info "Installing additional management tools..."
    
    # Copy health monitor
    if [ -f "ipfs_health_monitor.py" ]; then
        cp ipfs_health_monitor.py /opt/ipfs-tools/
        chmod +x /opt/ipfs-tools/ipfs_health_monitor.py
        print_success "Health monitor installed"
    fi
    
    # Copy backup script
    if [ -f "ipfs_backup_restore.sh" ]; then
        cp ipfs_backup_restore.sh /opt/ipfs-tools/
        chmod +x /opt/ipfs-tools/ipfs_backup_restore.sh
        ln -sf /opt/ipfs-tools/ipfs_backup_restore.sh /usr/local/bin/ipfs-backup
        print_success "Backup tools installed"
    fi
    
    # Update ipfs-tools wrapper
    cat > /usr/local/bin/ipfs-tools << 'EOF'
#!/bin/bash
source /opt/ipfs-tools/venv/bin/activate
case "$1" in
    "status")
        python3 /opt/ipfs-tools/ipfs_health_monitor.py
        ;;
    "monitor")
        shift
        python3 /opt/ipfs-tools/ipfs_health_monitor.py --continuous "$@"
        ;;
    "alerts")
        python3 /opt/ipfs-tools/ipfs_health_monitor.py --alerts
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
        /opt/ipfs-tools/ipfs_backup_restore.sh "$@"
        ;;
    *)
        echo "IPFS Tools for Raspberry Pi"
        echo "Usage: ipfs-tools [command] [options]"
        echo ""
        echo "Status & Monitoring:"
        echo "  status                  Check IPFS node health"
        echo "  monitor <interval>      Continuous monitoring"
        echo "  alerts                  Check for alerts only"
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
        echo "Examples:"
        echo "  ipfs-tools status"
        echo "  ipfs-tools monitor 60"
        echo "  ipfs-tools download 0x1234... 1"
        echo "  ipfs-tools csv nfts.csv"
        echo "  ipfs-tools backup backup"
        ;;
esac
EOF
    chmod +x /usr/local/bin/ipfs-tools
}

download_nft() {
    local contract="$1"
    local token_id="$2"
    
    if [ -z "$contract" ] || [ -z "$token_id" ]; then
        print_error "Please provide contract address and token ID"
        echo "Usage: $0 download <contract_address> <token_id>"
        return 1
    fi
    
    print_header "🎨 Downloading NFT"
    print_info "Contract: $contract"
    print_info "Token ID: $token_id"
    
    ipfs-tools download "$contract" "$token_id"
}

process_csv() {
    local csv_file="$1"
    
    if [ -z "$csv_file" ]; then
        print_error "Please provide CSV file path"
        echo "Usage: $0 csv <file.csv>"
        return 1
    fi
    
    if [ ! -f "$csv_file" ]; then
        print_error "CSV file not found: $csv_file"
        return 1
    fi
    
    print_header "📁 Processing CSV File"
    print_info "File: $csv_file"
    
    # Show preview of CSV
    echo "Preview (first 5 lines):"
    head -5 "$csv_file" | nl
    echo
    
    read -p "Continue processing? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ipfs-tools csv "$csv_file"
    else
        print_info "Processing cancelled"
    fi
}

show_nft_list() {
    print_header "🎭 Stored NFT Collections"
    ipfs-tools cleanup --list
}

optimize_ssd() {
    print_header "🚀 SSD Optimization"
    
    if [ "$EUID" -ne 0 ]; then
        print_error "SSD optimization requires root privileges"
        echo "Please run: sudo $0 optimize-ssd"
        return 1
    fi
    
    if [ -f "/opt/ipfs-tools/ssd_optimization.sh" ]; then
        print_info "Running SSD optimization script..."
        /opt/ipfs-tools/ssd_optimization.sh
    else
        print_error "SSD optimization script not found"
        echo "Please ensure ssd_optimization.sh is installed"
        return 1
    fi
}

check_ssd_health() {
    print_header "💾 SSD Health Check"
    
    if [ -f "/opt/ipfs-tools/ssd_health_monitor.py" ]; then
        if [ -f "/opt/ipfs-tools/venv/bin/activate" ]; then
            source /opt/ipfs-tools/venv/bin/activate
        fi
        python3 /opt/ipfs-tools/ssd_health_monitor.py
    else
        print_warning "SSD health monitor not available"
        print_info "Basic disk usage check:"
        df -h /mnt/ssd
    fi
}

show_logs() {
    print_header "📋 IPFS Service Logs"
    echo "Press Ctrl+C to exit log view"
    echo
    sudo journalctl -u ipfs -f
}

restart_ipfs() {
    print_header "🔄 Restarting IPFS Service"
    
    if [ "$EUID" -ne 0 ]; then
        print_error "Restart requires root privileges"
        echo "Please run: sudo $0 restart"
        return 1
    fi
    
    print_info "Stopping IPFS..."
    systemctl stop ipfs
    
    print_info "Starting IPFS..."
    systemctl start ipfs
    
    sleep 5
    
    if systemctl is-active --quiet ipfs; then
        print_success "IPFS service restarted successfully"
    else
        print_error "Failed to restart IPFS service"
        echo "Check logs with: sudo journalctl -u ipfs -f"
    fi
}

show_help() {
    echo "IPFS Node Management Commands:"
    echo
    echo "Setup & Installation:"
    echo "  $0 install              Install IPFS node and tools"
    echo "  $0 check                Check prerequisites"
    echo
    echo "Status & Monitoring:"
    echo "  $0 status               Show current status"
    echo "  $0 monitor [interval]   Start continuous monitoring"
    echo "  $0 logs                 View service logs"
    echo
    echo "NFT Management:"
    echo "  $0 download <contract> <token_id>  Download single NFT"
    echo "  $0 csv <file.csv>       Process NFTs from CSV"
    echo "  $0 list                 List stored NFTs"
    echo
    echo "Service Management:"
    echo "  $0 start                Start IPFS service"
    echo "  $0 stop                 Stop IPFS service"
    echo "  $0 restart              Restart IPFS service"
    echo
    echo "Backup & Maintenance:"
    echo "  $0 backup               Create full backup"
    echo "  $0 cleanup              Show cleanup options"
    echo "  $0 ssd-health           Check SSD health status"
    echo "  $0 optimize-ssd         Optimize SSD for IPFS (requires sudo)"
    echo
    echo "Web Interfaces:"
    echo "  IPFS WebUI: http://127.0.0.1:5001/webui/"
    echo "  IPFS Gateway: http://127.0.0.1:8080/ipfs/"
    echo
}

# Main command handling
case "$1" in
    "install")
        show_banner
        install_ipfs
        ;;
    "check")
        show_banner
        check_prerequisites
        ;;
    "status")
        show_banner
        show_status
        ;;
    "monitor")
        ipfs-tools monitor "${2:-60}"
        ;;
    "download")
        download_nft "$2" "$3"
        ;;
    "csv")
        process_csv "$2"
        ;;
    "list")
        show_nft_list
        ;;
    "start")
        [ "$EUID" -eq 0 ] && systemctl start ipfs || echo "Run with sudo"
        ;;
    "stop")
        [ "$EUID" -eq 0 ] && systemctl stop ipfs || echo "Run with sudo"
        ;;
    "restart")
        restart_ipfs
        ;;
    "logs")
        show_logs
        ;;
    "ssd-health")
        check_ssd_health
        ;;
    "optimize-ssd")
        optimize_ssd
        ;;
    "backup")
        create_backup
        ;;
    "cleanup")
        ipfs-tools cleanup --list
        echo
        echo "To remove specific NFT: ipfs-tools cleanup --cleanup <contract> <token_id>"
        ;;
    *)
        show_banner
        show_help
        ;;
esac