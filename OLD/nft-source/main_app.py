#!/usr/bin/env python3
"""
Unified NFT Management System - v2.0 (Part 1: Core App and UI Framework)
A single application for Collecting, Viewing, and Creating NFTs.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import json
import time
import tempfile
from pathlib import Path
from PIL import Image, ImageTk
import requests
import io
import os

# Set DISPLAY if not set (helps with remote/SSH connections)
if not os.environ.get('DISPLAY'):
    os.environ['DISPLAY'] = ':0'

from nft_system_core import (
    ConfigManager,
    DatabaseManager,
    SecureAPIKeyManager,
    IPFSManager,
    RealNFTFetcher
)

# Import the creator functionality from both parts
from main_app_creator_part1 import NFTCreatorMixin
from main_app_creator_part2 import NFTCreatorAdvancedMixin

# Combined Creator Mixin
class NFTCreatorComplete(NFTCreatorMixin, NFTCreatorAdvancedMixin):
    """Complete NFT Creator functionality"""
    pass

# --- Main Application Class ---
class UnifiedNFTApp(NFTCreatorComplete):
    def __init__(self, root):
        self.root = root
        self.root.title("Unified NFT Management System")
        self.root.geometry("1100x750")

        # --- Initialize Core Components ---
        self.app_dir = Path.home() / ".nft-system"
        self.app_dir.mkdir(exist_ok=True)
        
        try:
            self.config = ConfigManager(self.app_dir)
            self.db = DatabaseManager(self.app_dir / "nft_cache.db")
            self.key_manager = SecureAPIKeyManager(self.app_dir)
            self.ipfs = IPFSManager(self.config.get("ipfs_api"))
            self.fetcher = RealNFTFetcher(self.key_manager)
        except Exception as e:
            messagebox.showerror("Initialization Error", f"Failed to initialize core components: {e}")
            self.root.destroy()
            return

        self.nfts = self.db.get_all_nfts()
        self.current_viewer_index = 0

        # --- Main UI Setup ---
        self.create_main_interface()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.check_ipfs_status()

    def create_main_interface(self):
        """Create the main interface with proper error handling"""
        try:
            self.notebook = ttk.Notebook(self.root)
            self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            self.create_collector_tab()
            self.create_viewer_tab()
            self.create_creator_tab()  # This comes from NFTCreatorMixin
            self.create_settings_tab()
        except Exception as e:
            messagebox.showerror("UI Error", f"Failed to create interface: {e}")
            self.root.destroy()

    def on_closing(self):
        try:
            self.db.close()
        except:
            pass
        self.root.destroy()
        
    def check_ipfs_status(self):
        try:
            is_connected = self.ipfs.check_status()
            status_text = "IPFS Status: ✅ Connected" if is_connected else "IPFS Status: ❌ Disconnected"
            if hasattr(self, 'ipfs_status_label'):
                self.ipfs_status_label.config(text=status_text)
        except Exception as e:
            if hasattr(self, 'ipfs_status_label'):
                self.ipfs_status_label.config(text=f"IPFS Status: ❌ Error: {e}")
        
        # Re-check every 30 seconds
        self.root.after(30000, self.check_ipfs_status)

    # --- Clipboard Support Methods ---
    def setup_clipboard_bindings(self, widget):
        """Set up clipboard copy/paste bindings for an entry widget"""
        # Standard clipboard bindings
        widget.bind('<Control-c>', self.copy_text)
        widget.bind('<Control-v>', self.paste_text)
        widget.bind('<Control-x>', self.cut_text)
        widget.bind('<Control-a>', self.select_all)
        
        # Alternative bindings for some systems
        widget.bind('<Control-Insert>', self.copy_text)
        widget.bind('<Shift-Insert>', self.paste_text)
        widget.bind('<Shift-Delete>', self.cut_text)
        
        # Right-click context menu
        widget.bind('<Button-3>', lambda e: self.show_context_menu(e, widget))
    
    def copy_text(self, event):
        """Copy selected text to clipboard"""
        try:
            widget = event.widget
            if widget.selection_present():
                selected_text = widget.selection_get()
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
                print(f"Copied to clipboard: {selected_text}")
        except tk.TclError:
            pass
        return "break"
    
    def paste_text(self, event):
        """Paste text from clipboard"""
        try:
            widget = event.widget
            clipboard_text = self.root.clipboard_get()
            
            # If text is selected, replace it
            if widget.selection_present():
                widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            
            # Insert at cursor position
            widget.insert(tk.INSERT, clipboard_text)
            print(f"Pasted from clipboard: {clipboard_text}")
        except tk.TclError:
            print("Nothing to paste or clipboard empty")
        return "break"
    
    def cut_text(self, event):
        """Cut selected text to clipboard"""
        try:
            widget = event.widget
            if widget.selection_present():
                selected_text = widget.selection_get()
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
                widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                print(f"Cut to clipboard: {selected_text}")
        except tk.TclError:
            pass
        return "break"
    
    def select_all(self, event):
        """Select all text in the widget"""
        try:
            widget = event.widget
            widget.select_range(0, tk.END)
            widget.icursor(tk.END)
        except tk.TclError:
            pass
        return "break"
    
    def show_context_menu(self, event, widget):
        """Show right-click context menu"""
        try:
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="Cut", command=lambda: self.cut_text_manual(widget))
            context_menu.add_command(label="Copy", command=lambda: self.copy_text_manual(widget))
            context_menu.add_command(label="Paste", command=lambda: self.paste_text_manual(widget))
            context_menu.add_separator()
            context_menu.add_command(label="Select All", command=lambda: self.select_all_manual(widget))
            
            context_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            print(f"Error showing context menu: {e}")
    
    def cut_text_manual(self, widget):
        """Manual cut for context menu"""
        try:
            if widget.selection_present():
                selected_text = widget.selection_get()
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
                widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass
    
    def copy_text_manual(self, widget):
        """Manual copy for context menu"""
        try:
            if widget.selection_present():
                selected_text = widget.selection_get()
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
        except tk.TclError:
            pass
    
    def paste_text_manual(self, widget):
        """Manual paste for context menu"""
        try:
            clipboard_text = self.root.clipboard_get()
            if widget.selection_present():
                widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            widget.insert(tk.INSERT, clipboard_text)
        except tk.TclError:
            pass
    
    def select_all_manual(self, widget):
        """Manual select all for context menu"""
        try:
            widget.select_range(0, tk.END)
            widget.icursor(tk.END)
        except tk.TclError:
            pass
    
    def paste_address(self):
        """Paste address from clipboard to address field"""
        try:
            clipboard_text = self.root.clipboard_get().strip()
            self.address_var.set(clipboard_text)
            print(f"Pasted address: {clipboard_text}")
        except tk.TclError:
            messagebox.showinfo("Clipboard", "Clipboard is empty or contains no text")

    def run_threaded(self, func, *args):
        thread = threading.Thread(target=func, args=args, daemon=True)
        thread.start()

    # --- Collector Tab ---
    def create_collector_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🔍 Collector")
        
        ttk.Label(tab, text="Fetch NFTs by Wallet Address or ENS Name", font=("Arial", 14)).pack(pady=10)
        
        entry_frame = ttk.Frame(tab)
        entry_frame.pack(fill=tk.X, padx=20, pady=5)
        self.address_var = tk.StringVar(value=self.config.get("test_wallet"))
        
        # Create address entry with clipboard support
        self.address_entry = ttk.Entry(entry_frame, textvariable=self.address_var, width=50)
        self.address_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.setup_clipboard_bindings(self.address_entry)
        
        self.fetch_btn = ttk.Button(entry_frame, text="Fetch NFTs", command=self.fetch_nfts)
        self.fetch_btn.pack(side=tk.LEFT, padx=5)
        
        # Add paste button for convenience
        paste_btn = ttk.Button(entry_frame, text="📋 Paste", command=self.paste_address, width=8)
        paste_btn.pack(side=tk.LEFT, padx=2)

        self.collector_status_var = tk.StringVar(value="Ready to fetch.")
        ttk.Label(tab, textvariable=self.collector_status_var).pack(pady=5)
        
    def fetch_nfts(self):
        address = self.address_var.get().strip()
        if not address:
            messagebox.showerror("Error", "Please enter a wallet address.")
            return
            
        self.fetch_btn.config(state=tk.DISABLED)
        self.collector_status_var.set(f"Fetching NFTs for {address}...")
        self.run_threaded(self._fetch_nfts_thread, address)

    def _fetch_nfts_thread(self, address):
        try:
            nfts = self.fetcher.fetch_nfts(address, self.config.get("primary_api"))

            if nfts is None:
                self.root.after(0, lambda: self.collector_status_var.set("Could not fetch NFTs. Check API keys and address."))
            else:
                self.db.cache_nfts(nfts)
                self.nfts = self.db.get_all_nfts()
                self.root.after(0, self.update_viewer_list)
                self.root.after(0, lambda: self.collector_status_var.set(f"Success! Found {len(nfts)} new NFTs. Viewer updated."))
        except Exception as e:
            self.root.after(0, lambda: self.collector_status_var.set(f"Error: {str(e)}"))
        
        self.root.after(0, lambda: self.fetch_btn.config(state=tk.NORMAL))

    # --- Viewer Tab ---
    def create_viewer_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🖼️ Viewer")

        # Main layout
        main_frame = ttk.Frame(tab)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # NFT List on the left
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=0, column=0, sticky="ns", padx=5, pady=5)
        
        # Add scrollbar to listbox
        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        self.viewer_listbox = tk.Listbox(listbox_frame, width=40)
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.viewer_listbox.yview)
        self.viewer_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.viewer_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.viewer_listbox.bind('<<ListboxSelect>>', self.on_viewer_select)

        # Image and Details on the right
        details_frame = ttk.Frame(main_frame)
        details_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        details_frame.rowconfigure(0, weight=3)
        details_frame.rowconfigure(1, weight=2)
        details_frame.columnconfigure(0, weight=1)
        
        # Image display with placeholder
        image_frame = ttk.Frame(details_frame)
        image_frame.grid(row=0, column=0, sticky="nsew")
        
        self.image_label = ttk.Label(image_frame, text="Select an NFT to view", 
                                   background="lightgray", anchor=tk.CENTER)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Metadata display
        self.metadata_text = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD, height=10)
        self.metadata_text.grid(row=1, column=0, sticky="nsew", pady=5)

        # Initialize viewer list
        self.update_viewer_list()
        
        if self.nfts:
            self.display_nft_in_viewer(0)

    def update_viewer_list(self):
        try:
            self.viewer_listbox.delete(0, tk.END)
            for nft in self.nfts:
                display_name = nft.get('title', f"NFT #{nft.get('token_id', 'Unknown')}")
                self.viewer_listbox.insert(tk.END, display_name)
        except Exception as e:
            print(f"Error updating viewer list: {e}")

    def on_viewer_select(self, event):
        try:
            selection = self.viewer_listbox.curselection()
            if selection:
                self.current_viewer_index = selection[0]
                self.display_nft_in_viewer(self.current_viewer_index)
        except Exception as e:
            print(f"Error in viewer selection: {e}")

    def display_nft_in_viewer(self, index):
        if not self.nfts or not (0 <= index < len(self.nfts)):
            return
            
        try:
            nft = self.nfts[index]
            
            # Get image URL and convert IPFS URLs to HTTP gateway URLs
            image_url = nft.get('image_url', '')
            
            # If no image_url, try to get it from media array
            if not image_url:
                media = nft.get('media', [])
                if media and len(media) > 0:
                    image_url = media[0].get('gateway', '')
            
            # Convert IPFS URLs to HTTP gateway URLs
            if image_url:
                image_url = self.convert_ipfs_url_to_gateway(image_url)
                self.run_threaded(self._load_viewer_image, image_url)
            else:
                self.image_label.config(image='', text="No image available")
                self.image_label.image = None
            
            # Display metadata
            self.metadata_text.delete(1.0, tk.END)
            self.metadata_text.insert(tk.END, f"Title: {nft.get('title', 'Unknown')}\n")
            self.metadata_text.insert(tk.END, f"Contract: {nft.get('contract_address', 'Unknown')}\n")
            self.metadata_text.insert(tk.END, f"Token ID: {nft.get('token_id', 'Unknown')}\n\n")
            self.metadata_text.insert(tk.END, f"Description: {nft.get('description', 'No description')}\n\n")
            
            # Show the actual image URL being used
            if image_url:
                self.metadata_text.insert(tk.END, f"Image URL: {image_url}\n\n")
            
            # Parse and display attributes if available
            try:
                metadata_str = nft.get('metadata', '{}')
                if isinstance(metadata_str, str):
                    metadata = json.loads(metadata_str)
                else:
                    metadata = metadata_str
                
                if isinstance(metadata, dict) and 'attributes' in metadata:
                    self.metadata_text.insert(tk.END, "Attributes:\n")
                    for attr in metadata['attributes']:
                        trait_type = attr.get('trait_type', 'Property')
                        value = attr.get('value', 'Unknown')
                        self.metadata_text.insert(tk.END, f"  - {trait_type}: {value}\n")
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error parsing metadata: {e}")
                
        except Exception as e:
            print(f"Error displaying NFT: {e}")

    def convert_ipfs_url_to_gateway(self, url):
        """Convert IPFS URLs to HTTP gateway URLs with smart selection"""
        if not url:
            return url
            
        # Extract IPFS hash from various URL formats
        ipfs_hash = ""
        if url.startswith('ipfs://'):
            ipfs_hash = url.replace('ipfs://', '')
        elif '/ipfs/' in url:
            ipfs_hash = url.split('/ipfs/')[-1]
        else:
            return url  # Already a regular URL
        
        # Get user's gateway preference
        gateway_preference = self.config.get("gateway_preference", "auto")
        custom_gateway = self.config.get("custom_gateway", "")
        
        # Use custom gateway if specified
        if custom_gateway:
            gateway_url = f"{custom_gateway.rstrip('/')}/ipfs/{ipfs_hash}"
            print(f"Using custom gateway: {gateway_url}")
            return gateway_url
        
        # Handle different preferences
        if gateway_preference == "local_only":
            return self.get_local_gateway_url(ipfs_hash)
        elif gateway_preference == "public_only":
            return self.get_public_gateway_url(ipfs_hash)
        else:  # auto
            return self.get_best_gateway_for_hash(ipfs_hash)

    def get_local_gateway_url(self, ipfs_hash):
        """Get local IPFS gateway URL"""
        if self.ipfs.is_connected:
            local_url = f"http://127.0.0.1:8080/ipfs/{ipfs_hash}"
            print(f"Using local IPFS gateway: {local_url}")
            return local_url
        else:
            print("Local IPFS not available, cannot use local gateway")
            # Return a placeholder that will show an error
            return f"http://127.0.0.1:8080/ipfs/{ipfs_hash}"

    def get_public_gateway_url(self, ipfs_hash):
        """Get public IPFS gateway URL"""
        public_url = f"https://ipfs.io/ipfs/{ipfs_hash}"
        print(f"Using public IPFS gateway: {public_url}")
        return public_url

    def get_best_gateway_for_hash(self, ipfs_hash):
        """Get the best available gateway for a specific hash (auto mode)"""
        # Try local gateway first if IPFS is connected
        if self.ipfs.is_connected:
            # Quick test to see if local gateway is responsive
            local_url = f"http://127.0.0.1:8080/ipfs/{ipfs_hash}"
            try:
                # Quick test with a very short timeout
                response = requests.head(local_url, timeout=2)
                if response.status_code == 200:
                    print(f"Using fast local gateway: {local_url}")
                    return local_url
            except Exception:
                print("Local gateway test failed, trying public gateway")
        
        # Fallback to public gateway
        public_url = f"https://ipfs.io/ipfs/{ipfs_hash}"
        print(f"Using public gateway: {public_url}")
        return public_url

    def test_gateway_availability(self, gateway_url):
        """Test if a gateway is available and responsive"""
        try:
            # Test with a small known IPFS hash (1-byte file)
            test_hash = "QmbFMke1KXqnYyBBWxB74N4c5SBnJMVAiMNRcGu6x1AwQH"
            test_url = f"{gateway_url}/ipfs/{test_hash}"
            
            response = requests.head(test_url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Gateway test failed for {gateway_url}: {e}")
            return False


    def test_gateway_availability(self, gateway_url):
        """Test if a gateway is available and responsive"""
        try:
            # Test with a small known IPFS hash (empty file)
            test_hash = "QmbFMke1KXqnYyBBWxB74N4c5SBnJMVAiMNRcGu6x1AwQH"
            test_url = f"{gateway_url}/ipfs/{test_hash}"
            
            response = requests.head(test_url, timeout=3)
            return response.status_code == 200
        except Exception:
            return False

    def get_best_gateway_for_hash(self, ipfs_hash):
        """Get the best available gateway for a specific hash"""
        # Local gateway options
        local_gateways = [
            "http://127.0.0.1:8080",
            "http://localhost:8080"
        ]
        
        # Public gateway options (as fallback)
        public_gateways = [
            "https://ipfs.io",
            "https://gateway.ipfs.io",
            "https://cloudflare-ipfs.com"
        ]
        
        # Try local gateways first if IPFS is connected
        if self.ipfs.is_connected:
            for gateway in local_gateways:
                if self.test_gateway_availability(gateway):
                    gateway_url = f"{gateway}/ipfs/{ipfs_hash}"
                    print(f"Using fast local gateway: {gateway_url}")
                    return gateway_url
        
        # Fallback to public gateways
        for gateway in public_gateways:
            if self.test_gateway_availability(gateway):
                gateway_url = f"{gateway}/ipfs/{ipfs_hash}"
                print(f"Using public gateway: {gateway_url}")
                return gateway_url
        
        # Last resort - use ipfs.io without testing
        fallback_url = f"https://ipfs.io/ipfs/{ipfs_hash}"
        print(f"Using fallback gateway: {fallback_url}")
        return fallback_url

    def _load_viewer_image(self, url):
        if not url:
            return
            
        try:
            response = requests.get(url, timeout=20)
            if response.status_code == 200:
                image_data = response.content
                img = Image.open(io.BytesIO(image_data))
                
                # Resize image to fit display area
                img.thumbnail((600, 600), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)

                def update_ui():
                    self.image_label.config(image=photo, text="")
                    self.image_label.image = photo
                
                self.root.after(0, update_ui)
            else:
                def show_error():
                    self.image_label.config(image='', text=f"Failed to load image\n(HTTP {response.status_code})")
                    self.image_label.image = None
                self.root.after(0, show_error)
                
        except Exception as e:
            print(f"Failed to load image {url}: {e}")
            def show_error():
                self.image_label.config(image='', text=f"Image load error:\n{str(e)}")
                self.image_label.image = None
            self.root.after(0, show_error)

    # --- Settings Tab ---
    def create_settings_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚙️ Settings")
        
        # IPFS Status
        self.ipfs_status_label = ttk.Label(tab, text="Checking IPFS...", font=("Arial", 12))
        self.ipfs_status_label.pack(pady=10)
        
        # IPFS Management Section
        ipfs_frame = ttk.LabelFrame(tab, text="IPFS Management", padding=10)
        ipfs_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Bulk pin section
        bulk_pin_frame = ttk.Frame(ipfs_frame)
        bulk_pin_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(bulk_pin_frame, text="Pin your NFT collection to local IPFS for faster access:").pack(anchor=tk.W)
        
        pin_buttons_frame = ttk.Frame(bulk_pin_frame)
        pin_buttons_frame.pack(fill=tk.X, pady=5)
        
        self.bulk_pin_btn = ttk.Button(pin_buttons_frame, text="📌 Pin All NFTs to Local IPFS", 
                                     command=self.start_bulk_pin)
        self.bulk_pin_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(pin_buttons_frame, text="🔍 Manage Pinned Files", 
                  command=self.open_pin_manager).pack(side=tk.LEFT, padx=5)
        
        # Bulk pin status
        self.bulk_pin_status_var = tk.StringVar(value="Ready to pin NFT collection")
        ttk.Label(bulk_pin_frame, textvariable=self.bulk_pin_status_var, 
                 font=("Arial", 10), foreground="blue").pack(anchor=tk.W, pady=2)
        
        # Progress bar for bulk pinning
        self.bulk_pin_progress = ttk.Progressbar(bulk_pin_frame, mode='determinate')
        self.bulk_pin_progress_label = ttk.Label(bulk_pin_frame, text="", font=("Arial", 9))
        
        # IPFS Gateway Settings
        gateway_frame = ttk.LabelFrame(tab, text="IPFS Gateway Settings", padding=10)
        gateway_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Gateway preference
        gateway_pref_frame = ttk.Frame(gateway_frame)
        gateway_pref_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(gateway_pref_frame, text="Gateway Preference:").pack(side=tk.LEFT)
        
        self.gateway_preference_var = tk.StringVar(value=self.config.get("gateway_preference", "auto"))
        gateway_combo = ttk.Combobox(gateway_pref_frame, textvariable=self.gateway_preference_var, 
                                   values=["auto", "local_only", "public_only"], state="readonly", width=15)
        gateway_combo.pack(side=tk.LEFT, padx=5)
        
        # Gateway test button
        test_gateway_btn = ttk.Button(gateway_pref_frame, text="🔍 Test Gateways", 
                                    command=self.test_all_gateways)
        test_gateway_btn.pack(side=tk.LEFT, padx=5)
        
        # Custom gateway
        custom_gateway_frame = ttk.Frame(gateway_frame)
        custom_gateway_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(custom_gateway_frame, text="Custom Gateway:").pack(side=tk.LEFT)
        self.custom_gateway_var = tk.StringVar(value=self.config.get("custom_gateway", ""))
        custom_gateway_entry = ttk.Entry(custom_gateway_frame, textvariable=self.custom_gateway_var, width=40)
        custom_gateway_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Gateway preference explanations
        gateway_help = ttk.Label(gateway_frame, 
                               text="• Auto: Try local first, fallback to public\n• Local Only: Use local IPFS node only\n• Public Only: Use public gateways only",
                               font=("Arial", 9), foreground="gray")
        gateway_help.pack(anchor=tk.W, pady=5)
        
        # Save gateway settings button
        save_gateway_btn = ttk.Button(gateway_frame, text="Save Gateway Settings", 
                                    command=self.save_gateway_settings)
        save_gateway_btn.pack(pady=5)
        
        # API Keys Section
        api_frame = ttk.LabelFrame(tab, text="API Keys (Encrypted Storage)", padding=10)
        api_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.api_key_vars = {}
        try:
            loaded_keys = self.key_manager.load_keys()
        except Exception as e:
            loaded_keys = {}
            print(f"Error loading API keys: {e}")
        
        for api_id in self.fetcher.supported_apis:
            frame = ttk.Frame(api_frame)
            frame.pack(fill=tk.X, pady=2)
            ttk.Label(frame, text=f"{api_id.title()}:", width=10).pack(side=tk.LEFT)
            
            var = tk.StringVar(value=loaded_keys.get(api_id, ''))
            self.api_key_vars[api_id] = var
            api_entry = ttk.Entry(frame, textvariable=var, show="*", width=50)
            api_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
            self.setup_clipboard_bindings(api_entry)

        save_btn = ttk.Button(api_frame, text="Save API Keys", command=self.save_api_keys)
        save_btn.pack(pady=10)

        # Debug Info Section
        debug_frame = ttk.LabelFrame(tab, text="Debug Information", padding=10)
        debug_frame.pack(fill=tk.X, padx=20, pady=10)
        
        debug_text = scrolledtext.ScrolledText(debug_frame, height=8, wrap=tk.WORD)
        debug_text.pack(fill=tk.X)
        
        # Add debug information
        debug_info = f"""Application Directory: {self.app_dir}
Database Path: {self.app_dir / 'nft_cache.db'}
Database exists: {(self.app_dir / 'nft_cache.db').exists()}
Cached NFTs: {len(self.nfts)}
IPFS API URL: {self.config.get('ipfs_api')}
IPFS Local Gateway: http://127.0.0.1:8080
Primary API: {self.config.get('primary_api')}
Gateway Preference: {self.config.get('gateway_preference', 'auto')}
Test Wallet: {self.config.get('test_wallet')}
"""
        debug_text.insert(tk.END, debug_info)
        debug_text.config(state=tk.DISABLED)

    def open_pin_manager(self):
        """Open the pin management window"""
        if not self.ipfs.check_status():
            messagebox.showerror("IPFS Not Connected", "IPFS is not running.")
            return
        
        # Create pin manager window
        pin_window = tk.Toplevel(self.root)
        pin_window.title("IPFS Pin Manager")
        pin_window.geometry("800x600")
        pin_window.configure(bg="white")
        
        # Header
        header_frame = ttk.Frame(pin_window)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(header_frame, text="📌 IPFS Pin Manager", 
                 font=("Arial", 16, "bold")).pack(side=tk.LEFT)
        
        # Refresh button
        ttk.Button(header_frame, text="🔄 Refresh", 
                  command=lambda: self.refresh_pin_list(pin_listbox, status_label)).pack(side=tk.RIGHT)
        
        # Status label
        status_label = ttk.Label(pin_window, text="Loading pinned files...", font=("Arial", 10))
        status_label.pack(pady=5)
        
        # Main frame
        main_frame = ttk.Frame(pin_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Listbox with scrollbar for pinned files
        listbox_frame = ttk.Frame(main_frame)
        listbox_frame.grid(row=0, column=0, sticky="nsew", pady=5)
        listbox_frame.columnconfigure(0, weight=1)
        listbox_frame.rowconfigure(0, weight=1)
        
        # Create listbox with multiple selection
        pin_listbox = tk.Listbox(listbox_frame, selectmode=tk.EXTENDED, font=("Courier", 10))
        pin_listbox.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=pin_listbox.yview)
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        pin_listbox.configure(yscrollcommand=v_scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(listbox_frame, orient="horizontal", command=pin_listbox.xview)
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        pin_listbox.configure(xscrollcommand=h_scrollbar.set)
        
        # Selection info
        selection_frame = ttk.Frame(main_frame)
        selection_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        selection_label = ttk.Label(selection_frame, text="Select files to unpin (Ctrl+Click for multiple)")
        selection_label.pack(side=tk.LEFT)
        
        selected_count_label = ttk.Label(selection_frame, text="0 selected", font=("Arial", 10, "bold"))
        selected_count_label.pack(side=tk.RIGHT)
        
        # Update selection count when selection changes
        def update_selection_count(event=None):
            count = len(pin_listbox.curselection())
            selected_count_label.config(text=f"{count} selected")
        
        pin_listbox.bind('<<ListboxSelect>>', update_selection_count)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, sticky="ew", pady=10)
        
        # Select all/none buttons
        ttk.Button(button_frame, text="✅ Select All", 
                  command=lambda: self.select_all_pins(pin_listbox, update_selection_count)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="❌ Select None", 
                  command=lambda: self.select_no_pins(pin_listbox, update_selection_count)).pack(side=tk.LEFT, padx=5)
        
        # Filter buttons
        ttk.Button(button_frame, text="🖼️ Select NFT Files", 
                  command=lambda: self.select_nft_related_pins(pin_listbox, update_selection_count)).pack(side=tk.LEFT, padx=10)
        
        # Unpin button
        unpin_button = ttk.Button(button_frame, text="🗑️ Unpin Selected", 
                                command=lambda: self.unpin_selected_files(pin_listbox, status_label, update_selection_count),
                                style="Accent.TButton")
        unpin_button.pack(side=tk.RIGHT, padx=5)
        
        # Info frame
        info_frame = ttk.LabelFrame(main_frame, text="Information", padding=5)
        info_frame.grid(row=3, column=0, sticky="ew", pady=5)
        
        info_text = """Tips:
• Use Ctrl+Click to select multiple files
• Use Shift+Click to select a range
• NFT-related files usually start with 'Qm' or 'baf'
• System files are usually safe to keep pinned
• Unpinning removes files from local storage but they remain on the IPFS network"""
        
        ttk.Label(info_frame, text=info_text, font=("Arial", 9), justify=tk.LEFT).pack(anchor=tk.W)
        
        # Store references for the callbacks
        pin_window.pin_listbox = pin_listbox
        pin_window.status_label = status_label
        
        # Load pinned files
        self.refresh_pin_list(pin_listbox, status_label)

    def refresh_pin_list(self, listbox, status_label):
        """Refresh the list of pinned files"""
        def load_pins():
            try:
                status_label.config(text="Loading pinned files...")
                
                # Get pinned files using IPFS API
                response = requests.post(f"{self.ipfs.api_url}/api/v0/pin/ls", 
                                       params={'type': 'recursive'}, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    pins = data.get('Keys', {})
                    
                    # Filter and sort pins
                    user_pins = []
                    for pin_hash, pin_info in pins.items():
                        if pin_hash.startswith('Qm') or pin_hash.startswith('baf'):
                            # Try to get additional info
                            pin_type = pin_info.get('Type', 'unknown')
                            user_pins.append({
                                'hash': pin_hash,
                                'type': pin_type,
                                'display': f"{pin_hash} ({pin_type})"
                            })
                    
                    # Sort by hash
                    user_pins.sort(key=lambda x: x['hash'])
                    
                    def update_ui():
                        listbox.delete(0, tk.END)
                        for pin in user_pins:
                            listbox.insert(tk.END, pin['display'])
                        
                        status_label.config(text=f"📌 {len(user_pins)} pinned files loaded")
                    
                    self.root.after(0, update_ui)
                else:
                    def show_error():
                        status_label.config(text="❌ Failed to load pinned files")
                    self.root.after(0, show_error)
                    
            except Exception as e:
                def show_error():
                    status_label.config(text=f"❌ Error: {str(e)}")
                self.root.after(0, show_error)
        
        self.run_threaded(load_pins)

    def select_all_pins(self, listbox, update_callback):
        """Select all items in the listbox"""
        listbox.select_set(0, tk.END)
        update_callback()

    def select_no_pins(self, listbox, update_callback):
        """Deselect all items in the listbox"""
        listbox.selection_clear(0, tk.END)
        update_callback()

    def select_nft_related_pins(self, listbox, update_callback):
        """Select pins that are likely NFT-related"""
        listbox.selection_clear(0, tk.END)
        
        # Get all NFT hashes from database
        nft_hashes = set()
        for nft in self.nfts:
            # Extract hashes from various fields
            image_url = nft.get('image_url', '')
            if 'Qm' in image_url or 'baf' in image_url:
                import re
                hash_pattern = r'(Qm[1-9A-HJ-NP-Za-km-z]{44}|baf[a-z0-9]{52,})'
                matches = re.findall(hash_pattern, image_url)
                nft_hashes.update(matches)
            
            # Check media array
            media = nft.get('media', [])
            for media_item in media:
                if isinstance(media_item, dict):
                    gateway_url = media_item.get('gateway', '')
                    if 'Qm' in gateway_url or 'baf' in gateway_url:
                        import re
                        hash_pattern = r'(Qm[1-9A-HJ-NP-Za-km-z]{44}|baf[a-z0-9]{52,})'
                        matches = re.findall(hash_pattern, gateway_url)
                        nft_hashes.update(matches)
        
        # Select items that match NFT hashes
        for i in range(listbox.size()):
            item_text = listbox.get(i)
            item_hash = item_text.split(' ')[0]  # Get hash part before space
            if item_hash in nft_hashes:
                listbox.select_set(i)
        
        update_callback()

    def unpin_selected_files(self, listbox, status_label, update_callback):
        """Unpin the selected files"""
        selected_indices = listbox.curselection()
        
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select files to unpin.")
            return
        
        # Get selected hashes
        selected_hashes = []
        for index in selected_indices:
            item_text = listbox.get(index)
            item_hash = item_text.split(' ')[0]  # Get hash part before space
            selected_hashes.append(item_hash)
        
        # Confirm deletion
        result = messagebox.askyesno("Confirm Unpin", 
                                   f"Unpin {len(selected_hashes)} selected files?\n\n"
                                   "This will remove them from local storage but they "
                                   "will remain on the IPFS network.\n\n"
                                   "Continue?")
        if not result:
            return
        
        # Start unpinning process
        status_label.config(text=f"Unpinning {len(selected_hashes)} files...")
        
        def unpin_thread():
            unpinned_count = 0
            failed_count = 0
            
            for i, hash_val in enumerate(selected_hashes, 1):
                try:
                    # Update status
                    def update_status():
                        status_label.config(text=f"Unpinning {i}/{len(selected_hashes)}: {hash_val[:12]}...")
                    self.root.after(0, update_status)
                    
                    # Unpin using IPFS API
                    response = requests.post(f"{self.ipfs.api_url}/api/v0/pin/rm", 
                                           params={'arg': hash_val}, timeout=10)
                    
                    if response.status_code == 200:
                        unpinned_count += 1
                        print(f"✅ Unpinned: {hash_val}")
                    else:
                        failed_count += 1
                        print(f"❌ Failed to unpin: {hash_val}")
                    
                    time.sleep(0.1)  # Small delay
                    
                except Exception as e:
                    failed_count += 1
                    print(f"❌ Error unpinning {hash_val}: {e}")
            
            # Show results and refresh
            def show_results():
                if unpinned_count > 0:
                    messagebox.showinfo("Unpin Complete", 
                                      f"Successfully unpinned: {unpinned_count} files\n"
                                      f"Failed to unpin: {failed_count} files")
                else:
                    messagebox.showerror("Unpin Failed", 
                                       f"Failed to unpin any files. Check IPFS connection.")
                
                # Refresh the list
                self.refresh_pin_list(listbox, status_label)
                update_callback()
            
            self.root.after(0, show_results)
        
        self.run_threaded(unpin_thread)

    # Keep all your existing methods for bulk pinning, gateway testing, etc.
    # (start_bulk_pin, _bulk_pin_thread, etc. from previous implementations)
    
    def start_bulk_pin(self):
        """Start the bulk pinning process"""
        if not self.ipfs.check_status():
            messagebox.showerror("IPFS Not Connected", 
                               "IPFS is not running. Please start IPFS first:\n\n"
                               "sudo systemctl start ipfs\nOR\nipfs daemon")
            return
        
        if not self.nfts:
            messagebox.showinfo("No NFTs", "No NFTs found in your collection. Add some NFTs first!")
            return
        
        # Ask for confirmation
        result = messagebox.askyesno("Bulk Pin NFTs", 
                                   f"Pin all IPFS files from your {len(self.nfts)} NFTs to local IPFS?\n\n"
                                   "This will:\n"
                                   "• Make your NFTs load faster\n"
                                   "• Allow offline viewing\n"
                                   "• Store files permanently on your device\n\n"
                                   "Continue?")
        if not result:
            return
        
        # Disable button and start process
        self.bulk_pin_btn.config(state=tk.DISABLED)
        self.bulk_pin_status_var.set("Extracting IPFS hashes from NFT collection...")
        
        # Show progress bar
        self.bulk_pin_progress.pack(fill=tk.X, pady=5)
        self.bulk_pin_progress_label.pack(anchor=tk.W)
        
        # Start bulk pinning in background thread
        self.run_threaded(self._bulk_pin_thread)

    def _bulk_pin_thread(self):
        """Bulk pin NFTs in background thread"""
        import re
        
        def extract_ipfs_hash(url):
            """Extract IPFS hash from various URL formats"""
            if not url:
                return None
            
            # Handle ipfs:// URLs
            if url.startswith('ipfs://'):
                return url.replace('ipfs://', '').split('/')[0]
            
            # Handle gateway URLs with /ipfs/
            if '/ipfs/' in url:
                parts = url.split('/ipfs/')
                if len(parts) > 1:
                    return parts[1].split('/')[0]
            
            # Handle direct hashes
            hash_pattern = r'(Qm[1-9A-HJ-NP-Za-km-z]{44}|baf[a-z0-9]{52,})'
            match = re.search(hash_pattern, url)
            if match:
                return match.group(1)
            
            return None
        
        try:
            # Extract all IPFS hashes
            hashes_to_pin = set()
            
            for nft in self.nfts:
                # Check image URL
                image_url = nft.get('image_url', '')
                if image_url:
                    hash_val = extract_ipfs_hash(image_url)
                    if hash_val:
                        hashes_to_pin.add(hash_val)
                
                # Check media array
                media = nft.get('media', [])
                for media_item in media:
                    if isinstance(media_item, dict):
                        gateway_url = media_item.get('gateway', '')
                        if gateway_url:
                            hash_val = extract_ipfs_hash(gateway_url)
                            if hash_val:
                                hashes_to_pin.add(hash_val)
                
                # Check metadata for image field
                try:
                    metadata = nft.get('metadata', {})
                    if isinstance(metadata, dict):
                        metadata_image = metadata.get('image', '')
                        if metadata_image:
                            hash_val = extract_ipfs_hash(metadata_image)
                            if hash_val:
                                hashes_to_pin.add(hash_val)
                except:
                    pass
            
            if not hashes_to_pin:
                def show_no_hashes():
                    self.bulk_pin_status_var.set("No IPFS hashes found in NFT collection")
                    messagebox.showinfo("No Hashes", "No IPFS hashes found in your NFT collection.")
                    self._reset_bulk_pin_ui()
                
                self.root.after(0, show_no_hashes)
                return
            
            # Update UI with found hashes
            def update_found():
                self.bulk_pin_status_var.set(f"Found {len(hashes_to_pin)} unique IPFS hashes. Starting pinning...")
                self.bulk_pin_progress.config(maximum=len(hashes_to_pin), value=0)
            
            self.root.after(0, update_found)
            
            # Pin all hashes
            pinned_count = 0
            failed_count = 0
            
            for i, hash_val in enumerate(hashes_to_pin, 1):
                try:
                    # Update progress
                    def update_progress():
                        self.bulk_pin_progress.config(value=i)
                        self.bulk_pin_progress_label.config(text=f"Pinning {i}/{len(hashes_to_pin)}: {hash_val[:12]}...")
                        self.bulk_pin_status_var.set(f"Pinning {i}/{len(hashes_to_pin)} files...")
                    
                    self.root.after(0, update_progress)
                    
                    # Attempt to pin
                    success = self.ipfs.pin_hash(hash_val)
                    if success:
                        pinned_count += 1
                        print(f"✅ Pinned: {hash_val}")
                    else:
                        failed_count += 1
                        print(f"⚠️ Failed to pin: {hash_val}")
                    
                    # Small delay to avoid overwhelming IPFS
                    time.sleep(0.3)
                    
                except Exception as e:
                    failed_count += 1
                    print(f"❌ Error pinning {hash_val}: {e}")
            
            # Show results
            def show_results():
                success_msg = f"""✅ Bulk Pinning Complete!

Successfully pinned: {pinned_count} files
Failed to pin: {failed_count} files
Total processed: {len(hashes_to_pin)} files

Your NFTs will now load faster using local IPFS!"""
                
                self.bulk_pin_status_var.set(f"Complete! Pinned {pinned_count}/{len(hashes_to_pin)} files")
                messagebox.showinfo("Bulk Pinning Complete", success_msg)
                self._reset_bulk_pin_ui()
            
            self.root.after(0, show_results)
            
        except Exception as e:
            error_msg = f"Bulk pinning failed: {str(e)}"
            print(error_msg)
            
            def show_error():
                self.bulk_pin_status_var.set("Bulk pinning failed!")
                messagebox.showerror("Bulk Pinning Error", error_msg)
                self._reset_bulk_pin_ui()
            
            self.root.after(0, show_error)

    def _reset_bulk_pin_ui(self):
        """Reset bulk pin UI elements"""
        self.bulk_pin_btn.config(state=tk.NORMAL)
        self.bulk_pin_progress.pack_forget()
        self.bulk_pin_progress_label.pack_forget()

    def check_pinned_files(self):
        """Check and display pinned files"""
        if not self.ipfs.check_status():
            messagebox.showerror("IPFS Not Connected", "IPFS is not running.")
            return
        
        def check_pins_thread():
            try:
                # Get pinned files using IPFS API
                response = requests.post(f"{self.ipfs.api_url}/api/v0/pin/ls", 
                                       params={'type': 'recursive'}, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    pins = data.get('Keys', {})
                    
                    # Filter out system pins (focus on user content)
                    user_pins = []
                    for pin_hash, pin_info in pins.items():
                        if pin_hash.startswith('Qm') or pin_hash.startswith('baf'):
                            user_pins.append(pin_hash)
                    
                    def show_pins():
                        if user_pins:
                            pin_list = '\n'.join([f"• {pin_hash}" for pin_hash in user_pins[:10]])
                            if len(user_pins) > 10:
                                pin_list += f"\n... and {len(user_pins) - 10} more"
                            
                            message = f"📌 Found {len(user_pins)} pinned files:\n\n{pin_list}"
                        else:
                            message = "No user files are currently pinned to local IPFS."
                        
                        messagebox.showinfo("Pinned Files", message)
                    
                    self.root.after(0, show_pins)
                else:
                    def show_error():
                        messagebox.showerror("Error", "Failed to get pinned files from IPFS")
                    self.root.after(0, show_error)
                    
            except Exception as e:
                def show_error():
                    messagebox.showerror("Error", f"Failed to check pinned files: {e}")
                self.root.after(0, show_error)
        
        self.run_threaded(check_pins_thread)

    def test_all_gateways(self):
        """Test all available gateways and show results"""
        def test_gateways_thread():
            results = []
            
            # Test local gateways
            local_gateways = ["http://127.0.0.1:8080", "http://localhost:8080"]
            for gateway in local_gateways:
                try:
                    is_available = self.test_gateway_availability(gateway)
                    status = "✅ Available" if is_available else "❌ Not available"
                    results.append(f"Local: {gateway} - {status}")
                except Exception as e:
                    results.append(f"Local: {gateway} - ❌ Error: {e}")
            
            # Test public gateways
            public_gateways = ["https://ipfs.io", "https://gateway.ipfs.io", "https://cloudflare-ipfs.com"]
            for gateway in public_gateways:
                try:
                    is_available = self.test_gateway_availability(gateway)
                    status = "✅ Available" if is_available else "❌ Not available"
                    results.append(f"Public: {gateway} - {status}")
                except Exception as e:
                    results.append(f"Public: {gateway} - ❌ Error: {e}")
            
            # Show results
            def show_results():
                result_text = "IPFS Gateway Test Results:\n\n" + "\n".join(results)
                messagebox.showinfo("Gateway Test Results", result_text)
            
            self.root.after(0, show_results)
        
        # Show testing message
        messagebox.showinfo("Testing Gateways", "Testing gateways... This may take a few seconds.")
        self.run_threaded(test_gateways_thread)

    def save_gateway_settings(self):
        """Save gateway preferences to config"""
        try:
            self.config.set("gateway_preference", self.gateway_preference_var.get())
            self.config.set("custom_gateway", self.custom_gateway_var.get())
            messagebox.showinfo("Success", "Gateway settings saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save gateway settings: {e}")

    def save_api_keys(self):
        try:
            keys_to_save = {api_id: var.get() for api_id, var in self.api_key_vars.items() if var.get()}
            self.key_manager.save_keys(keys_to_save)
            self.fetcher.api_keys = self.key_manager.load_keys()
            messagebox.showinfo("Success", "API Keys saved securely.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save API keys: {e}")

    def test_gateway_availability(self, gateway_url):
        """Test if a gateway is available and responsive"""
        try:
            # Test with a small known IPFS hash (1-byte file)
            test_hash = "QmbFMke1KXqnYyBBWxB74N4c5SBnJMVAiMNRcGu6x1AwQH"
            test_url = f"{gateway_url}/ipfs/{test_hash}"
            
            response = requests.head(test_url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Gateway test failed for {gateway_url}: {e}")
            return False

    def test_all_gateways(self):
        """Test all available gateways and show results"""
        def test_gateways_thread():
            results = []
            
            # Test local gateways
            local_gateways = ["http://127.0.0.1:8080", "http://localhost:8080"]
            for gateway in local_gateways:
                try:
                    is_available = self.test_gateway_availability(gateway)
                    status = "✅ Available" if is_available else "❌ Not available"
                    results.append(f"Local: {gateway} - {status}")
                except Exception as e:
                    results.append(f"Local: {gateway} - ❌ Error: {e}")
            
            # Test public gateways
            public_gateways = ["https://ipfs.io", "https://gateway.ipfs.io", "https://cloudflare-ipfs.com"]
            for gateway in public_gateways:
                try:
                    is_available = self.test_gateway_availability(gateway)
                    status = "✅ Available" if is_available else "❌ Not available"
                    results.append(f"Public: {gateway} - {status}")
                except Exception as e:
                    results.append(f"Public: {gateway} - ❌ Error: {e}")
            
            # Show results
            def show_results():
                result_text = "IPFS Gateway Test Results:\n\n" + "\n".join(results)
                messagebox.showinfo("Gateway Test Results", result_text)
            
            self.root.after(0, show_results)
        
        # Show testing message
        messagebox.showinfo("Testing Gateways", "Testing gateways... This may take a few seconds.")
        self.run_threaded(test_gateways_thread)

    def save_gateway_settings(self):
        """Save gateway preferences to config"""
        try:
            self.config.set("gateway_preference", self.gateway_preference_var.get())
            self.config.set("custom_gateway", self.custom_gateway_var.get())
            messagebox.showinfo("Success", "Gateway settings saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save gateway settings: {e}")

    def save_api_keys(self):
        try:
            keys_to_save = {api_id: var.get() for api_id, var in self.api_key_vars.items() if var.get()}
            self.key_manager.save_keys(keys_to_save)
            self.fetcher.api_keys = self.key_manager.load_keys()
            messagebox.showinfo("Success", "API Keys saved securely.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save API keys: {e}")


    def save_api_keys(self):
        try:
            keys_to_save = {api_id: var.get() for api_id, var in self.api_key_vars.items() if var.get()}
            self.key_manager.save_keys(keys_to_save)
            self.fetcher.api_keys = self.key_manager.load_keys()
            messagebox.showinfo("Success", "API Keys saved securely.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save API keys: {e}")

    # Add this to your UnifiedNFTApp class in main_app.py

    def create_main_interface(self):
        """Create the main interface with proper error handling"""
        try:
            self.notebook = ttk.Notebook(self.root)
            self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            self.create_collector_tab()
            self.create_viewer_tab()
            self.create_creator_tab()  # This comes from NFTCreatorMixin
            self.create_slideshow_tab()  # New slideshow tab
            self.create_settings_tab()
        except Exception as e:
            messagebox.showerror("UI Error", f"Failed to create interface: {e}")
            self.root.destroy()

    def create_slideshow_tab(self):
        """Create the slideshow viewer tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🎬 Slideshow")
        
        # Slideshow state
        self.slideshow_playing = False
        self.slideshow_index = 0
        self.slideshow_timer = None
        self.slideshow_interval = 5000  # 5 seconds
        
        # Main slideshow frame
        slideshow_frame = ttk.Frame(tab)
        slideshow_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        slideshow_frame.rowconfigure(1, weight=1)  # Image area expandable
        slideshow_frame.columnconfigure(0, weight=1)
        
        # Controls frame
        controls_frame = ttk.Frame(slideshow_frame)
        controls_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        controls_frame.columnconfigure(2, weight=1)  # Spacer column
        
        # Playback controls
        self.slideshow_play_btn = ttk.Button(controls_frame, text="▶️ Play", 
                                           command=self.toggle_slideshow)
        self.slideshow_play_btn.grid(row=0, column=0, padx=5)
        
        ttk.Button(controls_frame, text="⏮️ Previous", 
                  command=self.slideshow_previous).grid(row=0, column=1, padx=5)
        
        ttk.Button(controls_frame, text="⏭️ Next", 
                  command=self.slideshow_next).grid(row=0, column=3, padx=5)
        
        ttk.Button(controls_frame, text="🔀 Shuffle", 
                  command=self.slideshow_shuffle).grid(row=0, column=4, padx=5)
        
        ttk.Button(controls_frame, text="🖼️ Fullscreen", 
                  command=self.slideshow_fullscreen).grid(row=0, column=5, padx=5)
        
        # Interval setting
        interval_frame = ttk.Frame(controls_frame)
        interval_frame.grid(row=0, column=6, padx=10)
        ttk.Label(interval_frame, text="Interval:").pack(side=tk.LEFT)
        
        self.slideshow_interval_var = tk.StringVar(value="5")
        interval_combo = ttk.Combobox(interval_frame, textvariable=self.slideshow_interval_var,
                                    values=["2", "3", "5", "10", "15", "30"], width=5, state="readonly")
        interval_combo.pack(side=tk.LEFT, padx=2)
        interval_combo.bind("<<ComboboxSelected>>", self.update_slideshow_interval)
        ttk.Label(interval_frame, text="sec").pack(side=tk.LEFT)
        
        # Progress and status
        progress_frame = ttk.Frame(slideshow_frame)
        progress_frame.grid(row=1, column=0, sticky="ew", pady=5)
        progress_frame.columnconfigure(1, weight=1)
        
        self.slideshow_status_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.slideshow_status_var).grid(row=0, column=0, sticky="w")
        
        self.slideshow_progress_var = tk.StringVar(value="0 / 0")
        ttk.Label(progress_frame, textvariable=self.slideshow_progress_var).grid(row=0, column=2, sticky="e")
        
        # Image display area
        image_frame = ttk.LabelFrame(slideshow_frame, text="NFT Display", padding=10)
        image_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        image_frame.rowconfigure(0, weight=1)
        image_frame.columnconfigure(0, weight=1)
        
        # Image label with dark background
        self.slideshow_image_label = tk.Label(image_frame, text="Select 'Play' to start slideshow", 
                                            bg="black", fg="white", font=("Arial", 16))
        self.slideshow_image_label.grid(row=0, column=0, sticky="nsew")
        
        # NFT info display
        info_frame = ttk.LabelFrame(slideshow_frame, text="Current NFT Info", padding=10)
        info_frame.grid(row=3, column=0, sticky="ew")
        info_frame.columnconfigure(1, weight=1)
        
        # NFT title and details
        ttk.Label(info_frame, text="Title:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.slideshow_title_var = tk.StringVar(value="No NFT selected")
        ttk.Label(info_frame, textvariable=self.slideshow_title_var, font=("Arial", 12, "bold")).grid(row=0, column=1, sticky="w")
        
        ttk.Label(info_frame, text="Collection:").grid(row=1, column=0, sticky="w", padx=(0, 5))
        self.slideshow_collection_var = tk.StringVar(value="")
        ttk.Label(info_frame, textvariable=self.slideshow_collection_var).grid(row=1, column=1, sticky="w")
        
        ttk.Label(info_frame, text="Source:").grid(row=2, column=0, sticky="w", padx=(0, 5))
        self.slideshow_source_var = tk.StringVar(value="")
        ttk.Label(info_frame, textvariable=self.slideshow_source_var).grid(row=2, column=1, sticky="w")
        
        # Keyboard bindings for slideshow tab
        self.root.bind('<Key>', self.on_slideshow_key)

    def on_slideshow_key(self, event):
        """Handle keyboard shortcuts for slideshow (when tab is active)"""
        # Only handle keys when slideshow tab is active
        current_tab = self.notebook.tab(self.notebook.select(), "text")
        if "Slideshow" not in current_tab:
            return
            
        key = event.keysym.lower()
        if key == 'space':
            self.toggle_slideshow()
        elif key == 'right':
            self.slideshow_next()
        elif key == 'left':
            self.slideshow_previous()
        elif key == 'r':
            self.slideshow_shuffle()

    def toggle_slideshow(self):
        """Toggle slideshow play/pause"""
        if not self.nfts:
            messagebox.showinfo("No NFTs", "No NFTs available for slideshow. Add some NFTs first!")
            return
            
        if self.slideshow_playing:
            self.stop_slideshow()
        else:
            self.start_slideshow()

    def start_slideshow(self):
        """Start the slideshow"""
        if not self.nfts:
            return
            
        self.slideshow_playing = True
        self.slideshow_play_btn.config(text="⏸️ Pause")
        self.slideshow_status_var.set("Playing")
        
        # Show first NFT if none selected
        if self.slideshow_index >= len(self.nfts):
            self.slideshow_index = 0
            
        self.show_slideshow_nft()
        self.schedule_next_slide()

    def stop_slideshow(self):
        """Stop the slideshow"""
        self.slideshow_playing = False
        self.slideshow_play_btn.config(text="▶️ Play")
        self.slideshow_status_var.set("Paused")
        
        if self.slideshow_timer:
            self.root.after_cancel(self.slideshow_timer)
            self.slideshow_timer = None

    def slideshow_next(self):
        """Show next NFT in slideshow"""
        if not self.nfts:
            return
            
        self.slideshow_index = (self.slideshow_index + 1) % len(self.nfts)
        self.show_slideshow_nft()

    def slideshow_previous(self):
        """Show previous NFT in slideshow"""
        if not self.nfts:
            return
            
        self.slideshow_index = (self.slideshow_index - 1) % len(self.nfts)
        self.show_slideshow_nft()

    def slideshow_shuffle(self):
        """Shuffle the NFT order for slideshow"""
        if not self.nfts:
            return
            
        import random
        current_nft = None
        if self.nfts and 0 <= self.slideshow_index < len(self.nfts):
            current_nft = self.nfts[self.slideshow_index]
            
        random.shuffle(self.nfts)
        
        # Try to find current NFT in new order
        if current_nft:
            try:
                self.slideshow_index = self.nfts.index(current_nft)
            except ValueError:
                self.slideshow_index = 0
        else:
            self.slideshow_index = 0
            
        self.slideshow_status_var.set("Shuffled")
        self.show_slideshow_nft()

    def update_slideshow_interval(self, event=None):
        """Update slideshow interval from combo box"""
        try:
            self.slideshow_interval = int(self.slideshow_interval_var.get()) * 1000
            print(f"Slideshow interval updated to {self.slideshow_interval}ms")
        except ValueError:
            self.slideshow_interval = 5000

    def schedule_next_slide(self):
        """Schedule the next slide"""
        if self.slideshow_playing:
            self.slideshow_timer = self.root.after(self.slideshow_interval, self.auto_next_slide)

    def auto_next_slide(self):
        """Automatically advance to next slide"""
        if self.slideshow_playing:
            self.slideshow_next()
            self.schedule_next_slide()

    def show_slideshow_nft(self):
        """Display current NFT in slideshow"""
        if not self.nfts or self.slideshow_index >= len(self.nfts):
            return
            
        nft = self.nfts[self.slideshow_index]
        
        # Update progress
        self.slideshow_progress_var.set(f"{self.slideshow_index + 1} / {len(self.nfts)}")
        
        # Update NFT info
        self.slideshow_title_var.set(nft.get('title', 'Unknown NFT'))
        self.slideshow_collection_var.set(nft.get('contract_address', 'Unknown')[-8:] if nft.get('contract_address') else 'Unknown')
        self.slideshow_source_var.set(nft.get('source_api', 'Unknown'))
        
        # Load image
        image_url = nft.get('image_url', '')
        if not image_url:
            # Try to get from media array
            media = nft.get('media', [])
            if media and len(media) > 0:
                image_url = media[0].get('gateway', '')
        
        if image_url:
            image_url = self.convert_ipfs_url_to_gateway(image_url)
            self.run_threaded(self._load_slideshow_image, image_url)
        else:
            self.slideshow_image_label.config(image='', text="No image available", 
                                            bg="black", fg="white")
            self.slideshow_image_label.image = None

    def _load_slideshow_image(self, url):
        """Load image for slideshow in background thread"""
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                # Load image
                img = Image.open(io.BytesIO(response.content))
                
                # Get display area size (approximate)
                display_width = 800
                display_height = 400
                
                # Resize image to fit display while maintaining aspect ratio
                img.thumbnail((display_width, display_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                def update_ui():
                    self.slideshow_image_label.config(image=photo, text="", bg="black")
                    self.slideshow_image_label.image = photo  # Keep reference
                
                self.root.after(0, update_ui)
            else:
                def show_error():
                    self.slideshow_image_label.config(image='', 
                                                    text=f"Failed to load image\n(HTTP {response.status_code})",
                                                    bg="black", fg="red")
                    self.slideshow_image_label.image = None
                self.root.after(0, show_error)
                
        except Exception as e:
            print(f"Failed to load slideshow image {url}: {e}")
            def show_error():
                self.slideshow_image_label.config(image='', 
                                                text=f"Image load error:\n{str(e)[:50]}...",
                                                bg="black", fg="red")
                self.slideshow_image_label.image = None
            self.root.after(0, show_error)

    def slideshow_fullscreen(self):
        """Open slideshow in fullscreen window"""
        if not self.nfts:
            messagebox.showinfo("No NFTs", "No NFTs available for fullscreen slideshow.")
            return
            
        # Create fullscreen slideshow window
        fullscreen_window = tk.Toplevel(self.root)
        fullscreen_window.title("NFT Slideshow - Fullscreen")
        fullscreen_window.configure(bg='black')
        fullscreen_window.attributes('-fullscreen', True)
        
        # Fullscreen slideshow state
        fs_playing = tk.BooleanVar(value=True)
        fs_index = tk.IntVar(value=self.slideshow_index)
        fs_timer = None
        
        # Image label
        fs_image_label = tk.Label(fullscreen_window, bg='black')
        fs_image_label.pack(fill=tk.BOTH, expand=True)
        
        # Info overlay
        info_frame = tk.Frame(fullscreen_window, bg='black')
        info_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        fs_title_label = tk.Label(info_frame, text="", fg='white', bg='black', 
                                font=('Arial', 24, 'bold'))
        fs_title_label.pack(pady=10)
        
        def show_fs_nft():
            if fs_index.get() >= len(self.nfts):
                return
                
            nft = self.nfts[fs_index.get()]
            fs_title_label.config(text=f"{nft.get('title', 'Unknown NFT')} ({fs_index.get() + 1}/{len(self.nfts)})")
            
            # Load image
            image_url = nft.get('image_url', '')
            if not image_url:
                media = nft.get('media', [])
                if media:
                    image_url = media[0].get('gateway', '')
            
            if image_url:
                image_url = self.convert_ipfs_url_to_gateway(image_url)
                
                def load_fs_image():
                    try:
                        response = requests.get(image_url, timeout=15)
                        if response.status_code == 200:
                            img = Image.open(io.BytesIO(response.content))
                            
                            # Get screen size
                            screen_width = fullscreen_window.winfo_screenwidth()
                            screen_height = fullscreen_window.winfo_screenheight() - 100
                            
                            img.thumbnail((screen_width, screen_height), Image.Resampling.LANCZOS)
                            photo = ImageTk.PhotoImage(img)
                            
                            def update_fs_ui():
                                fs_image_label.config(image=photo)
                                fs_image_label.image = photo
                            
                            fullscreen_window.after(0, update_fs_ui)
                    except Exception as e:
                        print(f"Fullscreen image load error: {e}")
                
                threading.Thread(target=load_fs_image, daemon=True).start()
        
        def fs_next():
            fs_index.set((fs_index.get() + 1) % len(self.nfts))
            show_fs_nft()
        
        def fs_previous():
            fs_index.set((fs_index.get() - 1) % len(self.nfts))
            show_fs_nft()
        
        def fs_toggle():
            fs_playing.set(not fs_playing.get())
            if fs_playing.get():
                schedule_fs_next()
        
        def schedule_fs_next():
            nonlocal fs_timer
            if fs_playing.get():
                fs_timer = fullscreen_window.after(self.slideshow_interval, auto_fs_next)
        
        def auto_fs_next():
            if fs_playing.get():
                fs_next()
                schedule_fs_next()
        
        def on_fs_key(event):
            key = event.keysym.lower()
            if key == 'escape' or key == 'q':
                fullscreen_window.destroy()
            elif key == 'space':
                fs_toggle()
            elif key == 'right':
                fs_next()
            elif key == 'left':
                fs_previous()
        
        fullscreen_window.bind('<Key>', on_fs_key)
        fullscreen_window.focus_set()
        
        # Start fullscreen slideshow
        show_fs_nft()
        if fs_playing.get():
            schedule_fs_next()

# --- Main Execution ---
def main():
    """Main function with proper error handling"""
    try:
        # Create main window
        main_root = tk.Tk()
        
        # Create application
        app = UnifiedNFTApp(main_root)
        
        # Start the GUI event loop
        main_root.mainloop()
        
    except Exception as e:
        # Show error in a simple dialog if possible
        try:
            import tkinter.messagebox as mb
            mb.showerror("Fatal Error", f"Application failed to start:\n{e}")
        except:
            print(f"FATAL ERROR: {e}")
        
        # Exit with error code
        exit(1)

if __name__ == "__main__":
    main()