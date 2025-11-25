#!/bin/bash
# IPFS Backup Tool Launcher for macOS
# Double-click this file to run the application

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    osascript -e 'display dialog "Python 3 is not installed.\n\nPlease install Python 3 from https://www.python.org/downloads/" buttons {"OK"} default button "OK" with icon stop'
    exit 1
fi

# Check and install required packages
echo "Checking dependencies..."
python3 -m pip install --quiet --upgrade pip
python3 -m pip install --quiet requests

# Run the GUI application
echo "Starting IPFS Backup Tool..."
python3 ipfs_backup_gui.pyw

# Keep terminal open if there was an error
if [ $? -ne 0 ]; then
    echo ""
    echo "Press Enter to close..."
    read
fi
