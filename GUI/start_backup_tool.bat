@echo off
REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    msg * "Python is not installed. Please install Python from https://www.python.org/"
    exit /b 1
)

REM Check if requests is installed
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo Installing required package: requests...
    pip install requests >nul 2>&1
)

REM Create csv_files folder if it doesn't exist
if not exist "csv_files" mkdir csv_files

REM Run the GUI with pythonw (no console window)
start "" pythonw ipfs_backup_gui.py
