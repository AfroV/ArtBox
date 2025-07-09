#!/usr/bin/env python3
"""
NFT Creator Functionality - Part 1: UI Setup and Single File Upload
Contains Creator tab UI and single file upload functionality
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import time
import tempfile
from pathlib import Path
import requests

class NFTCreatorMixin:
    """Mixin class containing all Creator tab functionality"""
    
    def create_creator_tab(self):
        """Create the main creator tab with sub-tabs"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="✨ Creator")
        
        # Create notebook for different creation modes
        creator_notebook = ttk.Notebook(tab)
        creator_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Single File Upload
        self.create_single_upload_tab(creator_notebook)
        
        # Tab 2: NFT Metadata + Image Upload
        self.create_nft_upload_tab(creator_notebook)
        
        # Tab 3: Manual Hash Entry
        self.create_manual_hash_tab(creator_notebook)
    
    def create_single_upload_tab(self, parent):
        """Create tab for single file uploads"""
        tab = ttk.Frame(parent)
        parent.add(tab, text="📁 Single File")
        
        # Header
        ttk.Label(tab, text="Upload Single File to IPFS", font=("Arial", 14)).pack(pady=10)
        
        # File selection frame
        file_frame = ttk.Frame(tab)
        file_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Selected file display
        self.selected_file_var = tk.StringVar(value="No file selected")
        ttk.Label(file_frame, text="Selected file:").pack(anchor=tk.W)
        file_label = ttk.Label(file_frame, textvariable=self.selected_file_var, 
                              background="white", relief="sunken", padding=5)
        file_label.pack(fill=tk.X, pady=5)
        
        # Buttons frame
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        # Select file button
        self.select_btn = ttk.Button(btn_frame, text="📁 Select File", command=self.select_file)
        self.select_btn.pack(side=tk.LEFT, padx=5)
        
        # Upload button (initially disabled)
        self.upload_btn = ttk.Button(btn_frame, text="📤 Upload to IPFS", 
                                   command=self.upload_file, state=tk.DISABLED)
        self.upload_btn.pack(side=tk.LEFT, padx=5)
        
        # Clear selection button
        clear_btn = ttk.Button(btn_frame, text="🗑️ Clear", command=self.clear_selection)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Status and progress
        status_frame = ttk.Frame(tab)
        status_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.creator_status_var = tk.StringVar(value="Ready to create. Select a file to upload.")
        ttk.Label(status_frame, textvariable=self.creator_status_var).pack(pady=5)
        
        # Progress bar (initially hidden)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, 
                                          mode='indeterminate')
        
        # File info frame
        info_frame = ttk.LabelFrame(tab, text="File Information", padding=10)
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.file_info_text = scrolledtext.ScrolledText(info_frame, height=8, wrap=tk.WORD)
        self.file_info_text.pack(fill=tk.X)
        self.file_info_text.insert(tk.END, "Select a file to see information...")
        self.file_info_text.config(state=tk.DISABLED)
        
        # Store selected file path
        self.selected_file_path = None
    
    def create_nft_upload_tab(self, parent):
        """Create tab for NFT (metadata + image) uploads"""
        tab = ttk.Frame(parent)
        parent.add(tab, text="🖼️ NFT Creation")
        
        # Header
        ttk.Label(tab, text="Create NFT from Metadata + Image", font=("Arial", 14)).pack(pady=10)
        
        # Instructions
        instructions = """Upload both a metadata JSON file and its corresponding image file.
The system will upload both to IPFS and add the NFT to your collection."""
        ttk.Label(tab, text=instructions, justify=tk.CENTER, wraplength=600).pack(pady=5)
        
        # Main frame
        main_frame = ttk.Frame(tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Metadata file section
        metadata_frame = ttk.LabelFrame(main_frame, text="Metadata File (.json)", padding=10)
        metadata_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.metadata_file_var = tk.StringVar(value="No metadata file selected")
        ttk.Label(metadata_frame, textvariable=self.metadata_file_var, 
                 background="white", relief="sunken", padding=5).pack(fill=tk.X, pady=5)
        
        ttk.Button(metadata_frame, text="📄 Select Metadata", 
                  command=self.select_metadata_file).pack(pady=5)
        
        # Image file section
        image_frame = ttk.LabelFrame(main_frame, text="Image File", padding=10)
        image_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        self.image_file_var = tk.StringVar(value="No image file selected")
        ttk.Label(image_frame, textvariable=self.image_file_var,
                 background="white", relief="sunken", padding=5).pack(fill=tk.X, pady=5)
        
        ttk.Button(image_frame, text="🖼️ Select Image", 
                  command=self.select_image_file).pack(pady=5)
        
        # Action buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.nft_upload_btn = ttk.Button(action_frame, text="🚀 Create NFT", 
                                        command=self.upload_nft, state=tk.DISABLED)
        self.nft_upload_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(action_frame, text="🗑️ Clear All", 
                  command=self.clear_nft_selection).pack(side=tk.LEFT, padx=5)
        
        # Status
        self.nft_status_var = tk.StringVar(value="Select both metadata and image files to create NFT")
        ttk.Label(main_frame, textvariable=self.nft_status_var).grid(row=2, column=0, columnspan=2, pady=5)
        
        # Progress bar for NFT creation
        self.nft_progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        
        # NFT info display
        nft_info_frame = ttk.LabelFrame(main_frame, text="NFT Information", padding=10)
        nft_info_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=10)
        main_frame.rowconfigure(3, weight=1)
        
        self.nft_info_text = scrolledtext.ScrolledText(nft_info_frame, height=10, wrap=tk.WORD)
        self.nft_info_text.pack(fill=tk.BOTH, expand=True)
        self.nft_info_text.insert(tk.END, "Select metadata and image files to see NFT information...")
        self.nft_info_text.config(state=tk.DISABLED)
        
        # Store file paths
        self.metadata_file_path = None
        self.image_file_path = None
    
    def create_manual_hash_tab(self, parent):
        """Create tab for manual hash entry"""
        tab = ttk.Frame(parent)
        parent.add(tab, text="🔗 Add by Hash")
        
        # Header
        ttk.Label(tab, text="Add NFT by IPFS Hashes", font=("Arial", 14)).pack(pady=10)
        
        instructions = """If you already have IPFS hashes for your metadata and image,
enter them below to add the NFT to your collection."""
        ttk.Label(tab, text=instructions, justify=tk.CENTER, wraplength=600).pack(pady=5)
        
        # Input frame
        input_frame = ttk.LabelFrame(tab, text="IPFS Hashes", padding=20)
        input_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Metadata hash
        ttk.Label(input_frame, text="Metadata Hash (JSON):").pack(anchor=tk.W)
        self.metadata_hash_var = tk.StringVar()
        metadata_hash_entry = ttk.Entry(input_frame, textvariable=self.metadata_hash_var, width=80)
        metadata_hash_entry.pack(fill=tk.X, pady=5)
        self.setup_clipboard_bindings(metadata_hash_entry)
        
        # Image hash
        ttk.Label(input_frame, text="Image Hash:").pack(anchor=tk.W, pady=(10,0))
        self.image_hash_var = tk.StringVar()
        image_hash_entry = ttk.Entry(input_frame, textvariable=self.image_hash_var, width=80)
        image_hash_entry.pack(fill=tk.X, pady=5)
        self.setup_clipboard_bindings(image_hash_entry)
        
        # Add preview update bindings
        self.metadata_hash_var.trace('w', self.update_hash_preview)
        self.image_hash_var.trace('w', self.update_hash_preview)
        
        # Buttons
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="📋 Paste Metadata Hash", 
                  command=lambda: self.paste_to_var(self.metadata_hash_var)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📋 Paste Image Hash", 
                  command=lambda: self.paste_to_var(self.image_hash_var)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✅ Add to Collection", 
                  command=self.add_nft_by_hash).pack(side=tk.LEFT, padx=20)
        ttk.Button(btn_frame, text="🗑️ Clear", 
                  command=self.clear_hash_fields).pack(side=tk.LEFT, padx=5)
        
        # Status
        self.hash_status_var = tk.StringVar(value="Enter IPFS hashes to add NFT to collection")
        ttk.Label(input_frame, textvariable=self.hash_status_var).pack(pady=5)
        
        # Preview frame
        preview_frame = ttk.LabelFrame(tab, text="NFT Preview & Gateway Info", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.hash_preview_text = scrolledtext.ScrolledText(preview_frame, height=12, wrap=tk.WORD)
        self.hash_preview_text.pack(fill=tk.BOTH, expand=True)
        self.hash_preview_text.insert(tk.END, "Enter hashes above to preview NFT metadata and gateway selection...")
        self.hash_preview_text.config(state=tk.DISABLED)

    def update_hash_preview(self, *args):
        """Update the preview when hash values change"""
        metadata_hash = self.metadata_hash_var.get().strip()
        image_hash = self.image_hash_var.get().strip()
        
        if not metadata_hash and not image_hash:
            preview_text = "Enter hashes above to preview NFT metadata and gateway selection..."
        else:
            preview_text = "NFT PREVIEW\n" + "="*50 + "\n\n"
            
            if metadata_hash:
                # Show which gateway will be used for metadata
                metadata_url = self.convert_ipfs_url_to_gateway(f"ipfs://{metadata_hash}")
                gateway_type = "Local" if "127.0.0.1" in metadata_url else "Public"
                
                preview_text += f"METADATA:\n"
                preview_text += f"Hash: {metadata_hash}\n"
                preview_text += f"Gateway: {gateway_type} ({metadata_url})\n"
                preview_text += f"IPFS URL: ipfs://{metadata_hash}\n\n"
            
            if image_hash:
                # Show which gateway will be used for image
                image_url = self.convert_ipfs_url_to_gateway(f"ipfs://{image_hash}")
                gateway_type = "Local" if "127.0.0.1" in image_url else "Public"
                
                preview_text += f"IMAGE:\n"
                preview_text += f"Hash: {image_hash}\n"
                preview_text += f"Gateway: {gateway_type} ({image_url})\n"
                preview_text += f"IPFS URL: ipfs://{image_hash}\n\n"
            
            # Show current gateway settings
            gateway_preference = self.config.get("gateway_preference", "auto")
            custom_gateway = self.config.get("custom_gateway", "")
            ipfs_status = "Connected" if self.ipfs.is_connected else "Disconnected"
            
            preview_text += f"GATEWAY SETTINGS:\n"
            preview_text += f"Preference: {gateway_preference}\n"
            preview_text += f"Local IPFS: {ipfs_status}\n"
            if custom_gateway:
                preview_text += f"Custom Gateway: {custom_gateway}\n"
            
            if metadata_hash and image_hash:
                preview_text += f"\n✅ Ready to add NFT with smart gateway selection!"
            elif metadata_hash or image_hash:
                preview_text += f"\n⚠️ Enter both hashes to add NFT to collection"
        
        # Update preview display
        self.hash_preview_text.config(state=tk.NORMAL)
        self.hash_preview_text.delete(1.0, tk.END)
        self.hash_preview_text.insert(tk.END, preview_text)
        self.hash_preview_text.config(state=tk.DISABLED)
    # --- Single File Upload Methods ---
    def select_file(self):
        """Select a file using file dialog"""
        try:
            # Define supported file types
            filetypes = [
                ("All supported", "*.jpg;*.jpeg;*.png;*.gif;*.bmp;*.webp;*.pdf;*.txt;*.json;*.mp4;*.mp3"),
                ("Image files", "*.jpg;*.jpeg;*.png;*.gif;*.bmp;*.webp"),
                ("Document files", "*.pdf;*.txt;*.json;*.doc;*.docx"),
                ("Media files", "*.mp4;*.mp3;*.wav;*.avi"),
                ("All files", "*.*")
            ]
            
            filepath = filedialog.askopenfilename(
                title="Select file to upload to IPFS",
                filetypes=filetypes,
                initialdir=Path.home()
            )
            
            if filepath:
                self.selected_file_path = Path(filepath)
                self.selected_file_var.set(f"{self.selected_file_path.name}")
                self.upload_btn.config(state=tk.NORMAL)
                self.show_file_info()
                self.creator_status_var.set(f"File selected: {self.selected_file_path.name}")
                print(f"Selected file: {filepath}")
            else:
                print("No file selected")
                
        except Exception as e:
            error_msg = f"Error selecting file: {str(e)}"
            print(error_msg)
            messagebox.showerror("File Selection Error", error_msg)
    
    def show_file_info(self):
        """Display information about the selected file"""
        if not self.selected_file_path or not self.selected_file_path.exists():
            return
            
        try:
            # Get file statistics
            stat = self.selected_file_path.stat()
            file_size = stat.st_size
            
            # Format file size
            if file_size < 1024:
                size_str = f"{file_size} bytes"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            elif file_size < 1024 * 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
            else:
                size_str = f"{file_size / (1024 * 1024 * 1024):.1f} GB"
            
            # Prepare file info
            info_text = f"""File: {self.selected_file_path.name}
Path: {self.selected_file_path}
Size: {size_str}
Type: {self.selected_file_path.suffix.upper() or 'No extension'}
Modified: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))}

Ready to upload to IPFS. Click 'Upload to IPFS' to proceed.
"""
            
            # Update file info display
            self.file_info_text.config(state=tk.NORMAL)
            self.file_info_text.delete(1.0, tk.END)
            self.file_info_text.insert(tk.END, info_text)
            self.file_info_text.config(state=tk.DISABLED)
            
        except Exception as e:
            print(f"Error getting file info: {e}")
    
    def clear_selection(self):
        """Clear the current file selection"""
        self.selected_file_path = None
        self.selected_file_var.set("No file selected")
        self.upload_btn.config(state=tk.DISABLED)
        self.creator_status_var.set("Ready to create. Select a file to upload.")
        
        # Clear file info
        self.file_info_text.config(state=tk.NORMAL)
        self.file_info_text.delete(1.0, tk.END)
        self.file_info_text.insert(tk.END, "Select a file to see information...")
        self.file_info_text.config(state=tk.DISABLED)
        
    def upload_file(self):
        """Upload the selected file to IPFS"""
        if not self.selected_file_path or not self.selected_file_path.exists():
            messagebox.showerror("Error", "Please select a valid file first.")
            return
        
        # Check IPFS connection
        if not self.ipfs.check_status():
            result = messagebox.askyesno("IPFS Not Connected", 
                                       "IPFS is not running. Do you want to continue anyway?")
            if not result:
                return
        
        try:
            self.upload_btn.config(state=tk.DISABLED)
            self.select_btn.config(state=tk.DISABLED)
            
            # Show progress bar
            self.progress_bar.pack(fill=tk.X, pady=5)
            self.progress_bar.start()
            
            self.creator_status_var.set(f"Uploading {self.selected_file_path.name} to IPFS...")
            self.run_threaded(self._upload_file_thread, self.selected_file_path)
            
        except Exception as e:
            error_msg = f"Failed to start upload: {str(e)}"
            print(error_msg)
            messagebox.showerror("Upload Error", error_msg)
            self._reset_upload_ui()
        
    def _upload_file_thread(self, filepath: Path):
        """Upload file in background thread with automatic pinning"""
        try:
            print(f"Starting file upload with automatic pinning: {filepath}")
            
            # Step 1: Upload to IPFS
            self.root.after(0, lambda: self.creator_status_var.set("Step 1/2: Uploading file to IPFS..."))
            ipfs_hash = self.ipfs.add_file(filepath)
            
            if ipfs_hash:
                print(f"Upload successful. IPFS hash: {ipfs_hash}")
                
                # Step 2: Pin the file
                file_pinned = False
                self.root.after(0, lambda: self.creator_status_var.set("Step 2/2: Pinning file to local IPFS..."))
                try:
                    file_pinned = self.ipfs.pin_hash(ipfs_hash)
                    if file_pinned:
                        print(f"✅ File pinned locally: {ipfs_hash}")
                    else:
                        print(f"⚠️ Failed to pin file: {ipfs_hash}")
                except Exception as e:
                    print(f"⚠️ Error pinning file: {e}")
                
                # Update UI with detailed status
                pin_status = "and pinned locally" if file_pinned else "but not pinned locally"
                success_msg = f"✅ Upload complete!\nIPFS Hash: {ipfs_hash}\nFile uploaded {pin_status}."
                
                def update_success():
                    status_text = "Upload and pinning successful!" if file_pinned else "Upload successful!"
                    self.creator_status_var.set(status_text)
                    
                    # Update file info with detailed status
                    pinning_status = "✅ File pinned locally" if file_pinned else "⚠️ File uploaded but not pinned"
                    
                    info_text = f"""UPLOAD SUCCESSFUL ✅

File: {filepath.name}
IPFS Hash: {ipfs_hash}
Storage Status: {pinning_status}
Gateway URL: {self.ipfs.ipfs_gateway}ipfs/{ipfs_hash}

You can access this file using the IPFS hash above.
{'' if file_pinned else 'Note: File was not pinned locally. It may not be available offline.'}
"""
                    self.file_info_text.config(state=tk.NORMAL)
                    self.file_info_text.delete(1.0, tk.END)
                    self.file_info_text.insert(tk.END, info_text)
                    self.file_info_text.config(state=tk.DISABLED)
                    
                    messagebox.showinfo("Upload Successful", success_msg)
                    
                self.root.after(0, update_success)
                
            else:
                error_msg = "Upload failed - IPFS returned no hash"
                print(error_msg)
                
                def update_error():
                    self.creator_status_var.set("Upload failed!")
                    messagebox.showerror("Upload Failed", error_msg)
                    
                self.root.after(0, update_error)
                
        except Exception as e:
            error_msg = f"Upload error: {str(e)}"
            print(error_msg)
            
            def update_error():
                self.creator_status_var.set("Upload failed!")
                messagebox.showerror("Upload Error", error_msg)
                
            self.root.after(0, update_error)
        
        # Reset UI
        self.root.after(0, self._reset_upload_ui)

    def _reset_upload_ui(self):
        """Reset upload UI elements"""
        self.upload_btn.config(state=tk.NORMAL if self.selected_file_path else tk.DISABLED)
        self.select_btn.config(state=tk.NORMAL)
        self.progress_bar.stop()
        self.progress_bar.pack_forget()