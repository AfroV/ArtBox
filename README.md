## 🚀 **Installation Process**

### **Step 1: Install PI OS**

# https://www.raspberrypi.com/software/

Set up the installer
-PI 4
-Raspberry PI OS 64 bit
-Your SSD for storage.

#Set username and password. Do remerber this for you will need it later to #ssh into your PI

configer Wireless LAN to use your home network. If not you will need to use a LAN cable.

Under the SERVICES tab.
Enable SSH
Us with password or public key

```bash
# Copy all files to your Pi. E.G punk@1.4.2.0
scp -r nft_setup pi@your-pi-ip:~/

# Or use USB drive, etc.
```

### **Step 2: Installation**

````bash
# SSH into your Pi
ssh pi@your-pi-ip

cd nft_setup

chmod +x *.sh *.py


```bash
# Main installation (installs everything)
sudo ./ipfs_setup.sh
````

# The script will automatically:

- Install IPFS and all dependencies
- Create the IPFS service
- Set up the directory structure
- Copy any available management scripts
- Run an initial status check
- Start the IPFS service

### **Step 3: Test Everything**

```bash
# Check status
ipfs-tools status

# Check SSD health
ipfs-tools ssd-health

# Test NFT download
sudo ipfs-tools download 0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb 1

# Create and test CSV
echo "contract_address,token_id
0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb,1" > test.csv
sudo ipfs-tools csv test.csv
```

---

## 🛠️ **What Gets Installed**

### **IPFS Node**

- ✅ IPFS Kubo (latest version)
- ✅ Systemd service (auto-start on boot)
- ✅ Optimized configuration for SSD
- ✅ Web UI accessible at `http://pi-ip:5001/webui/`

### **NFT Management**

- ✅ Single NFT download
- ✅ CSV batch processing
- ✅ Automatic IPFS pinning
- ✅ Metadata and image storage
- ✅ Easy cleanup tools

### **SSD Optimizations**

- ✅ Mount options (noatime, discard)
- ✅ I/O scheduler optimization
- ✅ Kernel parameter tuning
- ✅ Automatic TRIM setup
- ✅ Write reduction features

### **Health Monitoring**

- ✅ Real-time status checking
- ✅ SSD health monitoring
- ✅ Performance metrics
- ✅ Alert system
- ✅ Continuous monitoring mode

### **Backup System**

- ✅ Full IPFS data backup
- ✅ NFT collection backup
- ✅ Configuration backup
- ✅ Automated restore
- ✅ Scheduled cleanup

---

## 📊 **Directory Structure After Installation**

```
/mnt/ssd/
├── ipfs/              # IPFS node data
├── nft_data/          # Downloaded NFT files
│   ├── contract_token_metadata.json
│   ├── contract_token_image.png
│   └── contract_token_summary.json
└── backups/           # Automated backups

/opt/ipfs-tools/       # Management scripts and tools
├── venv/              # Python environment
├── nft_downloader.py
├── ipfs_health_monitor.py
├── ssd_optimization.sh
├── ipfs_backup_restore.sh
└── other management tools

/usr/local/bin/
└── ipfs-tools         # Main command interface
```

---

## ⚡ **Daily Usage Commands**

### **Status & Monitoring**

```bash
ipfs-tools status              # Check everything
ipfs-tools monitor 60          # Continuous monitoring
ipfs-tools alerts              # Check for problems
```

### **NFT Management**

```bash
ipfs-tools download <contract> <token_id>    # Single NFT
sudo ipfs-tools csv nfts.csv                      # Batch process
ipfs-tools cleanup --list                    # List stored NFTs
ipfs-tools cleanup --cleanup <contract> <id> # Remove NFT
```

### **Backup & Maintenance**

```bash
sudo ipfs-tools backup backup        # Create backup
ipfs-tools backup list               # List backups
sudo fstrim -v /mnt/ssd             # Manual TRIM
```

### **Service Management**

```bash
sudo systemctl status ipfs          # Check service
sudo systemctl restart ipfs         # Restart if needed
sudo journalctl -u ipfs -f          # View logs
```

---

## 🔧 **Troubleshooting**

### **If IPFS Won't Start**

```bash
# Check logs
sudo journalctl -u ipfs -f

# Restart service
sudo systemctl restart ipfs

# Re-run verification
sudo ./setup_verification.sh
```

### **If NFT Downloads Fail**

```bash
# Check IPFS status
ipfs-tools status

# Try different RPC endpoint
ipfs-tools download <contract> <token> --rpc-url https://mainnet.infura.io/v3/YOUR-KEY
```

### **If SSD Performance is Poor**

```bash
# Re-run optimization
sudo ./ssd_optimization.sh


# Run performance test
sudo /opt/ipfs-tools/ssd_performance_test.sh
```

---

## 🎉 **Success Indicators**

When everything is working correctly, you should see:

✅ **IPFS Service**: `systemctl status ipfs` shows "active (running)"  
✅ **Web UI**: Accessible at `http://your-pi-ip:5001/webui/`  
✅ **API**: `curl http://127.0.0.1:5001/api/v0/version` returns JSON  
✅ **SSD Health**: `ipfs-tools` shows optimizations  
✅ **NFT Downloads**: Successfully downloads and pins NFTs  
✅ **Peers**: Connected to IPFS network with multiple peers

## If links does not work, you might need to SSH tunel

##SSH Tunnel (Recommended):

Option 1: Local Port Forwarding

Forward your local port 5001 to Pi's port 5001

```bash
ssh -L 5001:localhost:5001 pi@your-pi-ip
```

Keep the SSH connection open, then access:
http://localhost:5001/webui/

Option 2: Use Different Local Port (if 5001 is busy)
Forward local port 15001 to Pi's port 5001

```bash
ssh -L 15001:localhost:5001 pi@your-pi-ip
```

Then access: http://localhost:15001/webui/

---

## 🏆 **Final Result**

You'll have a **IPFS node** with:

- 🔥 **High Performance**: SSD-optimized for IPFS workloads
- 🛡️ **Reliable**: Auto-restart, health monitoring, backups
- 🎨 **NFT Ready**: Download, pin, and manage NFT collections
- 🔧 **Maintainable**: Easy management tools and commands
- 💾 **Protected**: Comprehensive backup and restore system

## ⚠️ Important Safety Notice

This is an experimental DIY project shared for educational purposes. By building this device:

- You assume all risks of assembly and operation
- You are responsible for electrical safety and local regulations
- No warranty or support is provided
- Creator is not liable for any damage, injury, or loss

**Build at your own risk. If you're not comfortable with electronics, please consult someone who is.**
