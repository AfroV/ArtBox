@echo off
echo Creating Desktop Shortcut for IPFS Backup Tool...
echo.

REM Get current directory
set SCRIPT_DIR=%~dp0

REM Create VBScript to make shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%USERPROFILE%\Desktop\IPFS Backup Tool.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%SCRIPT_DIR%IPFS_Backup_Tool.vbs" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> CreateShortcut.vbs
echo oLink.Description = "IPFS NFT Backup Tool" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

REM Execute the VBScript
cscript CreateShortcut.vbs >nul

REM Clean up
del CreateShortcut.vbs

echo.
echo ✓ Desktop shortcut created successfully!
echo.
echo You can now run "IPFS Backup Tool" from your desktop.
echo.
pause
