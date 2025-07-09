#!/usr/bin/env python3
"""
Simple NFT Slideshow Viewer
Displays NFTs from your collection in a fullscreen slideshow
"""

import tkinter as tk
from tkinter import messagebox
import threading
import time
import json
from pathlib import Path
from PIL import Image, ImageTk
import requests
import io
import random

# Import from your existing system
import sys
sys.path.append(str(Path.home() / "nft-system"))
from nft_system_core import DatabaseManager, ConfigManager, IPFSManager

class NFTSlideshowViewer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("NFT Slideshow Viewer")
        self.root.configure(bg='black')
        
        # Initialize core components
        self.app_dir = Path.home() / ".nft-system"
        self.config = ConfigManager(self.app_dir)
        self.db = DatabaseManager(self.app_dir / "nft_cache.db")
        self.ipfs = IPFSManager(self.config.get("ipfs_api"))
        
        # Slideshow settings
        self.slide_interval = 5000  # 5 seconds
        self.current_index = 0
        self.nfts = []
        self.is_playing = False
        self.slide_timer = None
        
        # UI setup
        self.setup_ui()
        self.setup_bindings()
        
        # Load NFTs
        self.load_nfts()
        
        # Start slideshow
        if self.nfts:
            self.show_current_nft()
            self.start_slideshow()

    def setup_ui(self):
        """Setup the slideshow UI"""
        # Make fullscreen
        self.root.attributes('-fullscreen', True)
        
        # Main frame
        self.main_frame = tk.Frame(self.root, bg='black')
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Image label
        self.image_label = tk.Label(self.main_frame, bg='black')
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Info overlay (bottom)
        self.info_frame = tk.Frame(self.root, bg='black', height=100)
        self.info_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.info_frame.pack_propagate(False)
        
        # NFT title
        self.title_label = tk.Label(self.info_frame, text="", fg='white', bg='black', 
                                  font=('Arial', 24, 'bold'), wraplength=800)
        self.title_label.pack(pady=10)
        
        # NFT description
        self.desc_label = tk.Label(self.info_frame, text="", fg='lightgray', bg='black', 
                                 font=('Arial', 16), wraplength=800)
        self.desc_label.pack()
        
        # Controls overlay (top)
        self.controls_frame = tk.Frame(self.root, bg='black', height=50)
        self.controls_frame.pack(side=tk.TOP, fill=tk.X)
        self.controls_frame.pack_propagate(False)
        
        # Status label
        self.status_label = tk.Label(self.controls_frame, text="", fg='white', bg='black', 
                                   font=('Arial', 14))
        self.status_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Progress label
        self.progress_label = tk.Label(self.controls_frame, text="", fg='white', bg='black', 
                                     font=('Arial', 14))
        self.progress_label.pack(side=tk.RIGHT, padx=20, pady=10)

    def setup_bindings(self):
        """Setup keyboard bindings"""
        self.root.bind('<Key>', self.on_key_press)
        self.root.focus_set()

    def on_key_press(self, event):
        """Handle keyboard input"""
        key = event.keysym.lower()
        
        if key == 'escape' or key == 'q':
            self.quit_slideshow()
        elif key == 'space':
            self.toggle_slideshow()
        elif key == 'right' or key == 'n':
            self.next_nft()
        elif key == 'left' or key == 'p':
            self.previous_nft()
        elif key == 'r':
            self.shuffle_nfts()
        elif key == 'f':
            self.toggle_fullscreen()
        elif key == 'h':
            self.show_help()

    def load_nfts(self):
        """Load NFTs from database"""
        try:
            all_nfts = self.db.get_all_nfts()
            # Filter NFTs that have images
            self.nfts = [nft for nft in all_nfts if nft.get('image_url')]
            
            if not self.nfts:
                messagebox.showwarning("No NFTs", "No NFTs with images found in your collection.")
                self.root.quit()
                return
            
            print(f"Loaded {len(self.nfts)} NFTs for slideshow")
            self.update_status(f"Loaded {len(self.nfts)} NFTs")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load NFTs: {e}")
            self.root.quit()

    def convert_ipfs_url_to_gateway(self, url):
        """Convert IPFS URLs to gateway URLs"""
        if not url:
            return url
        
        if url.startswith('ipfs://'):
            ipfs_hash = url.replace('ipfs://', '')
            if self.ipfs.is_connected:
                return f"http://127.0.0.1:8080/ipfs/{ipfs_hash}"
            else:
                return f"https://ipfs.io/ipfs/{ipfs_hash}"
        
        return url

    def show_current_nft(self):
        """Display the current NFT"""
        if not self.nfts:
            return
        
        nft = self.nfts[self.current_index]
        
        # Update progress
        self.progress_label.config(text=f"{self.current_index + 1} / {len(self.nfts)}")
        
        # Update info
        title = nft.get('title', 'Unknown NFT')
        description = nft.get('description', '')[:200] + ('...' if len(nft.get('description', '')) > 200 else '')
        
        self.title_label.config(text=title)
        self.desc_label.config(text=description)
        
        # Load image
        image_url = nft.get('image_url', '')
        if image_url:
            image_url = self.convert_ipfs_url_to_gateway(image_url)
            self.load_image_async(image_url)
        else:
            self.show_no_image()

    def load_image_async(self, url):
        """Load image in background thread"""
        def load_image():
            try:
                self.update_status("Loading image...")
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    # Load and resize image
                    img = Image.open(io.BytesIO(response.content))
                    
                    # Get screen size
                    screen_width = self.root.winfo_screenwidth()
                    screen_height = self.root.winfo_screenheight() - 150  # Account for info bars
                    
                    # Resize image to fit screen while maintaining aspect ratio
                    img.thumbnail((screen_width, screen_height), Image.Resampling.LANCZOS)
                    
                    # Convert to PhotoImage
                    photo = ImageTk.PhotoImage(img)
                    
                    # Update UI in main thread
                    def update_ui():
                        self.image_label.config(image=photo)
                        self.image_label.image = photo  # Keep reference
                        self.update_status("Ready" if not self.is_playing else "Playing")
                    
                    self.root.after(0, update_ui)
                else:
                    self.root.after(0, lambda: self.show_error(f"Failed to load image (HTTP {response.status_code})"))
                    
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Image load error: {e}"))
        
        threading.Thread(target=load_image, daemon=True).start()

    def show_no_image(self):
        """Show placeholder for NFTs without images"""
        self.image_label.config(image='', text="No Image Available", fg='white', font=('Arial', 24))
        self.image_label.image = None

    def show_error(self, error_msg):
        """Show error message"""
        self.image_label.config(image='', text=f"Error: {error_msg}", fg='red', font=('Arial', 18))
        self.image_label.image = None
        self.update_status("Error")

    def next_nft(self):
        """Show next NFT"""
        if self.nfts:
            self.current_index = (self.current_index + 1) % len(self.nfts)
            self.show_current_nft()

    def previous_nft(self):
        """Show previous NFT"""
        if self.nfts:
            self.current_index = (self.current_index - 1) % len(self.nfts)
            self.show_current_nft()

    def start_slideshow(self):
        """Start automatic slideshow"""
        if not self.is_playing and self.nfts:
            self.is_playing = True
            self.update_status("Playing")
            self.schedule_next_slide()

    def stop_slideshow(self):
        """Stop automatic slideshow"""
        if self.is_playing:
            self.is_playing = False
            if self.slide_timer:
                self.root.after_cancel(self.slide_timer)
            self.update_status("Paused")

    def toggle_slideshow(self):
        """Toggle slideshow on/off"""
        if self.is_playing:
            self.stop_slideshow()
        else:
            self.start_slideshow()

    def schedule_next_slide(self):
        """Schedule the next slide"""
        if self.is_playing:
            self.slide_timer = self.root.after(self.slide_interval, self.auto_next)

    def auto_next(self):
        """Automatically advance to next slide"""
        if self.is_playing:
            self.next_nft()
            self.schedule_next_slide()

    def shuffle_nfts(self):
        """Shuffle the NFT order"""
        if self.nfts:
            current_nft = self.nfts[self.current_index]
            random.shuffle(self.nfts)
            # Try to find the current NFT in the new order
            try:
                self.current_index = self.nfts.index(current_nft)
            except ValueError:
                self.current_index = 0
            self.update_status("Shuffled")
            self.show_current_nft()

    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        current_state = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current_state)

    def show_help(self):
        """Show help overlay"""
        help_text = """
NFT SLIDESHOW CONTROLS:

SPACE      - Play/Pause slideshow
→ / N      - Next NFT
← / P      - Previous NFT
R          - Shuffle order
F          - Toggle fullscreen
H          - Show this help
Q / ESC    - Quit

Enjoy your NFT collection!
        """
        messagebox.showinfo("Help", help_text)

    def update_status(self, status):
        """Update status label"""
        self.status_label.config(text=status)

    def quit_slideshow(self):
        """Quit the slideshow"""
        try:
            self.db.close()
        except:
            pass
        self.root.quit()
        self.root.destroy()

    def run(self):
        """Start the slideshow"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit_slideshow()

def main():
    """Main function"""
    try:
        slideshow = NFTSlideshowViewer()
        slideshow.run()
    except Exception as e:
        print(f"Error starting slideshow: {e}")

if __name__ == "__main__":
    main()