# macOS Setup Instructions

## Quick Start (Recommended)

### Option 1: Using .command file (Easiest)

1. Open Terminal (you only need to do this once)
2. Navigate to the folder containing `run_ipfs_backup.command`:
   ```bash
   cd /path/to/ipfsdw
   ```
3. Make the file executable:
   ```bash
   chmod +x run_ipfs_backup.command
   ```
4. **Double-click** `run_ipfs_backup.command` to run the app!

The `.command` file will automatically:
- Check for Python 3
- Install required dependencies
- Launch the IPFS Backup Tool GUI

---

## Alternative Methods

### Option 2: Create a Desktop Application

Create a proper macOS `.app` bundle that appears in your Applications folder:

1. Open **Automator** (found in Applications/Utilities)
2. Choose **"New Document"** → **"Application"**
3. In the left sidebar, find **"Run Shell Script"** and drag it to the right panel
4. Replace the default text with:
   ```bash
   cd /path/to/ipfsdw
   /usr/bin/python3 ipfs_backup_gui.pyw
   ```
   (Replace `/path/to/ipfsdw` with the actual path)
5. Save as "IPFS Backup Tool" to your Applications folder or Desktop
6. **Double-click** the app to run!

Optional: Add a custom icon:
- Find an IPFS icon image
- Right-click the app → Get Info
- Drag the icon onto the small icon in the top-left of the Info window

### Option 3: Using the .sh file

If you prefer the `.sh` file:

1. Make it executable (one-time setup):
   ```bash
   chmod +x run_ipfs_backup.sh
   ```

2. Run it from Terminal:
   ```bash
   ./run_ipfs_backup.sh
   ```

Or create an alias in your `.zshrc` or `.bash_profile`:
```bash
alias ipfs-backup='cd /path/to/ipfsdw && ./run_ipfs_backup.sh'
```

Then just type `ipfs-backup` in Terminal!

---

## Troubleshooting

### "Permission Denied" Error
Run this in Terminal:
```bash
chmod +x run_ipfs_backup.command
```

### "Python 3 not found"
Install Python 3 from [python.org](https://www.python.org/downloads/)

### Security Warning "Cannot open because it is from an unidentified developer"
1. Right-click the file
2. Select "Open"
3. Click "Open" in the dialog
4. After the first time, double-clicking will work normally

---

## What's the difference?

- **`.command`** - Opens in Terminal, shows progress, easiest to debug
- **`.app` (Automator)** - Native macOS app, can add to Dock, looks professional
- **`.sh`** - Traditional Unix shell script, requires Terminal

We recommend starting with the `.command` file!
