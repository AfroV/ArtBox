#!/bin/bash

# Pi NFT Tools Complete Update Script
# This script updates ALL install files on the Pi with new versions
# Usage: sudo ./update_pi_tools.sh

set -e

# Configuration
SCRIPT_DIR="/opt/ipfs-tools"
BACKUP_DIR="/opt/ipfs-tools/backups"
INSTALL_DIR="/opt/ipfs-install"
SOURCE_DIR="$(pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

print_header "Pi NFT Tools Complete Update Script"
print_status "Source directory: $SOURCE_DIR"
print_status "Tool scripts target: $SCRIPT_DIR"
print_status "Install scripts target: $INSTALL_DIR"
print_status "Timestamp: $TIMESTAMP"

# Create directories if they don't exist
mkdir -p "$BACKUP_DIR"
mkdir -p "$INSTALL_DIR"

# Function to backup and update a file
update_file() {
    local filename="$1"
    local description="$2"
    local target_dir="$3"
    local source_file="$SOURCE_DIR/$filename"
    local target_file="$target_dir/$filename"
    local backup_file="$BACKUP_DIR/${filename}_backup_${TIMESTAMP}"
    
    print_status "Updating: $description"
    
    # Check if source file exists
    if [ ! -f "$source_file" ]; then
        print_warning "Source file not found: $source_file"
        return 1
    fi
    
    # Backup existing file if it exists
    if [ -f "$target_file" ]; then
        print_status "  Backing up existing file to: $backup_file"
        cp "$target_file" "$backup_file"
    fi
    
    # Copy new file
    print_status "  Copying: $source_file -> $target_file"
    cp "$source_file" "$target_file"
    
    # Set permissions
    chmod +x "$target_file"
    
    # Set ownership based on target directory
    if [ "$target_dir" = "$SCRIPT_DIR" ]; then
        chown ipfs:ipfs "$target_file"
    else
        chown root:root "$target_file"
    fi
    
    print_status "  ✅ $description updated successfully"
    return 0
}

# Function to validate Python file
validate_python_file() {
    local filename="$1"
    local target_dir="$2"
    local filepath="$target_dir/$filename"
    
    if [ -f "$filepath" ]; then
        # Check if it's valid Python syntax
        if python3 -m py_compile "$filepath" 2>/dev/null; then
            print_status "  ✅ Python syntax validation passed"
            return 0
        else
            print_error "  ❌ Python syntax validation failed"
            return 1
        fi
    else
        print_error "  ❌ File not found: $filepath"
        return 1
    fi
}

# Function to validate shell script
validate_shell_script() {
    local filename="$1"
    local target_dir="$2"
    local filepath="$target_dir/$filename"
    
    if [ -f "$filepath" ]; then
        # Check if it's valid shell syntax
        if bash -n "$filepath" 2>/dev/null; then
            print_status "  ✅ Shell script syntax validation passed"
            return 0
        else
            print_error "  ❌ Shell script syntax validation failed"
            return 1
        fi
    else
        print_error "  ❌ File not found: $filepath"
        return 1
    fi
}

# Function to test NFT downloader
test_nft_downloader() {
    local filepath="$SCRIPT_DIR/nft_downloader.py"
    
    print_status "Testing NFT downloader..."
    
    # Test help command
    if /opt/ipfs-tools/venv/bin/python3 "$filepath" --help >/dev/null 2>&1; then
        print_status "  ✅ Help command works"
    else
        print_error "  ❌ Help command failed"
        return 1
    fi
    
    # Check for EnhancedNFTDownloader class
    if grep -q "class EnhancedNFTDownloader" "$filepath"; then
        print_status "  ✅ Enhanced class found"
    else
        print_warning "  ⚠️  Enhanced class not found"
    fi
    
    # Check for bare hash fix
    if grep -q "if uri and '://' not in uri and self.is_ipfs_reference" "$filepath"; then
        print_status "  ✅ Bare hash fix detected"
    else
        print_warning "  ⚠️  Bare hash fix not detected"
    fi
    
    return 0
}

# Function to test setup script
test_setup_script() {
    local filepath="$INSTALL_DIR/ipfs_setup.sh"
    
    print_status "Testing setup script..."
    
    # Check for key functions
    if grep -q "backup_and_replace_nft_downloader" "$filepath"; then
        print_status "  ✅ Enhanced update function found"
    else
        print_warning "  ⚠️  Enhanced update function not found"
    fi
    
    # Check for enhanced NFT downloader creation
    if grep -q "install_enhanced_nft_downloader" "$filepath"; then
        print_status "  ✅ Enhanced installer function found"
    else
        print_warning "  ⚠️  Enhanced installer function not found"
    fi
    
    return 0
}

# Show available files in source directory
print_status "Available files in source directory:"
ls -la "$SOURCE_DIR" | grep -E '\.(py|sh)$' || print_warning "No .py or .sh files found"

echo ""
print_header "Complete File Update"

# Comprehensive list of all updatable files with descriptions and target directories
declare -A UPDATE_FILES=(
    # NFT Tool Scripts (go to /opt/ipfs-tools/)
    ["nft_downloader.py"]="Enhanced NFT Downloader|$SCRIPT_DIR"
    ["ipfs_health_monitor.py"]="IPFS Health Monitor|$SCRIPT_DIR"
    ["ipfs_backup_restore.sh"]="Backup & Restore Script|$SCRIPT_DIR"
    ["ssd_optimization.sh"]="SSD Optimization Script|$SCRIPT_DIR"
    ["ssd_health_monitor.py"]="SSD Health Monitor|$SCRIPT_DIR"
    ["process_nft_csv.py"]="CSV NFT Processor|$SCRIPT_DIR"
    ["cleanup_nft.py"]="NFT Cleanup Tool|$SCRIPT_DIR"
    ["ipfs_status.py"]="IPFS Status Script|$SCRIPT_DIR"
    
    # Install/Setup Scripts (go to /opt/ipfs-install/)
    ["ipfs_setup.sh"]="Main IPFS Setup Script|$INSTALL_DIR"
    ["update_pi_tools.sh"]="This Update Script|$INSTALL_DIR"
    ["troubleshoot_nft.sh"]="NFT Troubleshooting Script|$INSTALL_DIR"
    ["fix_nft_downloader.sh"]="NFT Downloader Fix Script|$INSTALL_DIR"
    
    # Configuration Files
    ["nfts.csv"]="NFT CSV Data File|$INSTALL_DIR"
    ["config.json"]="Configuration File|$INSTALL_DIR"
)

# Interactive mode
if [ "$#" -eq 0 ]; then
    print_status "Interactive mode - select update scope:"
    echo ""
    
    echo "Update options:"
    echo "  1) Update all NFT tool scripts (/opt/ipfs-tools/)"
    echo "  2) Update all install/setup scripts (/opt/ipfs-install/)"
    echo "  3) Update everything (all files)"
    echo "  4) Select specific files"
    echo "  q) Quit"
    echo ""
    
    read -p "Select option (1-4, q to quit): " choice
    
    case "$choice" in
        "1")
            print_status "Updating all NFT tool scripts..."
            updated_files=()
            for file in "${!UPDATE_FILES[@]}"; do
                IFS='|' read -r description target_dir <<< "${UPDATE_FILES[$file]}"
                if [ "$target_dir" = "$SCRIPT_DIR" ] && [ -f "$SOURCE_DIR/$file" ]; then
                    update_file "$file" "$description" "$target_dir"
                    updated_files+=("$file")
                    
                    # Validate files
                    if [[ "$file" == *.py ]]; then
                        validate_python_file "$file" "$target_dir"
                    elif [[ "$file" == *.sh ]]; then
                        validate_shell_script "$file" "$target_dir"
                    fi
                fi
            done
            
            # Test NFT downloader if updated
            for file in "${updated_files[@]}"; do
                if [ "$file" = "nft_downloader.py" ]; then
                    test_nft_downloader
                    break
                fi
            done
            ;;
            
        "2")
            print_status "Updating all install/setup scripts..."
            updated_files=()
            for file in "${!UPDATE_FILES[@]}"; do
                IFS='|' read -r description target_dir <<< "${UPDATE_FILES[$file]}"
                if [ "$target_dir" = "$INSTALL_DIR" ] && [ -f "$SOURCE_DIR/$file" ]; then
                    update_file "$file" "$description" "$target_dir"
                    updated_files+=("$file")
                    
                    # Validate files
                    if [[ "$file" == *.py ]]; then
                        validate_python_file "$file" "$target_dir"
                    elif [[ "$file" == *.sh ]]; then
                        validate_shell_script "$file" "$target_dir"
                    fi
                fi
            done
            
            # Test setup script if updated
            for file in "${updated_files[@]}"; do
                if [ "$file" = "ipfs_setup.sh" ]; then
                    test_setup_script
                    break
                fi
            done
            ;;
            
        "3")
            print_status "Updating everything..."
            updated_files=()
            tool_files_updated=false
            setup_files_updated=false
            
            for file in "${!UPDATE_FILES[@]}"; do
                IFS='|' read -r description target_dir <<< "${UPDATE_FILES[$file]}"
                if [ -f "$SOURCE_DIR/$file" ]; then
                    update_file "$file" "$description" "$target_dir"
                    updated_files+=("$file")
                    
                    # Track what types of files were updated
                    if [ "$target_dir" = "$SCRIPT_DIR" ]; then
                        tool_files_updated=true
                    elif [ "$target_dir" = "$INSTALL_DIR" ]; then
                        setup_files_updated=true
                    fi
                    
                    # Validate files
                    if [[ "$file" == *.py ]]; then
                        validate_python_file "$file" "$target_dir"
                    elif [[ "$file" == *.sh ]]; then
                        validate_shell_script "$file" "$target_dir"
                    fi
                fi
            done
            
            # Run specific tests
            if [ "$tool_files_updated" = true ]; then
                for file in "${updated_files[@]}"; do
                    if [ "$file" = "nft_downloader.py" ]; then
                        test_nft_downloader
                        break
                    fi
                done
            fi
            
            if [ "$setup_files_updated" = true ]; then
                for file in "${updated_files[@]}"; do
                    if [ "$file" = "ipfs_setup.sh" ]; then
                        test_setup_script
                        break
                    fi
                done
            fi
            ;;
            
        "4")
            print_status "Select specific files to update:"
            echo ""
            
            echo "Available files:"
            i=1
            file_list=()
            for file in "${!UPDATE_FILES[@]}"; do
                IFS='|' read -r description target_dir <<< "${UPDATE_FILES[$file]}"
                if [ -f "$SOURCE_DIR/$file" ]; then
                    echo "  $i) $file ($description) -> $target_dir"
                    file_list+=("$file")
                    ((i++))
                fi
            done
            
            echo ""
            read -p "Enter file numbers (space-separated, e.g., 1 3 5): " selections
            
            for selection in $selections; do
                if [ "$selection" -ge 1 ] && [ "$selection" -le "${#file_list[@]}" ]; then
                    selected_file="${file_list[$((selection-1))]}"
                    IFS='|' read -r description target_dir <<< "${UPDATE_FILES[$selected_file]}"
                    
                    print_status "Selected: $selected_file"
                    update_file "$selected_file" "$description" "$target_dir"
                    
                    # Validate and test
                    if [[ "$selected_file" == *.py ]]; then
                        validate_python_file "$selected_file" "$target_dir"
                    elif [[ "$selected_file" == *.sh ]]; then
                        validate_shell_script "$selected_file" "$target_dir"
                    fi
                    
                    # Special testing
                    if [ "$selected_file" = "nft_downloader.py" ]; then
                        test_nft_downloader
                    elif [ "$selected_file" = "ipfs_setup.sh" ]; then
                        test_setup_script
                    fi
                else
                    print_error "Invalid selection: $selection"
                fi
            done
            ;;
            
        "q"|"Q")
            print_status "Cancelled by user"
            exit 0
            ;;
        *)
            print_error "Invalid selection"
            exit 1
            ;;
    esac

# Command line mode
else
    print_status "Command line mode - updating specified files..."
    
    updated_files=()
    for file in "$@"; do
        if [ -f "$SOURCE_DIR/$file" ]; then
            if [[ -n "${UPDATE_FILES[$file]}" ]]; then
                IFS='|' read -r description target_dir <<< "${UPDATE_FILES[$file]}"
                update_file "$file" "$description" "$target_dir"
                updated_files+=("$file")
                
                # Validate files
                if [[ "$file" == *.py ]]; then
                    validate_python_file "$file" "$target_dir"
                elif [[ "$file" == *.sh ]]; then
                    validate_shell_script "$file" "$target_dir"
                fi
            else
                print_warning "Unknown file: $file (trying to update to $SCRIPT_DIR)"
                update_file "$file" "Unknown file" "$SCRIPT_DIR"
                updated_files+=("$file")
            fi
        else
            print_error "File not found: $SOURCE_DIR/$file"
        fi
    done
    
    # Run specific tests for updated files
    for file in "${updated_files[@]}"; do
        case "$file" in
            "nft_downloader.py")
                test_nft_downloader
                ;;
            "ipfs_setup.sh")
                test_setup_script
                ;;
        esac
    done
fi

print_header "Update Summary"

print_status "Updated files by location:"
echo ""
print_status "NFT Tools (/opt/ipfs-tools/):"
ls -la "$SCRIPT_DIR" | grep -E '\.(py|sh)$' | head -10 || print_status "  No tool files found"

echo ""
print_status "Install Scripts (/opt/ipfs-install/):"
ls -la "$INSTALL_DIR" | grep -E '\.(py|sh)$' | head -10 || print_status "  No install files found"

echo ""
print_status "Recent backups created:"
ls -la "$BACKUP_DIR" | grep "$TIMESTAMP" | head -5 || print_status "  No new backups created"

print_status ""
print_status "🔧 Quick Tests:"
print_status "  ipfs-tools status              - Check IPFS status"
if [ -f "$SCRIPT_DIR/nft_downloader.py" ]; then
    print_status "  ipfs-tools download --help     - Test NFT downloader help"
fi
if [ -f "$INSTALL_DIR/ipfs_setup.sh" ]; then
    print_status "  $INSTALL_DIR/ipfs_setup.sh     - Run updated setup script"
fi
print_status "  ls -la /opt/ipfs-tools/         - View all tools"
print_status "  ls -la /opt/ipfs-install/       - View install scripts"

print_header "Update Complete"

# Offer to restart IPFS service if any core files were updated
core_files=("ipfs_status.py" "nft_downloader.py" "ipfs_health_monitor.py")
restart_needed=false

if [ "$#" -eq 0 ]; then
    # Interactive mode - always offer restart
    restart_needed=true
else
    # Command line mode - check if core files were updated
    for file in "$@"; do
        for core_file in "${core_files[@]}"; do
            if [ "$file" = "$core_file" ]; then
                restart_needed=true
                break 2
            fi
        done
    done
fi

if [ "$restart_needed" = true ]; then
    echo ""
    read -p "Restart IPFS service to ensure clean state? (y/N): " restart_choice
    if [[ "$restart_choice" =~ ^[Yy]$ ]]; then
        print_status "Restarting IPFS service..."
        systemctl restart ipfs
        sleep 3
        print_status "✅ IPFS service restarted"
    fi
fi

print_status "✅ Complete update finished successfully!"
print_status ""
print_status "Updated locations:"
print_status "  • NFT Tools: /opt/ipfs-tools/"
print_status "  • Install Scripts: /opt/ipfs-install/"
print_status "  • Backups: /opt/ipfs-tools/backups/"
print_status ""
print_status "Next steps:"
print_status "  1. Test updated tools: ipfs-tools status"
print_status "  2. Test NFT downloader: ipfs-tools download 0xb6dae651468e9593e4581705a09c10a76ac1e0c8 343"
print_status "  3. Run updated setup if needed: sudo /opt/ipfs-install/ipfs_setup.sh"