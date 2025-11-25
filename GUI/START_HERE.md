# 🚀 START HERE - IPFS Backup Tool

## Quick Start (Choose Your Platform)

### 🪟 Windows Users

**Best Option (No Console, No Warnings):**
→ Double-click: **`IPFS_Backup_Tool.vbs`** ⭐ RECOMMENDED

**Alternative (No Console, Small Warning First Time):**
→ Double-click: **`ipfs_backup_gui.pyw`**

**Old Method (Has Console Window):**
→ Double-click: **`start_backup_tool.bat`**

### 🍎 Mac / 🐧 Linux Users

→ Run: **`./start_backup_tool.sh`**

Or directly: **`python3 ipfs_backup_gui.py`**

---

## 📁 File Structure

```
your-folder/
├── 🎯 IPFS_Backup_Tool.vbs    ← Windows: USE THIS!
├── ipfs_backup_gui.py          ← The main application
├── ipfs_backup_gui.pyw         ← Windows alternative
├── start_backup_tool.bat       ← Windows (old method)
├── start_backup_tool.sh        ← Mac/Linux launcher
└── csv_files/                  ← Put your CSV files here
    └── (your CSV files)
```

---

## 🎯 Which File to Use?

| Your Situation | Use This File |
|----------------|---------------|
| Windows, want no console & no warnings | **IPFS_Backup_Tool.vbs** ⭐ |
| Windows, don't mind one-time warning | **ipfs_backup_gui.pyw** |
| Mac or Linux | **start_backup_tool.sh** |
| Have Python, run directly | **ipfs_backup_gui.py** |

---

## 📋 First Time Setup

1. **Install Python** (if not already installed)
   - Windows: https://www.python.org/downloads/
   - Check "Add Python to PATH" during installation

2. **Place your CSV files** in the `csv_files` folder

3. **Run the application** using one of the files above

4. **Done!** The app will:
   - Check if IPFS is running (and help you start it)
   - Show your CSV files with checkboxes
   - Let you download with progress tracking

---

## 💡 Why Multiple Launchers?

Different users have different needs:

**VBS (IPFS_Backup_Tool.vbs):**
- Clean, professional experience
- No black console window
- No security warnings
- ⭐ Best for end users

**.pyw file:**
- Simple Python script
- No console window
- Small security warning first time
- Good for Python users

**.bat file:**
- Shows console (useful for debugging)
- Good for developers
- Shows error messages clearly

**.sh file:**
- For Mac/Linux users
- Standard Unix launcher

---

## 🆘 Troubleshooting

**"Python is not installed"**
→ Install Python from https://www.python.org/

**"IPFS Not Running"**
→ The app will detect this and offer to download/start IPFS

**Console window appears**
→ Use the VBS file instead of BAT file

**"Publisher not verified" warning**
→ Use the VBS file (no warning!) or click "More info" → "Run anyway"

---

## 📚 Need More Info?

- **WINDOWS_DEPLOYMENT.md** - Complete Windows deployment guide
- **README_GUI.md** - Feature overview and quick start
- **IPFS_GUIDE.md** - IPFS setup and troubleshooting
- **TESTING.md** - Test procedures
- **COMPLETE_PACKAGE.md** - Everything about the tool

---

## 🎉 Ready to Go!

**Windows:** Double-click `IPFS_Backup_Tool.vbs` → Enjoy! 🚀

**Mac/Linux:** Run `./start_backup_tool.sh` → Enjoy! 🚀
