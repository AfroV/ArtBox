# IPFS Backup Tool - GUI Version

## 🎯 Quick Start

1. **Make sure IPFS is running** (the app will help you with this!)
2. **Place your CSV files** in a folder called `csv_files` (next to the script)
3. **Run the application**: `python ipfs_backup_gui.py`
4. **Select which CSV files** you want to download (checkboxes)
5. **Click "Start Download"** and wait!

## ✨ New Features (v1.2)

### 🔍 Automatic IPFS Detection
The app now **automatically checks** if IPFS is running when you:
- Launch the application
- Click "Check IPFS" button
- Try to start a download

### 🚀 Smart IPFS Management
If IPFS is not running, the app will:

**1. If IPFS is not installed:**
- Detect that IPFS is missing
- Offer to open the download page
- Guide you to install IPFS Desktop or CLI

**2. If IPFS is installed but not running:**
- Detect that the daemon is stopped
- Offer to **start it automatically** with one click
- Or provide instructions to start it manually

**3. If IPFS is running:**
- Show ✅ green status indicator
- Allow downloads to proceed normally

### 🎮 Easy Controls
- **🔄 Check IPFS** button - manually verify IPFS status
- Status indicator shows real-time IPFS daemon status
- Automatic startup dialog if daemon is not running

## 📋 All Features

- ✅ **Automatic IPFS detection** - knows if daemon is running
- ✅ **One-click IPFS startup** - start daemon from the app
- ✅ **Easy checkbox selection** - pick which CSV files to process
- 📊 **Real-time progress bar** - see exactly how far along you are
- 🔄 **Resume capability** - if interrupted, just run again to continue
- 🛑 **Graceful stop** - stop anytime and resume later
- 🚀 **Parallel downloads** - adjust workers for faster downloads (1-8)
- 📁 **Auto file detection** - automatically finds all CSV files in the folder

## 🖥️ How It Works

### CSV Folder
By default, the app looks for CSV files in a `csv_files` subfolder. You can:
- Click **"Change Folder"** to select a different location
- Click **"Refresh"** to rescan for new CSV files

### File Selection
- Each CSV file shows:
  - Filename
  - Number of items
  - File size
- Use **"Select All"** or **"Select None"** for quick selection
- Or manually check/uncheck individual files

### Workers
- **1 worker** (default): Slower but more reliable
- **2-4 workers**: Good balance for most cases
- **5-8 workers**: Faster but may timeout on slow IPFS nodes

### Progress
The app shows:
- Progress bar with percentage
- Items completed / total items
- Items remaining

### Output
Downloaded files are saved to: `ipfs_backup/files/`
Progress is saved to: `ipfs_backup/download_progress.json`

## 🔧 Requirements

```bash
pip install requests
```

That's it! tkinter comes with Python by default.

## 📦 Creating a Standalone Executable (Optional)

To make a double-click application without Python:

### Windows:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "IPFS Backup" ipfs_backup_gui.py
```

### macOS:
```bash
pip install py2app
python setup.py py2app
```

### Linux:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed ipfs_backup_gui.py
```

The executable will be in the `dist/` folder!

## 🚨 Troubleshooting

**"IPFS Not Running"**
- The app will automatically detect this and offer to start IPFS
- Click "Yes" to start the daemon automatically
- Or start manually: open terminal and run `ipfs daemon`

**"IPFS Not Installed"**
- The app will detect this and offer to open the download page
- Install IPFS Desktop (recommended): Easy GUI app
- Or install IPFS CLI: For command-line use
- After installing, restart the backup tool

**IPFS Status Not Updating**
- Click the "🔄 Check IPFS" button to manually refresh
- Make sure IPFS daemon is running (check http://127.0.0.1:8080)

**"No CSV files found"**
- Make sure your CSV files are in the correct folder
- Click "Change Folder" to select the right location

**Download times out**
- Some IPFS files can be very slow
- The app retries for ~13 minutes per file
- Reduce workers to 1 for better reliability

## 💡 IPFS Tips

**First Time Setup:**
1. Install IPFS Desktop from https://docs.ipfs.tech/install/ipfs-desktop/
2. Or install IPFS CLI from https://docs.ipfs.tech/install/command-line/
3. Start IPFS daemon (Desktop app does this automatically)
4. Run the backup tool - it will verify IPFS is ready!

**Checking IPFS Manually:**
- Open http://127.0.0.1:8080/ipfs/bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi
- If you see content, IPFS is running correctly!

**Starting IPFS Manually:**
- **IPFS Desktop**: Just open the app
- **IPFS CLI**: Run `ipfs daemon` in terminal

## 💡 Tips

1. **Start small**: Test with one CSV file first
2. **Be patient**: IPFS can be slow, especially for large collections
3. **Check progress file**: If interrupted, your progress is saved automatically
4. **Nested files**: JSON and HTML files are scanned for embedded IPFS links

## 📝 CSV File Format

Your CSV file should have one of these column names:
- `cid` or `CID` - Direct IPFS CID
- `metadata_url` or `metadataUrl` - URL containing IPFS CID

Example:
```csv
name,cid
My NFT 1,QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG
My NFT 2,bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi
```

Or:
```csv
title,metadata_url
Art Piece,https://ipfs.io/ipfs/QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG
```
