#!/bin/bash

# NFT System Updater v2.0
# This script updates an old installation to the new unified application.

set -e

# --- Configuration ---
ACTUAL_USER="${SUDO_USER:-$USER}"
ACTUAL_HOME=$(eval echo ~$ACTUAL_USER)
BACKUP_DIR="$ACTUAL_HOME/nft-system-backup-$(date +%F)"

echo "Starting update to the new Unified NFT System..."

# 1. Backup existing data
echo "Backing up your existing data to: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Backup old API keys and config (if they exist)
if [ -d "$ACTUAL_HOME/.nft-artbox" ]; then
    cp -r "$ACTUAL_HOME/.nft-artbox" "$BACKUP_DIR/nft-artbox-config-backup"
fi

# Backup old database
if [ -f "$ACTUAL_HOME/ipfs-artbox/cache.db" ]; then
    cp "$ACTUAL_HOME/ipfs-artbox/cache.db" "$BACKUP_DIR/cache.db.backup"
fi

echo "Backup complete."

# 2. Remove old application files and shortcuts
echo "Removing old application files and shortcuts..."
rm -rf "$ACTUAL_HOME/ipfs-artbox"
rm -rf "$ACTUAL_HOME/nft-viewer"
rm -rf "$ACTUAL_HOME/.nft-artbox"
rm -f "$ACTUAL_HOME/Desktop/"*.desktop

echo "Old files removed."

# 3. Run the new installer from the current directory
echo "Running the new installer..."
if [ -f "./install.sh" ]; then
    sudo bash ./install.sh
else
    echo "ERROR: New 'install.sh' not found in the current directory."
    exit 1
fi

# 4. Restore the database
echo "Restoring NFT database..."
if [ -f "$BACKUP_DIR/cache.db.backup" ]; then
    # The new database is at ~/.nft-system/nft_cache.db
    NEW_DB_PATH="$ACTUAL_HOME/.nft-system/nft_cache.db"
    cp "$BACKUP_DIR/cache.db.backup" "$NEW_DB_PATH"
    chown $ACTUAL_USER:$ACTUAL_USER "$NEW_DB_PATH"
    echo "Database restored."
else
    echo "No database backup found to restore."
fi

# 5. Final Instructions
echo ""
echo "🎉 Update Complete!"
echo "--------------------------------------------------------"
echo "IMPORTANT FINAL STEP:"
echo "1. Open the new 'Unified NFT System' application from your Desktop."
echo "2. Go to the '⚙️ Settings' tab."
echo "3. Re-enter your API keys from your notes or old backup."
echo "   (Your old encoded keys are in $BACKUP_DIR/nft-artbox-config-backup)"
echo "--------------------------------------------------------"