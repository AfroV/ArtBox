#SSD Health Monitor for IPFS
#Monitors SSD health, temperature, and wear indicators

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
                    'device': parts[0],
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

def get_ssd_temperature(device):
    """Get SSD temperature if available"""
    try:
        result = subprocess.run(['smartctl', '-A', device], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'Temperature' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.isdigit() and int(part) > 20 and int(part) < 100:
                            return f"{part}°C"
    except:
        pass
    return "Not available"

def main():
    # Auto-detect SSD device from IPFS data directory
    ipfs_data_path = "/opt/ipfs-data"
    
    try:
        # Get device from IPFS data directory
        result = subprocess.run(['df', ipfs_data_path], capture_output=True, text=True)
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
    print(f"IPFS Data: {ipfs_data_path}")
    print()
    
    # Disk usage
    usage = get_disk_usage(ipfs_data_path)
    if usage:
        print(f"💾 Disk Usage:")
        print(f"  Device: {usage['device']}")
        print(f"  Total: {usage['total']}")
        print(f"  Used: {usage['used']} ({usage['use_percent']})")
        print(f"  Available: {usage['available']}")
        
        # Warn if disk is getting full
        used_percent = int(usage['use_percent'].rstrip('%'))
        if used_percent > 90:
            print(f"  ⚠️  WARNING: Disk is {used_percent}% full!")
        elif used_percent > 80:
            print(f"  ⚠️  CAUTION: Disk is {used_percent}% full")
    
    print()
    
    # SSD Type Detection
    try:
        device_name = os.path.basename(ssd_device)
        with open(f'/sys/block/{device_name}/queue/rotational', 'r') as f:
            rotational = f.read().strip()
            if rotational == "0":
                print("💾 Storage Type: ✅ SSD (Non-rotational)")
            else:
                print("💾 Storage Type: ⚠️  HDD (Rotational)")
    except:
        print("💾 Storage Type: Could not determine")
    
    # TRIM support
    trim_supported = check_trim_support(ssd_device)
    print(f"✂️  TRIM Support: {'✅ Yes' if trim_supported else '❌ No'}")
    
    # Temperature
    temp = get_ssd_temperature(ssd_device)
    print(f"🌡️  Temperature: {temp}")
    
    print()
    
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
            233: "Media Wearout Indicator",
            194: "Temperature"
        }
        
        found_attrs = False
        for attr in attrs:
            attr_id = attr['id']
            if attr_id in key_attrs:
                name = key_attrs[attr_id]
                value = attr['raw']['value']
                normalized = attr.get('value', 'N/A')
                
                # Special formatting for certain attributes
                if attr_id == 9:  # Power-On Hours
                    hours = int(value)
                    days = hours // 24
                    print(f"  {name}: {value} hours ({days} days)")
                elif attr_id == 194:  # Temperature
                    print(f"  {name}: {value}°C")
                elif attr_id in [231, 233]:  # Life indicators
                    print(f"  {name}: {normalized}% (raw: {value})")
                else:
                    print(f"  {name}: {value}")
                found_attrs = True
        
        if not found_attrs:
            print("  No key SSD health attributes found")
            print("  (This is normal for some SSD models)")
    else:
        print("🏥 SMART Health: Not available")
        print("  (May need sudo or smartmontools not installed)")
    
    print()
    print("📈 Optimization Status:")
    
    # Check I/O scheduler
    try:
        device_name = os.path.basename(ssd_device)
        with open(f'/sys/block/{device_name}/queue/scheduler', 'r') as f:
            scheduler = f.read().strip()
            current = scheduler[scheduler.find('[')+1:scheduler.find(']')]
            if current in ['none', 'noop']:
                print(f"  I/O Scheduler: ✅ {current} (optimal for SSD)")
            else:
                print(f"  I/O Scheduler: ⚠️  {current} (consider 'none' for SSD)")
    except:
        print("  I/O Scheduler: Could not determine")
    
    # Check mount options
    try:
        with open('/proc/mounts', 'r') as f:
            for line in f:
                if ipfs_data_path in line or (ipfs_data_path == "/opt/ipfs-data" and " / " in line):
                    parts = line.split()
                    if len(parts) > 3:
                        options = parts[3]
                        has_noatime = 'noatime' in options
                        has_discard = 'discard' in options
                        print(f"  noatime: {'✅' if has_noatime else '❌'} (reduces writes)")
                        print(f"  discard: {'✅' if has_discard else '❌'} (enables TRIM)")
                    break
    except:
        print("  Mount options: Could not determine")
    
    # Check TRIM timer
    try:
        result = subprocess.run(['systemctl', 'is-enabled', 'fstrim.timer'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("  TRIM Timer: ✅ Enabled")
        else:
            print("  TRIM Timer: ❌ Not enabled")
    except:
        print("  TRIM Timer: Could not check")
    
    print()
    print("💡 Recommendations:")
    
    if usage and int(usage['use_percent'].rstrip('%')) > 85:
        print("  • Free up disk space (keep <85% for optimal SSD performance)")
    
    if not trim_supported:
        print("  • Enable TRIM support for SSD longevity")
    
    try:
        device_name = os.path.basename(ssd_device)
        with open(f'/sys/block/{device_name}/queue/scheduler', 'r') as f:
            scheduler = f.read().strip()
            current = scheduler[scheduler.find('[')+1:scheduler.find(']')]
            if current not in ['none', 'noop']:
                print(f"  • Consider changing I/O scheduler to 'none' for better SSD performance")
    except:
        pass
    
    print("  • Run 'sudo /opt/ipfs-tools/ssd_optimization.sh' for full SSD optimization")
    print("  • Monitor SSD health regularly with this command")

if __name__ == "__main__":
    main()
