#!/usr/bin/env python3
"""
NFT Creator Functionality - Part 2: NFT Creation and Hash Entry
Contains NFT creation workflow and manual hash entry functionality
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import time
import tempfile
from pathlib import Path
import requests

class NFTCreatorAdvancedMixin:
    """Advanced NFT creation functionality - to be combined with NFTCreatorMixin"""
    
    # --- NFT Upload Methods ---
    def select_metadata_file(self):
        """Select metadata JSON file"""
        try:
            filepath = tk.filedialog.askopenfilename(
                title="Select NFT Metadata File",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialdir=Path.home()
            )
            
            if filepath:
                self.metadata_file_path = Path(filepath)
                self.metadata_file_var.set(self.metadata_file_path.name)
                self.check_nft_ready()
                self.update_nft_info()
                print(f"Selected metadata file: {filepath}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error selecting metadata file: {e}")
    
    def select_image_file(self):
        """Select image file"""
        try:
            filepath = tk.filedialog.askopenfilename(
                title="Select NFT Image File",
                filetypes=[
                    ("Image files", "*.jpg;*.jpeg;*.png;*.gif;*.bmp;*.webp"),
                    ("All files", "*.*")
                ],
                initialdir=Path.home()
            )
            
            if filepath:
                self.image_file_path = Path(filepath)
                self.image_file_var.set(self.image_file_path.name)
                self.check_nft_ready()
                self.update_nft_info()
                print(f"Selected image file: {filepath}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error selecting image file: {e}")
    
    def check_nft_ready(self):
        """Check if both files are selected and enable upload button"""
        if self.metadata_file_path and self.image_file_path:
            self.nft_upload_btn.config(state=tk.NORMAL)
            self.nft_status_var.set("Ready to create NFT! Click 'Create NFT' to upload both files.")
        else:
            self.nft_upload_btn.config(state=tk.DISABLED)
            missing = []
            if not self.metadata_file_path:
                missing.append("metadata")
            if not self.image_file_path:
                missing.append("image")
            self.nft_status_var.set(f"Still need: {', '.join(missing)} file(s)")
    
    def update_nft_info(self):
        """Update NFT information display"""
        info_text = "NFT CREATION PREVIEW\n" + "="*50 + "\n\n"
        
        # Metadata info
        if self.metadata_file_path and self.metadata_file_path.exists():
            try:
                with open(self.metadata_file_path, 'r') as f:
                    metadata = json.load(f)
                
                info_text += f"METADATA FILE: {self.metadata_file_path.name}\n"
                info_text += f"Name: {metadata.get('name', 'Unknown')}\n"
                info_text += f"Description: {metadata.get('description', 'No description')}\n"
                
                if 'attributes' in metadata:
                    info_text += f"Attributes: {len(metadata['attributes'])} traits\n"
                    for attr in metadata['attributes'][:3]:  # Show first 3 attributes
                        info_text += f"  - {attr.get('trait_type', '')}: {attr.get('value', '')}\n"
                    if len(metadata['attributes']) > 3:
                        info_text += f"  ... and {len(metadata['attributes']) - 3} more\n"
                
                info_text += "\n"
                
            except Exception as e:
                info_text += f"ERROR reading metadata: {e}\n\n"
        
        # Image info
        if self.image_file_path and self.image_file_path.exists():
            stat = self.image_file_path.stat()
            size_kb = stat.st_size / 1024
            info_text += f"IMAGE FILE: {self.image_file_path.name}\n"
            info_text += f"Size: {size_kb:.1f} KB\n"
            info_text += f"Type: {self.image_file_path.suffix.upper()}\n\n"
        
        # Next steps
        if self.metadata_file_path and self.image_file_path:
            info_text += "READY TO CREATE NFT!\n\n"
            info_text += "What will happen:\n"
            info_text += "1. Upload image to IPFS\n"
            info_text += "2. Update metadata with image IPFS hash\n"
            info_text += "3. Upload metadata to IPFS\n"
            info_text += "4. Add NFT to your collection\n"
        
        # Update display
        self.nft_info_text.config(state=tk.NORMAL)
        self.nft_info_text.delete(1.0, tk.END)
        self.nft_info_text.insert(tk.END, info_text)
        self.nft_info_text.config(state=tk.DISABLED)
    
    def clear_nft_selection(self):
        """Clear NFT file selections"""
        self.metadata_file_path = None
        self.image_file_path = None
        self.metadata_file_var.set("No metadata file selected")
        self.image_file_var.set("No image file selected")
        self.nft_upload_btn.config(state=tk.DISABLED)
        self.nft_status_var.set("Select both metadata and image files to create NFT")
        
        # Clear info display
        self.nft_info_text.config(state=tk.NORMAL)
        self.nft_info_text.delete(1.0, tk.END)
        self.nft_info_text.insert(tk.END, "Select metadata and image files to see NFT information...")
        self.nft_info_text.config(state=tk.DISABLED)
    
    def upload_nft(self):
        """Upload NFT (metadata + image) to IPFS and add to collection"""
        if not (self.metadata_file_path and self.image_file_path):
            messagebox.showerror("Error", "Please select both metadata and image files.")
            return
        
        # Check files exist
        if not self.metadata_file_path.exists():
            messagebox.showerror("Error", f"Metadata file not found: {self.metadata_file_path}")
            return
        if not self.image_file_path.exists():
            messagebox.showerror("Error", f"Image file not found: {self.image_file_path}")
            return
        
        # Check IPFS connection
        if not self.ipfs.check_status():
            result = messagebox.askyesno("IPFS Not Connected", 
                                       "IPFS is not running. Do you want to continue anyway?")
            if not result:
                return
        
        try:
            # Disable buttons and show progress
            self.nft_upload_btn.config(state=tk.DISABLED)
            self.nft_progress_bar.grid(row=4, column=0, columnspan=2, sticky="ew", pady=5)
            self.nft_progress_bar.start()
            
            self.nft_status_var.set("Creating NFT... Please wait.")
            self.run_threaded(self._upload_nft_thread)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start NFT creation: {e}")
            self._reset_nft_ui()
    
    def _upload_nft_thread(self):
        """Upload NFT in background thread with automatic pinning"""
        try:
            print(f"Starting NFT creation with automatic pinning...")
            
            # Step 1: Upload image to IPFS
            self.root.after(0, lambda: self.nft_status_var.set("Step 1/6: Uploading image to IPFS..."))
            image_hash = self.ipfs.add_file(self.image_file_path)
            
            if not image_hash:
                raise Exception("Failed to upload image to IPFS")
            
            print(f"Image uploaded with hash: {image_hash}")
            
            # Step 2: Pin image to local IPFS
            image_pinned = False
            self.root.after(0, lambda: self.nft_status_var.set("Step 2/6: Pinning image to local IPFS..."))
            try:
                image_pinned = self.ipfs.pin_hash(image_hash)
                if image_pinned:
                    print(f"✅ Image pinned locally: {image_hash}")
                else:
                    print(f"⚠️ Failed to pin image: {image_hash}")
            except Exception as e:
                print(f"⚠️ Error pinning image: {e}")
            
            # Step 3: Read and update metadata
            self.root.after(0, lambda: self.nft_status_var.set("Step 3/6: Updating metadata..."))
            
            with open(self.metadata_file_path, 'r') as f:
                metadata = json.load(f)
            
            # Update metadata with IPFS image URL
            metadata['image'] = f"ipfs://{image_hash}"
            
            # Step 4: Upload updated metadata to IPFS
            self.root.after(0, lambda: self.nft_status_var.set("Step 4/6: Uploading metadata to IPFS..."))
            
            # Write updated metadata to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(metadata, temp_file, indent=2)
                temp_metadata_path = Path(temp_file.name)
            
            try:
                metadata_hash = self.ipfs.add_file(temp_metadata_path)
                if not metadata_hash:
                    raise Exception("Failed to upload metadata to IPFS")
                
                print(f"Metadata uploaded with hash: {metadata_hash}")
                
                # Step 5: Pin metadata to local IPFS
                metadata_pinned = False
                self.root.after(0, lambda: self.nft_status_var.set("Step 5/6: Pinning metadata to local IPFS..."))
                try:
                    metadata_pinned = self.ipfs.pin_hash(metadata_hash)
                    if metadata_pinned:
                        print(f"✅ Metadata pinned locally: {metadata_hash}")
                    else:
                        print(f"⚠️ Failed to pin metadata: {metadata_hash}")
                except Exception as e:
                    print(f"⚠️ Error pinning metadata: {e}")
                
                # Step 6: Add to database
                self.root.after(0, lambda: self.nft_status_var.set("Step 6/6: Adding to collection..."))
                
                # Create NFT record
                nft_data = [{
                    'contract': {'address': 'user-created'},
                    'tokenId': f"local-{int(time.time())}",
                    'title': metadata.get('name', 'User Created NFT'),
                    'description': metadata.get('description', ''),
                    'media': [{'gateway': f"ipfs://{image_hash}"}],
                    'metadata': metadata,
                    'source_api': 'user-created'
                }]
                
                # Cache in database
                self.db.cache_nfts(nft_data)
                self.nfts = self.db.get_all_nfts()
                
                # Update viewer
                self.root.after(0, self.update_viewer_list)
                
                # Determine pinning status
                pinning_status = []
                if image_pinned:
                    pinning_status.append("✅ Image pinned locally")
                else:
                    pinning_status.append("⚠️ Image uploaded but not pinned")
                    
                if metadata_pinned:
                    pinning_status.append("✅ Metadata pinned locally")
                else:
                    pinning_status.append("⚠️ Metadata uploaded but not pinned")
                
                pinning_info = "\n".join(pinning_status)
                both_pinned = image_pinned and metadata_pinned
                
                # Success message with pinning status
                success_info = f"""✅ NFT CREATED SUCCESSFULLY!

Image Hash: {image_hash}
Metadata Hash: {metadata_hash}

STORAGE STATUS:
{pinning_info}

Your NFT has been added to your collection.
Switch to the Viewer tab to see it!

IPFS Gateway URLs:
Image: {self.ipfs.ipfs_gateway}ipfs/{image_hash}
Metadata: {self.ipfs.ipfs_gateway}ipfs/{metadata_hash}

IPFS Protocol URLs:
Image: ipfs://{image_hash}
Metadata: ipfs://{metadata_hash}
"""
                
                def show_success():
                    self.nft_status_var.set("NFT created and pinned successfully!" if both_pinned else "NFT created successfully!")
                    
                    # Update info display
                    self.nft_info_text.config(state=tk.NORMAL)
                    self.nft_info_text.delete(1.0, tk.END)
                    self.nft_info_text.insert(tk.END, success_info)
                    self.nft_info_text.config(state=tk.DISABLED)
                    
                    pin_status = "and pinned locally" if both_pinned else "but not fully pinned"
                    messagebox.showinfo("NFT Created!", f"NFT successfully created {pin_status}!\nCheck the preview for details.")
                
                self.root.after(0, show_success)
                
            finally:
                # Clean up temp file
                try:
                    temp_metadata_path.unlink()
                except:
                    pass
            
        except Exception as e:
            error_msg = f"NFT creation failed: {str(e)}"
            print(error_msg)
            
            def show_error():
                self.nft_status_var.set("NFT creation failed!")
                messagebox.showerror("NFT Creation Failed", error_msg)
            
            self.root.after(0, show_error)
        
        # Reset UI
        self.root.after(0, self._reset_nft_ui)

    def _reset_nft_ui(self):
        """Reset NFT upload UI"""
        self.check_nft_ready()  # Re-enable button if files still selected
        self.nft_progress_bar.stop()
        self.nft_progress_bar.grid_remove()

    # --- Manual Hash Entry Methods ---
    def paste_to_var(self, var):
        """Paste clipboard content to a StringVar"""
        try:
            clipboard_text = self.root.clipboard_get().strip()
            var.set(clipboard_text)
            print(f"Pasted to field: {clipboard_text}")
        except tk.TclError:
            messagebox.showinfo("Clipboard", "Clipboard is empty or contains no text")
    
    def clear_hash_fields(self):
        """Clear hash input fields"""
        self.metadata_hash_var.set("")
        self.image_hash_var.set("")
        self.hash_status_var.set("Enter IPFS hashes to add NFT to collection")
        
        # Clear preview
        self.hash_preview_text.config(state=tk.NORMAL)
        self.hash_preview_text.delete(1.0, tk.END)
        self.hash_preview_text.insert(tk.END, "Enter hashes above to preview NFT metadata...")
        self.hash_preview_text.config(state=tk.DISABLED)
    
    def add_nft_by_hash(self):
        """Add NFT to collection using provided hashes"""
        metadata_hash = self.metadata_hash_var.get().strip()
        image_hash = self.image_hash_var.get().strip()
        
        if not metadata_hash:
            messagebox.showerror("Error", "Please enter a metadata hash")
            return
        
        if not image_hash:
            messagebox.showerror("Error", "Please enter an image hash")
            return
        
        try:
            self.hash_status_var.set("Fetching metadata from IPFS...")
            self.run_threaded(self._add_nft_by_hash_thread, metadata_hash, image_hash)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add NFT: {e}")
    
    def _add_nft_by_hash_thread(self, metadata_hash, image_hash):
        """Add NFT by hash in background thread with automatic pinning"""
        try:
            # Use smart gateway selection for metadata URL
            metadata_ipfs_url = f"ipfs://{metadata_hash}"
            metadata_url = self.convert_ipfs_url_to_gateway(metadata_ipfs_url)
            
            # Step 1: Fetch metadata
            self.root.after(0, lambda: self.hash_status_var.set("Step 1/4: Fetching metadata..."))
            
            try:
                response = requests.get(metadata_url, timeout=10)
                response.raise_for_status()
                metadata = response.json()
                print(f"Successfully fetched metadata from: {metadata_url}")
            except Exception as e:
                # If we can't fetch metadata, create a basic one
                metadata = {
                    "name": f"NFT from Hash {metadata_hash[:8]}...",
                    "description": f"NFT added manually using IPFS hashes",
                    "image": f"ipfs://{image_hash}",
                    "external_url": "",
                    "attributes": []
                }
                print(f"Could not fetch metadata from gateway, using default: {e}")
            
            # Step 2: Pin metadata to local IPFS (if connected)
            metadata_pinned = False
            if self.ipfs.is_connected:
                self.root.after(0, lambda: self.hash_status_var.set("Step 2/4: Pinning metadata to local IPFS..."))
                try:
                    metadata_pinned = self.ipfs.pin_hash(metadata_hash)
                    if metadata_pinned:
                        print(f"✅ Metadata pinned locally: {metadata_hash}")
                    else:
                        print(f"⚠️ Failed to pin metadata: {metadata_hash}")
                except Exception as e:
                    print(f"⚠️ Error pinning metadata: {e}")
            
            # Step 3: Pin image to local IPFS (if connected)
            image_pinned = False
            if self.ipfs.is_connected:
                self.root.after(0, lambda: self.hash_status_var.set("Step 3/4: Pinning image to local IPFS..."))
                try:
                    image_pinned = self.ipfs.pin_hash(image_hash)
                    if image_pinned:
                        print(f"✅ Image pinned locally: {image_hash}")
                    else:
                        print(f"⚠️ Failed to pin image: {image_hash}")
                except Exception as e:
                    print(f"⚠️ Error pinning image: {e}")
            
            # Step 4: Use smart gateway selection for image URL
            self.root.after(0, lambda: self.hash_status_var.set("Step 4/4: Adding to collection..."))
            
            image_ipfs_url = f"ipfs://{image_hash}"
            image_gateway_url = self.convert_ipfs_url_to_gateway(image_ipfs_url)
            
            # Create NFT record with smart gateway URLs
            nft_data = [{
                'contract': {'address': 'manual-entry'},
                'tokenId': f"hash-{int(time.time())}",
                'title': metadata.get('name', 'Manual Entry NFT'),
                'description': metadata.get('description', ''),
                'media': [{'gateway': image_gateway_url}],  # Store smart gateway URL
                'metadata': metadata,
                'source_api': 'manual-entry'
            }]
            
            # Add to database
            self.db.cache_nfts(nft_data)
            self.nfts = self.db.get_all_nfts()
            
            # Update viewer
            self.root.after(0, self.update_viewer_list)
            
            # Determine storage status
            if self.ipfs.is_connected:
                storage_status = []
                if metadata_pinned:
                    storage_status.append("✅ Metadata pinned locally")
                else:
                    storage_status.append("⚠️ Metadata not pinned")
                    
                if image_pinned:
                    storage_status.append("✅ Image pinned locally")
                else:
                    storage_status.append("⚠️ Image not pinned")
                    
                storage_info = "\n".join(storage_status)
            else:
                storage_info = "ℹ️ IPFS not connected - files not pinned locally"
            
            # Show success with actual URLs used and pinning status
            gateway_type = "Local" if "127.0.0.1" in image_gateway_url else "Public"
            success_info = f"""✅ NFT ADDED SUCCESSFULLY!

Metadata Hash: {metadata_hash}
Image Hash: {image_hash}
NFT Name: {metadata.get('name', 'Unknown')}
Gateway Type: {gateway_type} IPFS Gateway

STORAGE STATUS:
{storage_info}

Your NFT has been added to your collection.
Switch to the Viewer tab to see it!

Gateway URLs Used:
Image: {image_gateway_url}
Metadata: {metadata_url}

IPFS Protocol URLs:
Image: ipfs://{image_hash}
Metadata: ipfs://{metadata_hash}
"""
            
            def show_success():
                self.hash_status_var.set("NFT added successfully!")
                
                # Update preview display
                self.hash_preview_text.config(state=tk.NORMAL)
                self.hash_preview_text.delete(1.0, tk.END)
                self.hash_preview_text.insert(tk.END, success_info)
                self.hash_preview_text.config(state=tk.DISABLED)
                
                pin_status = "and pinned locally" if (metadata_pinned and image_pinned) else "but not fully pinned"
                messagebox.showinfo("NFT Added!", 
                                  f"NFT successfully added {pin_status}!\nCheck the preview for details.")
                
                # Clear the input fields
                self.clear_hash_fields()
            
            self.root.after(0, show_success)
            
        except Exception as e:
            error_msg = f"Failed to add NFT: {str(e)}"
            print(error_msg)
            
            def show_error():
                self.hash_status_var.set("Failed to add NFT!")
                messagebox.showerror("Error", error_msg)
            
            self.root.after(0, show_error)