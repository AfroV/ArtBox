#!/bin/bash

# Unified NFT System Installer v4.1 (Fixed Launcher Edition)
# This script installs the application and ensures the launcher appears on desktop.

set -e

# --- Configuration ---
if [ -n "$SUDO_USER" ]; then
    ACTUAL_USER="$SUDO_USER"
    ACTUAL_HOME=$(eval echo ~$SUDO_USER)
else
    echo "ERROR: This script must be run with sudo."
    exit 1
fi

DEST_DIR="$ACTUAL_HOME/nft-system"
CONFIG_DIR="$ACTUAL_HOME/.nft-system"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== NFT System Installer v4.1 ==="
echo "User: $ACTUAL_USER"
echo "Home: $ACTUAL_HOME"
echo "Installation directory: $DEST_DIR"
echo "Source directory: $SOURCE_DIR"
echo

# --- Pre-flight Checks ---
echo "--- Running Pre-flight Checks ---"
if [[ "$SOURCE_DIR" == "$DEST_DIR" ]]; then
    echo -e "\n\033[0;31m[ERROR] Do not run the installer from its destination directory.\033[0m"
    exit 1
fi
echo "✅ Check 1/3: Running from a safe location."

if ! [ -f "$SOURCE_DIR/main_app.py" ] || ! [ -f "$SOURCE_DIR/launcher.py" ]; then
    echo -e "\n\033[0;31m[ERROR] Missing application files (main_app.py or launcher.py).\033[0m"
    exit 1
fi
echo "✅ Check 2/3: Required application files found."

# Check if we're running on a system with GUI support
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    echo "⚠️  Warning: No display detected. GUI may not work properly."
else
    echo "✅ Check 3/3: Display environment detected."
fi
echo "---------------------------------"
sleep 2

# --- Main Installation ---
echo -e "\nStarting installation..."

# Clean up any previous installations
echo "1. Cleaning up previous installations..."
sudo rm -rf "$DEST_DIR" "$CONFIG_DIR"
sudo rm -f "$ACTUAL_HOME/Desktop/"*.desktop 2>/dev/null || true

echo "2. Creating application directories..."
mkdir -p "$DEST_DIR"
mkdir -p "$CONFIG_DIR"

echo "3. Copying application files..."
cp -r "$SOURCE_DIR/"* "$DEST_DIR/"

echo "4. Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv python3-tk git curl ufw pcmanfm wayfire wofi foot

echo "5. Setting file ownership..."
chown -R "$ACTUAL_USER:$ACTUAL_USER" "$DEST_DIR"
chown -R "$ACTUAL_USER:$ACTUAL_USER" "$CONFIG_DIR"

echo "6. Setting up Python environment..."
sudo -u "$ACTUAL_USER" bash -c "cd '$DEST_DIR' && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

echo "7. Creating application run script..."
cat > "$DEST_DIR/run_app.sh" << 'RUN_APP_EOF'
#!/bin/bash
# This script activates the virtual environment and runs the main application.
cd "$(dirname "$0")"
source venv/bin/activate
python3 main_app.py
RUN_APP_EOF
chmod +x "$DEST_DIR/run_app.sh"
chown "$ACTUAL_USER:$ACTUAL_USER" "$DEST_DIR/run_app.sh"

echo "8. Creating launcher startup script..."
cat > "$DEST_DIR/start_launcher.sh" << 'LAUNCHER_EOF'
#!/bin/bash
# Start the NFT System Launcher
cd "$(dirname "$0")"
export DISPLAY=${DISPLAY:-:0}
python3 launcher.py
LAUNCHER_EOF
chmod +x "$DEST_DIR/start_launcher.sh"
chown "$ACTUAL_USER:$ACTUAL_USER" "$DEST_DIR/start_launcher.sh"

echo "9. Configuring Wayfire desktop environment..."
sudo -u $ACTUAL_USER mkdir -p "$ACTUAL_HOME/.config/wayfire"
cat > "$ACTUAL_HOME/.config/wayfire/wayfire.ini" << WAYFIRE_CONFIG_EOF
[core]
plugins = core decoration command autostart
xwayland = true

[autostart]
background = swaybg -i /usr/share/pixmaps/raspberry-pi-logo.png -m fill
terminal = foot --server
# Start NFT Launcher after a short delay
launcher = bash -c "sleep 3 && $DEST_DIR/start_launcher.sh"

[command]
binding_launcher = <super> KEY_D
command_launcher = wofi --show drun
binding_terminal = <super> KEY_ENTER
command_terminal = foot
binding_nft = <super> KEY_N
command_nft = $DEST_DIR/start_launcher.sh
WAYFIRE_CONFIG_EOF
chown $ACTUAL_USER:$ACTUAL_USER "$ACTUAL_HOME/.config/wayfire/wayfire.ini"

echo "10. Creating desktop application entry..."
sudo -u $ACTUAL_USER mkdir -p "$ACTUAL_HOME/.local/share/applications"
cat > "$ACTUAL_HOME/.local/share/applications/nft-system.desktop" << DESKTOP_EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=NFT System
Comment=Unified NFT Management System
Exec=$DEST_DIR/run_app.sh
Icon=system-software-install
Terminal=false
Categories=Graphics;Network;
StartupNotify=true
DESKTOP_EOF
chown $ACTUAL_USER:$ACTUAL_USER "$ACTUAL_HOME/.local/share/applications/nft-system.desktop"

echo "11. Creating launcher desktop entry..."
cat > "$ACTUAL_HOME/.local/share/applications/nft-launcher.desktop" << LAUNCHER_DESKTOP_EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=NFT Launcher
Comment=NFT System Launcher Panel
Exec=$DEST_DIR/start_launcher.sh
Icon=applications-accessories
Terminal=false
Categories=Utility;
StartupNotify=true
LAUNCHER_DESKTOP_EOF
chown $ACTUAL_USER:$ACTUAL_USER "$ACTUAL_HOME/.local/share/applications/nft-launcher.desktop"

echo "12. Setting up manual launcher for immediate testing..."
# Create a desktop shortcut that user can double-click
sudo -u $ACTUAL_USER mkdir -p "$ACTUAL_HOME/Desktop"
cat > "$ACTUAL_HOME/Desktop/NFT-Launcher.desktop" << MANUAL_LAUNCHER_EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=NFT System Launcher
Comment=Click to start NFT System Launcher
Exec=$DEST_DIR/start_launcher.sh
Icon=applications-accessories
Terminal=false
Categories=Utility;
StartupNotify=true
MANUAL_LAUNCHER_EOF
chmod +x "$ACTUAL_HOME/Desktop/NFT-Launcher.desktop"
chown $ACTUAL_USER:$ACTUAL_USER "$ACTUAL_HOME/Desktop/NFT-Launcher.desktop"

echo "13. Testing launcher (optional)..."
if [ "$1" != "--no-test" ]; then
    echo "Starting launcher for 5-second test..."
    sudo -u $ACTUAL_USER DISPLAY=:0 timeout 5s "$DEST_DIR/start_launcher.sh" || echo "Test completed (timeout expected)"
fi

# --- Final Instructions ---
echo
echo "🎉🎉🎉 Installation Complete! 🎉🎉🎉"
echo "================================================"
echo "MULTIPLE WAYS TO START THE LAUNCHER:"
echo
echo "1. AUTOMATIC (after reboot):"
echo "   The launcher will appear automatically when you log in"
echo
echo "2. MANUAL (right now):"
echo "   Double-click 'NFT-Launcher' icon on your Desktop"
echo
echo "3. KEYBOARD SHORTCUT:"
echo "   Press Super+N (Windows key + N)"
echo
echo "4. COMMAND LINE:"
echo "   $DEST_DIR/start_launcher.sh"
echo
echo "5. APPLICATION MENU:"
echo "   Press Super+D and search for 'NFT Launcher'"
echo "================================================"
echo
echo "NEXT STEPS:"
echo "• REBOOT for automatic startup, OR"
echo "• Double-click the Desktop icon to test now"
echo "================================================"

# Ask user if they want to reboot or test now
echo
read -p "Do you want to (R)eboot now, (T)est launcher now, or (S)kip? [R/T/S]: " -n 1 -r
echo
case $REPLY in
    [Rr]* ) 
        echo "Rebooting..."
        sleep 2
        sudo reboot
        ;;
    [Tt]* ) 
        echo "Starting launcher for testing..."
        echo "The launcher should appear in a few seconds..."
        sudo -u $ACTUAL_USER DISPLAY=:0 "$DEST_DIR/start_launcher.sh" &
        echo "Launcher started in background. Check your desktop!"
        ;;
    * ) 
        echo "Installation complete. You can start the launcher manually."
        ;;
esac