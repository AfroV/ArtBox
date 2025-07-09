#!/bin/bash

# SSD Optimization Script for IPFS on Raspberry Pi
# Optimizes SSD performance, reduces wear, and extends lifespan

set -e

# Configuration
SSD_MOUNT_POINT="/mnt/ssd"
IPFS_DATA_DIR="/mnt/ssd/ipfs"
NFT_DATA_DIR="/mnt/ssd/nft_data"
BACKUP_DIR="/mnt/ssd/backups"

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
    echo "  ███████╗███████╗██████╗      ██████╗ ██████╗ ████████╗██╗███╗   ███╗██╗███████╗███████╗"
    echo "  ██╔════╝██╔════╝██╔══██╗    ██╔═══██╗██╔══██╗╚══██╔══╝██║████╗ ████║██║╚══███╔╝██╔════╝"
    echo "  ███████╗███████╗██║  ██║    ██║   ██║██████╔╝   ██║   ██║██╔████╔██║██║  ███╔╝ █████╗  "
    echo "  ╚════██║╚════██║██║  ██║    ██║   ██║██╔═══╝    ██║   ██║██║╚██╔╝██║██║ ███╔╝  ██╔══╝  "
    echo "  ███████║███████║██████╔╝    ╚██████╔╝██║        ██║   ██║██║ ╚═╝ ██║██║███████╗███████╗"
    echo "  ╚══════╝╚══════╝╚═════╝      ╚═════╝ ╚═╝        ╚═╝   ╚═╝╚═╝     ╚═╝╚═╝╚══════╝╚══════╝"
    echo -e "${NC}"
    echo -e "${CYAN}🚀 SSD Optimization for IPFS on Raspberry Pi${NC}"
    echo
}

check_prerequisites() {
    print_header "🔍 Checking Prerequisites"
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
    
    # Check if SSD is mounted
    if ! mountpoint -q "$SSD_MOUNT_POINT"; then
        print_error "SSD not mounted at $SSD_MOUNT_POINT"
        exit 1
    fi
    
    # Get SSD device
    SSD_DEVICE=$(df "$SSD_MOUNT_POINT" | tail -1 | awk '{print $1}' | sed 's/[0-9]*$//')
    print_success "SSD detected: $SSD_DEVICE"
    
    # Check if it's actually an SSD
    if [ -f "/sys/block/$(basename $SSD_DEVICE)/queue/rotational" ]; then
        ROTATIONAL=$(cat "/sys/block/$(basename $SSD_DEVICE)/queue/rotational")
        if [ "$ROTATIONAL" = "0" ]; then
            print_success "Confirmed: Non-rotational storage (SSD/NVMe)"
        else
            print_warning "Warning: Storage appears to be rotational (HDD)"
            read -p "Continue anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
    
    echo
}

detect_ssd_info() {
    print_header "💾 SSD Information"
    
    # Get device info
    SSD_PARTITION=$(df "$SSD_MOUNT_POINT" | tail -1 | awk '{print $1}')
    SSD_DEVICE=$(echo "$SSD_PARTITION" | sed 's/[0-9]*$//')
    
    echo "Device: $SSD_DEVICE"
    echo "Partition: $SSD_PARTITION"
    echo "Mount point: $SSD_MOUNT_POINT"
    
    # Check filesystem
    FILESYSTEM=$(df -T "$SSD_MOUNT_POINT" | tail -1 | awk '{print $2}')
    echo "Filesystem: $FILESYSTEM"
    
    # Get size info
    SIZE_INFO=$(df -h "$SSD_MOUNT_POINT" | tail -1)
    echo "Size info: $SIZE_INFO"
    
    # Check TRIM support
    if lsblk -D | grep -q "$(basename $SSD_DEVICE)"; then
        TRIM_SUPPORT=$(lsblk -D "$SSD_DEVICE" | tail -1 | awk '{print $3}')
        if [ "$TRIM_SUPPORT" != "0B" ] && [ -n "$TRIM_SUPPORT" ]; then
            print_success "TRIM supported"
        else
            print_warning "TRIM may not be supported"
        fi
    fi
    
    # Check current scheduler
    SCHEDULER_FILE="/sys/block/$(basename $SSD_DEVICE)/queue/scheduler"
    if [ -f "$SCHEDULER_FILE" ]; then
        CURRENT_SCHEDULER=$(cat "$SCHEDULER_FILE" | grep -o '\[.*\]' | tr -d '[]')
        echo "Current I/O scheduler: $CURRENT_SCHEDULER"
    fi
    
    echo
}

optimize_filesystem_mount() {
    print_header "📁 Optimizing Filesystem Mount Options"
    
    # Create backup of fstab
    cp /etc/fstab /etc/fstab.backup.$(date +%Y%m%d_%H%M%S)
    print_info "Created fstab backup"
    
    # Get current fstab entry
    FSTAB_LINE=$(grep "$SSD_MOUNT_POINT" /etc/fstab || echo "")
    
    if [ -n "$FSTAB_LINE" ]; then
        print_info "Current fstab entry found"
        echo "  $FSTAB_LINE"
        
        # Extract device and filesystem type
        DEVICE=$(echo "$FSTAB_LINE" | awk '{print $1}')
        FS_TYPE=$(echo "$FSTAB_LINE" | awk '{print $3}')
        
        # Define optimized mount options based on filesystem
        case "$FS_TYPE" in
            "ext4")
                MOUNT_OPTIONS="defaults,noatime,nodiratime,discard,errors=remount-ro"
                ;;
            "btrfs")
                MOUNT_OPTIONS="defaults,noatime,nodiratime,discard,compress=zstd,space_cache=v2"
                ;;
            "xfs")
                MOUNT_OPTIONS="defaults,noatime,nodiratime,discard,largeio,inode64"
                ;;
            *)
                MOUNT_OPTIONS="defaults,noatime,nodiratime,discard"
                ;;
        esac
        
        # Create new fstab entry
        NEW_FSTAB_LINE="$DEVICE $SSD_MOUNT_POINT $FS_TYPE $MOUNT_OPTIONS 0 2"
        
        # Replace the line in fstab
        sed -i "\|$SSD_MOUNT_POINT|c\\$NEW_FSTAB_LINE" /etc/fstab
        
        print_success "Updated fstab with optimized mount options"
        print_info "New entry: $NEW_FSTAB_LINE"
        
        # Remount to apply new options
        print_info "Remounting with new options..."
        systemctl stop ipfs 2>/dev/null || true
        sleep 2
        
        umount "$SSD_MOUNT_POINT"
        mount "$SSD_MOUNT_POINT"
        
        print_success "Remounted with optimized options"
    else
        print_warning "No fstab entry found for $SSD_MOUNT_POINT"
        print_info "Please add SSD to fstab manually with optimized options"
    fi
    
    echo
}

optimize_io_scheduler() {
    print_header "⚡ Optimizing I/O Scheduler"
    
    SSD_DEVICE_NAME=$(basename $SSD_DEVICE)
    SCHEDULER_FILE="/sys/block/$SSD_DEVICE_NAME/queue/scheduler"
    
    if [ -f "$SCHEDULER_FILE" ]; then
        # Check available schedulers
        AVAILABLE_SCHEDULERS=$(cat "$SCHEDULER_FILE" | tr -d '[]' | tr ' ' '\n' | grep -v '^$')
        print_info "Available schedulers:"
        echo "$AVAILABLE_SCHEDULERS" | sed 's/^/  /'
        
        # Choose best scheduler for SSD
        if echo "$AVAILABLE_SCHEDULERS" | grep -q "none"; then
            BEST_SCHEDULER="none"
        elif echo "$AVAILABLE_SCHEDULERS" | grep -q "noop"; then
            BEST_SCHEDULER="noop"
        elif echo "$AVAILABLE_SCHEDULERS" | grep -q "deadline"; then
            BEST_SCHEDULER="deadline"
        else
            BEST_SCHEDULER=$(echo "$AVAILABLE_SCHEDULERS" | head -1)
        fi
        
        # Set scheduler
        echo "$BEST_SCHEDULER" > "$SCHEDULER_FILE"
        print_success "Set I/O scheduler to: $BEST_SCHEDULER"
        
        # Make permanent by creating udev rule
        cat > /etc/udev/rules.d/60-ssd-scheduler.rules << EOF
# SSD I/O Scheduler optimization
ACTION=="add|change", KERNEL=="$SSD_DEVICE_NAME", ATTR{queue/scheduler}="$BEST_SCHEDULER"
EOF
        print_success "Created udev rule for persistent scheduler setting"
    else
        print_warning "Cannot access scheduler settings for $SSD_DEVICE"
    fi
    
    echo
}

optimize_kernel_parameters() {
    print_header "🔧 Optimizing Kernel Parameters"
    
    # Create sysctl configuration for SSD optimization
    cat > /etc/sysctl.d/99-ssd-ipfs-optimization.conf << 'EOF'
# SSD and IPFS optimization parameters

# Reduce swappiness (SSD wear reduction)
vm.swappiness = 1

# Optimize dirty page handling for SSDs
vm.dirty_ratio = 5
vm.dirty_background_ratio = 2

# Reduce write cache flush frequency
vm.dirty_expire_centisecs = 1000
vm.dirty_writeback_centisecs = 500

# Optimize for many small files (IPFS characteristic)
fs.file-max = 2097152

# Network optimizations for IPFS
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# Reduce TCP timeouts for better P2P performance
net.ipv4.tcp_keepalive_time = 120
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 3

# Optimize for high connection count
net.core.somaxconn = 1024
net.core.netdev_max_backlog = 5000
EOF

    # Apply settings
    sysctl -p /etc/sysctl.d/99-ssd-ipfs-optimization.conf >/dev/null
    print_success "Applied kernel optimizations"
    
    echo
}

setup_trim_automation() {
    print_header "✂️ Setting Up TRIM Automation"
    
    # Check if fstrim timer is available
    if systemctl list-unit-files | grep -q fstrim.timer; then
        # Enable periodic TRIM
        systemctl enable fstrim.timer
        systemctl start fstrim.timer
        print_success "Enabled automatic TRIM (fstrim.timer)"
        
        # Show TRIM schedule
        TIMER_INFO=$(systemctl list-timers fstrim.timer | tail -1)
        print_info "TRIM schedule: $TIMER_INFO"
    else
        # Create custom TRIM service and timer
        cat > /etc/systemd/system/ssd-trim.service << EOF
[Unit]
Description=SSD TRIM
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/sbin/fstrim -v $SSD_MOUNT_POINT
EOF

        cat > /etc/systemd/system/ssd-trim.timer << EOF
[Unit]
Description=Weekly SSD TRIM
Requires=ssd-trim.service

[Timer]
OnCalendar=weekly
Persistent=true

[Install]
WantedBy=timers.target
EOF

        systemctl daemon-reload
        systemctl enable ssd-trim.timer
        systemctl start ssd-trim.timer
        print_success "Created and enabled custom TRIM timer"
    fi
    
    # Run immediate TRIM
    print_info "Running immediate TRIM..."
    fstrim -v "$SSD_MOUNT_POINT" || print_warning "TRIM operation may have failed"
    
    echo
}

optimize_ipfs_config() {
    print_header "🏗️ Optimizing IPFS Configuration for SSD"
    
    if [ -f "$IPFS_DATA_DIR/config" ]; then
        # Backup original config
        cp "$IPFS_DATA_DIR/config" "$IPFS_DATA_DIR/config.backup.$(date +%Y%m%d_%H%M%S)"
        
        # Stop IPFS for config changes
        systemctl stop ipfs 2>/dev/null || true
        
        # Apply SSD-optimized settings
        sudo -u ipfs IPFS_PATH="$IPFS_DATA_DIR" /usr/local/bin/ipfs config --json Datastore.BloomFilterSize 1048576
        sudo -u ipfs IPFS_PATH="$IPFS_DATA_DIR" /usr/local/bin/ipfs config --json Datastore.StorageGCWatermark 85
        sudo -u ipfs IPFS_PATH="$IPFS_DATA_DIR" /usr/local/bin/ipfs config --json Datastore.GCPeriod '"1h"'
        sudo -u ipfs IPFS_PATH="$IPFS_DATA_DIR" /usr/local/bin/ipfs config --json Reprovider.Interval '"12h"'
        sudo -u ipfs IPFS_PATH="$IPFS_DATA_DIR" /usr/local/bin/ipfs config --json Swarm.ConnMgr.LowWater 400
        sudo -u ipfs IPFS_PATH="$IPFS_DATA_DIR" /usr/local/bin/ipfs config --json Swarm.ConnMgr.HighWater 800
        sudo -u ipfs IPFS_PATH="$IPFS_DATA_DIR" /usr/local/bin/ipfs config --json Routing.Type '"dhtclient"'
        
        print_success "Applied SSD-optimized IPFS configuration"
        
        # Start IPFS
        systemctl start ipfs
        sleep 5
        
        if systemctl is-active ipfs >/dev/null; then
            print_success "IPFS restarted successfully"
        else
            print_error "IPFS failed to start - check configuration"
        fi
    else
        print_warning "IPFS config not found - run IPFS setup first"
    fi
    
    echo
}

setup_log_optimization() {
    print_header "📝 Optimizing Logging for SSD"
    
    # Configure systemd journal for SSD
    mkdir -p /etc/systemd/journald.conf.d
    cat > /etc/systemd/journald.conf.d/ssd-optimization.conf << 'EOF'
[Journal]
# Limit journal size to reduce SSD writes
SystemMaxUse=100M
RuntimeMaxUse=50M
# Compress logs
Compress=yes
# Reduce sync frequency
SyncIntervalSec=60s
EOF
    
    systemctl restart systemd-journald
    print_success "Optimized systemd journal for SSD"
    
    # Setup log rotation for IPFS
    cat > /etc/logrotate.d/ipfs << 'EOF'
/var/log/ipfs/*.log {
    daily
    missingok
    rotate 7
    compress
    notifempty
    create 0644 ipfs ipfs
    postrotate
        systemctl reload ipfs 2>/dev/null || true
    endscript
}
EOF
    
    print_success "Configured log rotation for IPFS"
    
    echo
}

create_monitoring_script() {
    print_header "📊 Creating SSD Health Monitoring"
    
    cat > /opt/ipfs-tools/ssd_health_monitor.py << 'EOF'
#!/usr/bin/env python3
"""
SSD Health Monitor for IPFS
Monitors SSD health, temperature, and wear indicators
"""

import subprocess
import json
import sys
import os
from pathlib import Path

def get_ssd_smart_data(device):
    """Get SMART data from SSD"""
    try:
        result = subprocess.run(['smartctl', '-A', '-j', device], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception as e:
        print(f"Error getting SMART data: {e}")
    return None

def get_disk_usage(mount_point):
    """Get disk usage statistics"""
    try:
        result = subprocess.run(['df', '-h', mount_point], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                return {
                    'total': parts[1],
                    'used': parts[2],
                    'available': parts[3],
                    'use_percent': parts[4]
                }
    except Exception as e:
        print(f"Error getting disk usage: {e}")
    return None

def check_trim_support(device):
    """Check if TRIM is supported and enabled"""
    try:
        result = subprocess.run(['lsblk', '-D', device], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                disc_gran = parts[2] if len(parts) > 2 else "0"
                return disc_gran != "0B" and disc_gran != "0"
    except Exception as e:
        print(f"Error checking TRIM support: {e}")
    return False

def main():
    # Auto-detect SSD device
    mount_point = "/mnt/ssd"
    
    try:
        # Get device from mount point
        result = subprocess.run(['df', mount_point], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                device_partition = lines[1].split()[0]
                # Remove partition number to get base device
                ssd_device = device_partition.rstrip('0123456789')
        else:
            ssd_device = "/dev/sda"  # Fallback
    except:
        ssd_device = "/dev/sda"  # Fallback
    
    print("🔍 SSD Health Report")
    print("=" * 40)
    print(f"Device: {ssd_device}")
    print(f"Mount: {mount_point}")
    print()
    
    # Disk usage
    usage = get_disk_usage(mount_point)
    if usage:
        print(f"💾 Disk Usage:")
        print(f"  Total: {usage['total']}")
        print(f"  Used: {usage['used']} ({usage['use_percent']})")
        print(f"  Available: {usage['available']}")
    
    # TRIM support
    trim_supported = check_trim_support(ssd_device)
    print(f"✂️  TRIM Support: {'✅ Yes' if trim_supported else '❌ No'}")
    
    # SMART data
    smart_data = get_ssd_smart_data(ssd_device)
    if smart_data and 'ata_smart_attributes' in smart_data:
        print(f"🏥 SMART Health:")
        attrs = smart_data['ata_smart_attributes']['table']
        
        # Key attributes for SSD health
        key_attrs = {
            5: "Reallocated Sectors",
            9: "Power-On Hours", 
            12: "Power Cycle Count",
            173: "Wear Leveling Count",
            177: "Wear Leveling Count",
            231: "SSD Life Left",
            233: "Media Wearout Indicator"
        }
        
        for attr in attrs:
            attr_id = attr['id']
            if attr_id in key_attrs:
                name = key_attrs[attr_id]
                value = attr['raw']['value']
                print(f"  {name}: {value}")
    else:
        print("🏥 SMART Health: Not available (may need sudo or smartmontools)")
    
    print("\n📈 Optimization Status:")
    
    # Check I/O scheduler
    try:
        device_name = os.path.basename(ssd_device)
        with open(f'/sys/block/{device_name}/queue/scheduler', 'r') as f:
            scheduler = f.read().strip()
            current = scheduler[scheduler.find('[')+1:scheduler.find(']')]
            print(f"  I/O Scheduler: {current}")
    except:
        print("  I/O Scheduler: Could not determine")
    
    # Check mount options
    try:
        with open('/proc/mounts', 'r') as f:
            for line in f:
                if mount_point in line:
                    parts = line.split()
                    if len(parts) > 3:
                        options = parts[3]
                        has_noatime = 'noatime' in options
                        has_discard = 'discard' in options
                        print(f"  noatime: {'✅' if has_noatime else '❌'}")
                        print(f"  discard: {'✅' if has_discard else '❌'}")
                    break
    except:
        print("  Mount options: Could not determine")

if __name__ == "__main__":
    main()
EOF
    
    chmod +x /opt/ipfs-tools/ssd_health_monitor.py
    print_success "Created SSD health monitoring script"
    
    # Add to ipfs-tools wrapper
    sed -i '/cleanup")/ a\    "ssd-health")\
        python3 /opt/ipfs-tools/ssd_health_monitor.py\
        ;;' /usr/local/bin/ipfs-tools 2>/dev/null || true
    
    echo
}

create_performance_test() {
    print_header "🏃 Creating Performance Test Script"
    
    cat > /opt/ipfs-tools/ssd_performance_test.sh << 'EOF'
#!/bin/bash

# SSD Performance Test for IPFS workload
# Tests sequential and random I/O performance

SSD_MOUNT="/mnt/ssd"
TEST_DIR="$SSD_MOUNT/performance_test"

echo "🚀 SSD Performance Test"
echo "======================"

# Check if fio is available
if ! command -v fio &> /dev/null; then
    echo "Installing fio for performance testing..."
    apt update && apt install -y fio
fi

mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

echo "📊 Running performance tests..."

# Sequential read test
echo "1. Sequential Read Test"
fio --name=seq-read --ioengine=libaio --iodepth=32 --rw=read --bs=1M --direct=1 --size=1G --numjobs=1 --runtime=30 --group_reporting --filename=test-seq-read

# Sequential write test  
echo "2. Sequential Write Test"
fio --name=seq-write --ioengine=libaio --iodepth=32 --rw=write --bs=1M --direct=1 --size=1G --numjobs=1 --runtime=30 --group_reporting --filename=test-seq-write

# Random read test (IPFS-like workload)
echo "3. Random Read Test (IPFS-like)"
fio --name=rand-read --ioengine=libaio --iodepth=16 --rw=randread --bs=4K --direct=1 --size=1G --numjobs=4 --runtime=30 --group_reporting --filename=test-rand-read

# Random write test
echo "4. Random Write Test"
fio --name=rand-write --ioengine=libaio --iodepth=16 --rw=randwrite --bs=4K --direct=1 --size=1G --numjobs=4 --runtime=30 --group_reporting --filename=test-rand-write

# Mixed workload (IPFS-like)
echo "5. Mixed Workload Test (70% read, 30% write)"
fio --name=mixed --ioengine=libaio --iodepth=16 --rw=randrw --rwmixread=70 --bs=4K --direct=1 --size=1G --numjobs=4 --runtime=30 --group_reporting --filename=test-mixed

# Cleanup
rm -f test-*

echo "✅ Performance tests completed"
echo "💡 For IPFS workloads, focus on:"
echo "   - Random 4K read/write performance"
echo "   - Mixed workload performance"
echo "   - Low latency for small operations"
EOF
    
    chmod +x /opt/ipfs-tools/ssd_performance_test.sh
    print_success "Created SSD performance test script"
    
    echo
}

show_optimization_summary() {
    print_header "📋 Optimization Summary"
    
    echo "✅ Completed Optimizations:"
    echo "  🔧 Filesystem mount options (noatime, discard)"
    echo "  ⚡ I/O scheduler optimization"
    echo "  🧠 Kernel parameter tuning"
    echo "  ✂️  Automatic TRIM setup"
    echo "  🏗️  IPFS configuration optimization"
    echo "  📝 Logging optimization"
    echo "  📊 Health monitoring tools"
    echo "  🏃 Performance testing tools"
    
    echo
    echo "🛠️ Available Commands:"
    echo "  ipfs-tools ssd-health    - Check SSD health"
    echo "  /opt/ipfs-tools/ssd_performance_test.sh - Run performance tests"
    echo "  sudo fstrim -v $SSD_MOUNT_POINT - Manual TRIM"
    echo "  systemctl status fstrim.timer - Check TRIM schedule"
    
    echo
    echo "📈 Expected Benefits:"
    echo "  • Reduced SSD wear and extended lifespan"
    echo "  • Improved IPFS performance"
    echo "  • Better random I/O performance"
    echo "  • Reduced write amplification"
    echo "  • Optimized garbage collection"
    
    echo
    echo "⚠️  Recommendations:"
    echo "  • Monitor SSD health regularly"
    echo "  • Keep 10-20% free space for optimal performance"
    echo "  • Run performance tests after optimization"
    echo "  • Check TRIM is working: 'systemctl status fstrim.timer'"
    
    echo
    print_success "SSD optimization completed successfully!"
    
    echo
    echo "🔄 Next Steps:"
    echo "  1. Restart your Pi to ensure all optimizations take effect"
    echo "  2. Run: ipfs-tools ssd-health"
    echo "  3. Run: ipfs-tools status"
    echo "  4. Test performance: /opt/ipfs-tools/ssd_performance_test.sh"
}

# Main execution
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

show_banner
check_prerequisites
detect_ssd_info

echo "This script will optimize your SSD for IPFS usage."
echo "The following optimizations will be applied:"
echo "  • Filesystem mount options"
echo "  • I/O scheduler"
echo "  • Kernel parameters"  
echo "  • TRIM automation"
echo "  • IPFS configuration"
echo "  • Logging optimization"
echo

read -p "Continue with SSD optimization? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_info "Optimization cancelled"
    exit 0
fi

optimize_filesystem_mount
optimize_io_scheduler
optimize_kernel_parameters
setup_trim_automation
optimize_ipfs_config
setup_log_optimization
create_monitoring_script
create_performance_test

show_optimization_summary