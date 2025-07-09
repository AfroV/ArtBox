#!/bin/bash

# IPFS Backup and Restore Script
# Manages backups of IPFS data, NFT collections, and configurations

set -e

# Configuration
BACKUP_DIR="/mnt/ssd/backups"
IPFS_DATA_DIR="/mnt/ssd/ipfs"
NFT_DATA_DIR="/mnt/ssd/nft_data"
SCRIPT_DIR="/opt/ipfs-tools"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

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

create_backup_dir() {
    mkdir -p "$BACKUP_DIR"
    chmod 755 "$BACKUP_DIR"
    chown ipfs:ipfs "$BACKUP_DIR" 2>/dev/null || true
}

backup_ipfs_config() {
    print_status "Backing up IPFS configuration..."
    
    if [ -f "$IPFS_DATA_DIR/config" ]; then
        cp "$IPFS_DATA_DIR/config" "$BACKUP_DIR/ipfs-config-${TIMESTAMP}.json"
        print_status "IPFS config backed up to: ipfs-config-${TIMESTAMP}.json"
    else
        print_error "IPFS config file not found"
        return 1
    fi
}

backup_nft_data() {
    print_status "Backing up NFT data..."
    
    if [ -d "$NFT_DATA_DIR" ]; then
        cd /mnt/ssd
        tar -czf "$BACKUP_DIR/nft-data-${TIMESTAMP}.tar.gz" nft_data/
        print_status "NFT data backed up to: nft-data-${TIMESTAMP}.tar.gz"
        
        # Create a summary of backed up NFTs
        find "$NFT_DATA_DIR" -name "*_summary.json" | wc -l > "$BACKUP_DIR/nft-count-${TIMESTAMP}.txt"
        echo "NFT count: $(cat "$BACKUP_DIR/nft-count-${TIMESTAMP}.txt")"
    else
        print_warning "NFT data directory not found"
    fi
}

backup_pinned_hashes() {
    print_status "Backing up pinned IPFS hashes..."
    
    if systemctl is-active --quiet ipfs; then
        export IPFS_PATH="$IPFS_DATA_DIR"
        sudo -u ipfs /usr/local/bin/ipfs pin ls > "$BACKUP_DIR/pinned-hashes-${TIMESTAMP}.txt"
        print_status "Pinned hashes backed up to: pinned-hashes-${TIMESTAMP}.txt"
    else
        print_warning "IPFS service not running, cannot backup pinned hashes"
    fi
}

backup_scripts() {
    print_status "Backing up management scripts..."
    
    if [ -d "$SCRIPT_DIR" ]; then
        tar -czf "$BACKUP_DIR/ipfs-tools-${TIMESTAMP}.tar.gz" -C /opt ipfs-tools/
        print_status "Scripts backed up to: ipfs-tools-${TIMESTAMP}.tar.gz"
    else
        print_warning "Scripts directory not found"
    fi
}

list_backups() {
    print_header "📋 Available Backups"
    echo "===================="
    
    if [ ! -d "$BACKUP_DIR" ]; then
        print_warning "No backup directory found"
        return
    fi
    
    echo "IPFS Configurations:"
    ls -la "$BACKUP_DIR"/ipfs-config-*.json 2>/dev/null || echo "  None found"
    
    echo
    echo "NFT Data Archives:"
    ls -la "$BACKUP_DIR"/nft-data-*.tar.gz 2>/dev/null || echo "  None found"
    
    echo
    echo "Pinned Hashes Lists:"
    ls -la "$BACKUP_DIR"/pinned-hashes-*.txt 2>/dev/null || echo "  None found"
    
    echo
    echo "Script Backups:"
    ls -la "$BACKUP_DIR"/ipfs-tools-*.tar.gz 2>/dev/null || echo "  None found"
}

restore_ipfs_config() {
    local config_file="$1"
    
    if [ -z "$config_file" ]; then
        print_error "Please specify config file to restore"
        return 1
    fi
    
    if [ ! -f "$BACKUP_DIR/$config_file" ]; then
        print_error "Config file not found: $BACKUP_DIR/$config_file"
        return 1
    fi
    
    print_status "Stopping IPFS service..."
    systemctl stop ipfs
    
    print_status "Restoring IPFS configuration..."
    cp "$BACKUP_DIR/$config_file" "$IPFS_DATA_DIR/config"
    chown ipfs:ipfs "$IPFS_DATA_DIR/config"
    
    print_status "Starting IPFS service..."
    systemctl start ipfs
    
    print_status "IPFS configuration restored successfully"
}

restore_nft_data() {
    local archive_file="$1"
    
    if [ -z "$archive_file" ]; then
        print_error "Please specify archive file to restore"
        return 1
    fi
    
    if [ ! -f "$BACKUP_DIR/$archive_file" ]; then
        print_error "Archive file not found: $BACKUP_DIR/$archive_file"
        return 1
    fi
    
    print_warning "This will overwrite existing NFT data. Continue? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        print_status "Restore cancelled"
        return 0
    fi
    
    print_status "Restoring NFT data..."
    cd /mnt/ssd
    tar -xzf "$BACKUP_DIR/$archive_file"
    chown -R ipfs:ipfs nft_data/
    
    print_status "NFT data restored successfully"
}

restore_pinned_hashes() {
    local hashes_file="$1"
    
    if [ -z "$hashes_file" ]; then
        print_error "Please specify hashes file to restore"
        return 1
    fi
    
    if [ ! -f "$BACKUP_DIR/$hashes_file" ]; then
        print_error "Hashes file not found: $BACKUP_DIR/$hashes_file"
        return 1
    fi
    
    if ! systemctl is-active --quiet ipfs; then
        print_error "IPFS service not running"
        return 1
    fi
    
    print_status "Restoring pinned hashes..."
    export IPFS_PATH="$IPFS_DATA_DIR"
    
    while IFS= read -r line; do
        hash=$(echo "$line" | awk '{print $1}')
        if [ -n "$hash" ] && [[ "$hash" =~ ^Qm[a-zA-Z0-9]{44}$ ]]; then
            print_status "Pinning: $hash"
            sudo -u ipfs /usr/local/bin/ipfs pin add "$hash" || print_warning "Failed to pin: $hash"
        fi
    done < "$BACKUP_DIR/$hashes_file"
    
    print_status "Pinned hashes restored"
}

cleanup_old_backups() {
    local days="${1:-30}"
    
    print_status "Cleaning up backups older than $days days..."
    
    find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$days -delete
    find "$BACKUP_DIR" -name "*.json" -mtime +$days -delete
    find "$BACKUP_DIR" -name "*.txt" -mtime +$days -delete
    
    print_status "Old backups cleaned up"
}

create_full_backup() {
    print_header "🔄 Creating Full Backup"
    print_status "Timestamp: $TIMESTAMP"
    
    create_backup_dir
    backup_ipfs_config
    backup_nft_data
    backup_pinned_hashes
    backup_scripts
    
    # Create backup manifest
    cat > "$BACKUP_DIR/backup-manifest-${TIMESTAMP}.txt" << EOF
IPFS Node Backup Manifest
========================
Date: $(date)
Hostname: $(hostname)
IPFS Version: $(sudo -u ipfs /usr/local/bin/ipfs version --number 2>/dev/null || echo "Unknown")

Files in this backup:
- ipfs-config-${TIMESTAMP}.json
- nft-data-${TIMESTAMP}.tar.gz
- pinned-hashes-${TIMESTAMP}.txt
- ipfs-tools-${TIMESTAMP}.tar.gz
- nft-count-${TIMESTAMP}.txt

Total backup size: $(du -sh "$BACKUP_DIR" | cut -f1)
EOF
    
    print_status "Backup manifest created: backup-manifest-${TIMESTAMP}.txt"
    print_status "✅ Full backup completed successfully!"
    print_status "📁 Backup location: $BACKUP_DIR"
}

show_backup_size() {
    if [ -d "$BACKUP_DIR" ]; then
        print_header "💾 Backup Directory Size"
        du -sh "$BACKUP_DIR"
        echo
        df -h "$BACKUP_DIR"
    else
        print_warning "Backup directory not found"
    fi
}

usage() {
    echo "IPFS Backup and Restore Utility"
    echo "Usage: $0 [command] [options]"
    echo
    echo "Commands:"
    echo "  backup              Create full backup"
    echo "  list               List available backups"
    echo "  restore-config     Restore IPFS configuration"
    echo "  restore-nft        Restore NFT data"
    echo "  restore-pins       Restore pinned hashes"
    echo "  cleanup [days]     Remove backups older than N days (default: 30)"
    echo "  size               Show backup directory size"
    echo
    echo "Examples:"
    echo "  $0 backup"
    echo "  $0 list"
    echo "  $0 restore-config ipfs-config-20241225_120000.json"
    echo "  $0 restore-nft nft-data-20241225_120000.tar.gz"
    echo "  $0 cleanup 7"
}

# Main script logic
case "$1" in
    "backup")
        if [ "$EUID" -ne 0 ]; then
            print_error "Please run as root (use sudo)"
            exit 1
        fi
        create_full_backup
        ;;
    "list")
        list_backups
        ;;
    "restore-config")
        if [ "$EUID" -ne 0 ]; then
            print_error "Please run as root (use sudo)"
            exit 1
        fi
        restore_ipfs_config "$2"
        ;;
    "restore-nft")
        if [ "$EUID" -ne 0 ]; then
            print_error "Please run as root (use sudo)"
            exit 1
        fi
        restore_nft_data "$2"
        ;;
    "restore-pins")
        if [ "$EUID" -ne 0 ]; then
            print_error "Please run as root (use sudo)"
            exit 1
        fi
        restore_pinned_hashes "$2"
        ;;
    "cleanup")
        if [ "$EUID" -ne 0 ]; then
            print_error "Please run as root (use sudo)"
            exit 1
        fi
        cleanup_old_backups "$2"
        ;;
    "size")
        show_backup_size
        ;;
    *)
        usage
        ;;
esac