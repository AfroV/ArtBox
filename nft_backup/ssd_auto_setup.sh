#!/bin/bash

# SSD Mount and Directory Setup Script
# Sets up IPFS directories on existing SSD without formatting
# For use when SSD already contains Raspberry Pi OS

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

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

show_banner() {
    echo -e "${PURPLE}"
    echo "  ███████╗███████╗██████╗     ██████╗ ██╗██████╗ ███████╗ ██████╗████████╗ ██████╗ ██████╗ ██╗   ██╗"
    echo "  ██╔════╝██╔════╝██╔══██╗    ██╔══██╗██║██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗╚██╗ ██╔╝"
    echo "  ███████╗███████╗██║  ██║    ██║  ██║██║██████╔╝█████╗  ██║        ██║   ██║   ██║██████╔╝ ╚████╔╝ "
    echo "  ╚════██║╚════██║██║  ██║    ██║  ██║██║██╔══██╗██╔══╝  ██║        ██║   ██║   ██║██╔══██╗  ╚██╔╝  "
    echo "  ███████║███████║██████╔╝    ██████╔╝██║██║  ██║███████╗╚██████╗   ██║   ╚██████╔╝██║  ██║   ██║   "
    echo "  ╚══════╝╚══════╝╚═════╝     ╚═════╝ ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝   "
    echo -e "${NC}"
    echo -e "${CYAN}📁 SSD Directory Setup for IPFS (No Formatting)${NC}"
    echo
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script needs root privileges for directory creation"
        print_info "Please run: sudo $0"
        exit 1
    fi
}

detect_storage_setup() {
    print_header "💾 Detecting Current Storage Setup"
    
    print_info "Current storage layout:"
    df -h
    echo
    
    print_info "Current mount points:"
    lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE
    echo
    
    # Check if we're running from SSD
    SCRIPT_DIR=$(pwd)
    SCRIPT_DEVICE=$(df "$SCRIPT_DIR" | tail -1 | awk '{print $1}' | sed 's/[0-9]*$//')
    
    print_info "Script running from: $SCRIPT_DIR"
    print_info "Device: $SCRIPT_DEVICE"
    
    # Check if root is on SSD (common setup)
    ROOT_DEVICE=$(df / | tail -1 | awk '{print $1}' | sed 's/[0-9]*$//')
    
    if [[ "$ROOT_DEVICE" == "/dev/sd"* ]] || [[ "$ROOT_DEVICE" == "/dev/nvme"* ]]; then
        print_success "Root filesystem appears to be on SSD: $ROOT_DEVICE"
        SSD_ROOT=true
    else
        print_info "Root filesystem on: $ROOT_DEVICE (likely SD card)"
        SSD_ROOT=false
    fi
    
    echo
}

choose_ipfs_location() {
    print_header "📂 Choosing IPFS Data Location"
    
    if [ "$SSD_ROOT" = true ]; then
        print_info "Since you're running from SSD, we'll create IPFS directories on the root filesystem"
        IPFS_BASE_DIR="/opt/ipfs-data"
        print_success "IPFS data will be stored at: $IPFS_BASE_DIR"
    else
        print_info "Looks like you're running from SD card but may have an SSD mounted"
        echo
        echo "Where would you like to store IPFS data?"
        echo "1. On root filesystem (current location): $(df / | tail -1 | awk '{print $6}')"
        echo "2. On mounted SSD (if available)"
        echo "3. Custom location"
        echo
        
        while true; do
            echo -n "Choose option (1-3): "
            read choice
            
            case $choice in
                1)
                    IPFS_BASE_DIR="/opt/ipfs-data"
                    break
                    ;;
                2)
                    # Look for mounted SSD
                    SSD_MOUNT=$(lsblk -o MOUNTPOINT,TYPE | grep -E "(ssd|nvme)" | awk '{print $1}' | head -1)
                    if [ -n "$SSD_MOUNT" ] && [ "$SSD_MOUNT" != "/" ]; then
                        IPFS_BASE_DIR="$SSD_MOUNT/ipfs-data"
                        break
                    else
                        print_error "No separate SSD mount found"
                        continue
                    fi
                    ;;
                3)
                    echo -n "Enter custom path: "
                    read IPFS_BASE_DIR
                    if [ -n "$IPFS_BASE_DIR" ]; then
                        break
                    fi
                    ;;
                *)
                    print_error "Invalid choice. Please enter 1, 2, or 3"
                    ;;
            esac
        done
    fi
    
    print_success "IPFS data location: $IPFS_BASE_DIR"
    echo
}

create_ipfs_directories() {
    print_header "📁 Creating IPFS Directory Structure"
    
    # Create main directories
    IPFS_DATA_DIR="$IPFS_BASE_DIR/ipfs"
    NFT_DATA_DIR="$IPFS_BASE_DIR/nft_data"
    BACKUP_DIR="$IPFS_BASE_DIR/backups"
    
    print_info "Creating directories..."
    mkdir -p "$IPFS_DATA_DIR"
    mkdir -p "$NFT_DATA_DIR" 
    mkdir -p "$BACKUP_DIR"
    mkdir -p "/opt/ipfs-tools"
    
    print_success "Created: $IPFS_DATA_DIR"
    print_success "Created: $NFT_DATA_DIR"
    print_success "Created: $BACKUP_DIR"
    print_success "Created: /opt/ipfs-tools"
    
    # Set permissions
    print_info "Setting basic permissions..."
    chmod 755 "$IPFS_BASE_DIR"
    chmod 755 "$IPFS_DATA_DIR"
    chmod 755 "$NFT_DATA_DIR"
    chmod 755 "$BACKUP_DIR"
    chmod 755 "/opt/ipfs-tools"
    
    print_success "Permissions set"
    echo
}

create_symlinks() {
    print_header "🔗 Creating Standard Symlinks"
    
    # Create symlinks to standard locations for compatibility
    if [ "$IPFS_BASE_DIR" != "/mnt/ssd" ]; then
        print_info "Creating compatibility symlinks..."
        
        # Remove existing /mnt/ssd if it's a directory
        if [ -d "/mnt/ssd" ] && [ ! -L "/mnt/ssd" ]; then
            rmdir /mnt/ssd 2>/dev/null || print_warning "Could not remove /mnt/ssd directory"
        fi
        
        # Create symlink
        if [ ! -e "/mnt/ssd" ]; then
            ln -sf "$IPFS_BASE_DIR" "/mnt/ssd"
            print_success "Created symlink: /mnt/ssd -> $IPFS_BASE_DIR"
        else
            print_warning "Symlink /mnt/ssd already exists"
        fi
    fi
    
    echo
}

optimize_mount_options() {
    print_header "⚡ Optimizing Mount Options"
    
    # Get the device containing our IPFS directory
    IPFS_DEVICE=$(df "$IPFS_BASE_DIR" | tail -1 | awk '{print $1}')
    IPFS_MOUNT=$(df "$IPFS_BASE_DIR" | tail -1 | awk '{print $6}')
    
    print_info "IPFS data device: $IPFS_DEVICE"
    print_info "Mount point: $IPFS_MOUNT"
    
    # Check current mount options
    CURRENT_OPTIONS=$(mount | grep "$IPFS_DEVICE" | awk '{print $6}' | tr -d '()')
    print_info "Current mount options: $CURRENT_OPTIONS"
    
    # Check if optimizations are needed
    NEEDS_OPTIMIZATION=false
    
    if [[ "$CURRENT_OPTIONS" != *"noatime"* ]]; then
        print_warning "noatime not enabled (reduces write operations)"
        NEEDS_OPTIMIZATION=true
    fi
    
    if [[ "$CURRENT_OPTIONS" != *"discard"* ]] && [[ "$IPFS_DEVICE" == *"sd"* || "$IPFS_DEVICE" == *"nvme"* ]]; then
        print_warning "discard not enabled (TRIM support for SSD)"
        NEEDS_OPTIMIZATION=true
    fi
    
    if [ "$NEEDS_OPTIMIZATION" = true ]; then
        print_warning "Mount optimizations recommended"
        echo "To optimize mount options, add the following to /etc/fstab:"
        echo "$IPFS_DEVICE $IPFS_MOUNT ext4 defaults,noatime,discard,errors=remount-ro 0 1"
        echo
        echo "Then remount with: sudo mount -o remount $IPFS_MOUNT"
        
        echo -n "Apply optimizations now? (y/N): "
        read apply_opts
        if [[ "$apply_opts" =~ ^[Yy]$ ]]; then
            apply_mount_optimizations "$IPFS_DEVICE" "$IPFS_MOUNT"
        fi
    else
        print_success "Mount options are already optimized"
    fi
    
    echo
}

apply_mount_optimizations() {
    local device="$1"
    local mount_point="$2"
    
    print_info "Backing up /etc/fstab..."
    cp /etc/fstab "/etc/fstab.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Update fstab
    print_info "Updating /etc/fstab..."
    
    # Remove existing entry
    sed -i "\|$mount_point|d" /etc/fstab
    
    # Add optimized entry
    echo "$device $mount_point ext4 defaults,noatime,discard,errors=remount-ro 0 1" >> /etc/fstab
    
    # Remount
    print_info "Remounting with optimizations..."
    mount -o remount,noatime,discard "$mount_point"
    
    print_success "Mount optimizations applied"
}

check_available_space() {
    print_header "💾 Checking Available Space"
    
    AVAILABLE_GB=$(df -BG "$IPFS_BASE_DIR" | tail -1 | awk '{print $4}' | tr -d 'G')
    TOTAL_GB=$(df -BG "$IPFS_BASE_DIR" | tail -1 | awk '{print $2}' | tr -d 'G')
    USED_PERCENT=$(df "$IPFS_BASE_DIR" | tail -1 | awk '{print $5}' | tr -d '%')
    
    print_info "Storage summary for IPFS location:"
    echo "  Total space: ${TOTAL_GB}GB"
    echo "  Available: ${AVAILABLE_GB}GB"
    echo "  Used: ${USED_PERCENT}%"
    
    if [ "$AVAILABLE_GB" -lt 10 ]; then
        print_error "Less than 10GB available - IPFS needs more space"
        exit 1
    elif [ "$AVAILABLE_GB" -lt 50 ]; then
        print_warning "Less than 50GB available - consider freeing up space"
    else
        print_success "Sufficient space available for IPFS"
    fi
    
    echo
}

create_configuration_file() {
    print_header "📝 Creating Configuration File"
    
    # Create config file for the installer
    cat > "/tmp/ipfs_config.env" << EOF
# IPFS Installation Configuration
# Generated by ssd_mount_setup.sh

IPFS_DATA_DIR="$IPFS_DATA_DIR"
NFT_DATA_DIR="$NFT_DATA_DIR"
BACKUP_DIR="$BACKUP_DIR"
IPFS_BASE_DIR="$IPFS_BASE_DIR"
EOF
    
    print_success "Configuration saved to /tmp/ipfs_config.env"
    print_info "This will be used by the main installer"
    echo
}

show_summary() {
    print_header "📋 Setup Summary"
    
    echo "SSD Directory Setup Completed!"
    echo "=============================="
    echo "IPFS data directory: $IPFS_DATA_DIR"
    echo "NFT data directory: $NFT_DATA_DIR"
    echo "Backup directory: $BACKUP_DIR"
    echo "Tools directory: /opt/ipfs-tools"
    echo
    echo "Compatibility:"
    echo "  Standard path: /mnt/ssd -> $IPFS_BASE_DIR"
    echo
    echo "Available space: ${AVAILABLE_GB}GB"
    echo
    print_success "✅ Directories ready for IPFS installation!"
    print_info "Next step: Run 'sudo ./ipfs_setup.sh'"
}

# Main execution
show_banner

# Only run with sudo
check_root

print_warning "This script sets up IPFS directories on your existing SSD."
print_warning "⚠️  NO FORMATTING will be performed - your data is safe!"
echo
echo "The script will:"
echo "  1. Detect your current storage setup"
echo "  2. Create IPFS directories in optimal location"
echo "  3. Set up compatibility symlinks"
echo "  4. Optimize mount options (optional)"
echo "  5. Check available space"
echo

read -p "Continue with directory setup? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Directory setup cancelled"
    exit 0
fi

detect_storage_setup
choose_ipfs_location
create_ipfs_directories
create_symlinks
optimize_mount_options
check_available_space
create_configuration_file
show_summary

print_success "🎉 SSD directory setup completed successfully!"
print_info "Your existing data is safe - no formatting was performed."