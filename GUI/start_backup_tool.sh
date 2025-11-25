#!/bin/bash

echo "Starting IPFS Backup Tool..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3 from https://www.python.org/"
    exit 1
fi

# Check if requests is installed
python3 -c "import requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required package: requests"
    pip3 install requests
    echo ""
fi

# Create csv_files folder if it doesn't exist
if [ ! -d "csv_files" ]; then
    echo "Creating csv_files folder..."
    mkdir csv_files
    echo ""
fi

# Run the GUI
python3 ipfs_backup_gui.py
