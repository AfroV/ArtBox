#!/usr/bin/env python3
"""
IPFS Backup Tool - GUI Version
Easy-to-use interface for downloading NFT metadata and assets from IPFS
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import csv
import json
import re
import time
import threading
import subprocess
import platform
import webbrowser
from pathlib import Path
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

class IPFSManager:
    """Handles IPFS daemon checking and starting"""
    
    def __init__(self):
        self.ipfs_process = None
        self.daemon_url = "http://127.0.0.1:8080"
        
    def is_running(self):
        """Check if IPFS daemon is running"""
        try:
            response = requests.get(f"{self.daemon_url}/ipfs/bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def is_installed(self):
        """Check if IPFS is installed"""
        try:
            result = subprocess.run(['ipfs', 'version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def start_daemon(self):
        """Start IPFS daemon in background"""
        try:
            # Start daemon in background
            if platform.system() == 'Windows':
                # On Windows, use CREATE_NO_WINDOW flag
                CREATE_NO_WINDOW = 0x08000000
                self.ipfs_process = subprocess.Popen(
                    ['ipfs', 'daemon'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=CREATE_NO_WINDOW
                )
            else:
                # On Unix-like systems
                self.ipfs_process = subprocess.Popen(
                    ['ipfs', 'daemon'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            # Wait a bit for daemon to start
            time.sleep(3)
            
            # Check if it's running
            for _ in range(10):  # Try for 10 seconds
                if self.is_running():
                    return True
                time.sleep(1)
            
            return False
        except Exception as e:
            print(f"Error starting IPFS: {e}")
            return False
    
    def get_download_url(self):
        """Get IPFS download URL for current platform"""
        system = platform.system()
        if system == 'Windows':
            return "https://docs.ipfs.tech/install/ipfs-desktop/#windows"
        elif system == 'Darwin':  # macOS
            return "https://docs.ipfs.tech/install/ipfs-desktop/#macos"
        else:  # Linux
            return "https://docs.ipfs.tech/install/ipfs-desktop/#linux"

class IPFSBackupDownloader:
    def __init__(self, output_dir="ipfs_backup"):
        self.files_dir = Path(output_dir) / "files"
        self.files_dir.mkdir(parents=True, exist_ok=True)
        self.downloaded = set()
        self.lock = threading.Lock()
        self.progress_file = Path(output_dir) / "download_progress.json"
        self.session = requests.Session()
        self.cid_pattern = re.compile(r'(?:https?://[^/\s]*ipfs[^/\s]*/(?:ipfs/)?|ipfs://)?(?:(Qm[a-zA-Z0-9]{44})|(baf[a-z0-9]{50,}))', re.I)
        self.completed_items = 0
        self.total_items = 0
        self.stop_event = threading.Event()
        self.callback = None
        self._load_progress()

    def _load_progress(self):
        if self.progress_file.exists():
            try:
                self.downloaded = set(json.load(open(self.progress_file)).get("downloaded", []))
            except: pass

    def _save_progress(self):
        json.dump({"downloaded": list(self.downloaded)}, open(self.progress_file, "w"), indent=2)

    def _update_progress(self):
        with self.lock:
            self.completed_items += 1
            if self.callback:
                percentage = (self.completed_items / self.total_items * 100) if self.total_items > 0 else 0
                self.callback(self.completed_items, self.total_items, percentage)

    def _download(self, cid, quiet=False):
        url = f"http://127.0.0.1:8080/ipfs/{cid}"
        for attempt in range(5):  # Reduced from 40 to 5 attempts
            if self.stop_event.is_set():
                return None
            try:
                r = self.session.get(url, timeout=30)
                if r.status_code == 200 and len(r.content) > 100:  # Reduced from 1000 to 100 bytes
                    return r.content
            except:
                pass
            # Wait 3 seconds between retries (reduced from 20)
            for _ in range(3):
                if self.stop_event.is_set():
                    return None
                time.sleep(1)
        return None

    def _exists(self, cid):
        return any((self.files_dir / f"{cid}{e}").exists() for e in [".json",".gif",".png",".jpg",".mp4",".glb",".html",".bin",".webp"])

    def _extract_all_cids(self, obj, parent_cid):
        cids = []
        if isinstance(obj, str):
            for match in self.cid_pattern.finditer(obj):
                cid = match.group(1) or match.group(2)
                if cid and cid != parent_cid:
                    cids.append(cid)
        elif isinstance(obj, dict):
            for value in obj.values():
                cids.extend(self._extract_all_cids(value, parent_cid))
        elif isinstance(obj, list):
            for item in obj:
                cids.extend(self._extract_all_cids(item, parent_cid))
        return cids

    def download_cid(self, cid, name="", is_nested=False):
        if self.stop_event.is_set():
            return False

        cid = cid.strip()

        already_exists = self._exists(cid)

        # Thread-safe check and mark: Skip if already processed in this session
        with self.lock:
            if cid in self.downloaded:
                return True
            # Mark as processed to prevent duplicate downloads
            self.downloaded.add(cid)

        if already_exists:
            for ext in [".json",".gif",".png",".jpg",".mp4",".glb",".html",".bin",".webp"]:
                file_path = self.files_dir / f"{cid}{ext}"
                if file_path.exists():
                    if ext in [".json", ".html"] and not is_nested:
                        try:
                            data = file_path.read_bytes()
                            text_content = data.decode("utf-8", errors="ignore")
                            if ext == ".json":
                                meta = json.loads(text_content)
                                nested_cids = self._extract_all_cids(meta, cid)
                            else:
                                nested_cids = []
                                for match in self.cid_pattern.finditer(text_content):
                                    found_cid = match.group(1) or match.group(2)
                                    if found_cid and found_cid != cid:
                                        nested_cids.append(found_cid)
                            if nested_cids:
                                for nested in nested_cids:
                                    if not self._exists(nested):
                                        self.download_cid(nested, is_nested=True)
                        except: pass
                    return True

        data = self._download(cid, quiet=is_nested)
        if not data:
            # Failed to download - still mark as processed but don't save
            return False

        ext = ".bin"
        if data.startswith(b'<!DOCTYPE html'): ext = ".html"
        elif data.startswith(b'\x89PNG'): ext = ".png"
        elif data.startswith(b'\xff\xd8\xff'): ext = ".jpg"
        elif data.startswith(b'GIF8'): ext = ".gif"
        elif len(data) >= 12 and data[:4] == b'RIFF' and data[8:12] == b'WEBP': ext = ".webp"
        elif len(data) >= 8 and data[4:8] in [b'ftyp', b'mdat', b'moov', b'wide']: ext = ".mp4"
        elif data.startswith(b'glTF'): ext = ".glb"
        else:
            try: json.loads(data); ext = ".json"
            except: pass

        (self.files_dir / f"{cid}{ext}").write_bytes(data)
        with self.lock:
            self._save_progress()

        if ext in [".json", ".html"] and not is_nested:
            try:
                text_content = data.decode("utf-8", errors="ignore")
                if ext == ".json":
                    meta = json.loads(text_content)
                    nested_cids = self._extract_all_cids(meta, cid)
                else:
                    nested_cids = []
                    for match in self.cid_pattern.finditer(text_content):
                        found_cid = match.group(1) or match.group(2)
                        if found_cid and found_cid != cid:
                            nested_cids.append(found_cid)
                if nested_cids:
                    for nested in nested_cids:
                        if not self._exists(nested):
                            self.download_cid(nested, is_nested=True)
            except: pass
        return True

    def run(self, csv_files, workers=1):
        # Clear downloaded set for this run (files on disk are still preserved)
        self.downloaded.clear()

        items = []
        for csv_file in csv_files:
            with open(csv_file, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    cid = (row.get("cid") or row.get("CID") or "").strip()
                    if not cid:
                        metadata_url = (row.get("metadata_url") or row.get("metadataUrl") or "").strip()
                        if metadata_url:
                            match = self.cid_pattern.search(metadata_url)
                            if match:
                                cid = match.group(1) or match.group(2)
                    if cid and cid not in ["See CSV","On-Chain","Arweave","--"]:
                        title = row.get("title") or row.get("name") or row.get("filename") or ""
                        items.append((title, cid))

        self.total_items = len(items)
        self.completed_items = 0
        
        # Notify GUI of total items
        if self.callback:
            self.callback(0, self.total_items, 0)

        def task(item):
            if self.stop_event.is_set():
                return
            title, cid = item
            self.download_cid(cid, title)
            self._update_progress()

        try:
            if workers == 1:
                for item in items:
                    if self.stop_event.is_set():
                        break
                    task(item)
            else:
                with ThreadPoolExecutor(max_workers=workers) as exe:
                    futures = [exe.submit(task, i) for i in items]
                    for future in as_completed(futures):
                        if self.stop_event.is_set():
                            break
                        future.result()
        except Exception as e:
            print(f"Error during download: {e}")

class IPFSBackupGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("IPFS Backup Tool")
        self.root.geometry("700x750")
        
        # Variables
        self.csv_folder = Path("csv_files")
        self.csv_files = []
        self.checkboxes = []
        self.checkbox_vars = []
        self.downloader = None
        self.download_thread = None
        self.ipfs_manager = IPFSManager()
        
        self.setup_ui()
        self.scan_csv_files()
        
        # Check IPFS status on startup
        self.root.after(1000, self.check_ipfs_status)
        
    def setup_ui(self):
        # Configure ttk style for always-visible scrollbar and buttons
        style = ttk.Style()
        style.theme_use('clam')  # Use a theme that supports visible scrollbars and button styling

        # Configure button styles for cross-platform color support
        style.configure("Green.TButton",
                       background="#27ae60",
                       foreground="white",
                       borderwidth=0,
                       focuscolor='none',
                       font=("Arial", 12, "bold"),
                       padding=(30, 10))
        style.map("Green.TButton",
                 background=[('active', '#2ecc71'), ('pressed', '#229954')])

        style.configure("Red.TButton",
                       background="#e74c3c",
                       foreground="white",
                       borderwidth=0,
                       focuscolor='none',
                       font=("Arial", 12, "bold"),
                       padding=(30, 10))
        style.map("Red.TButton",
                 background=[('active', '#ec7063'), ('pressed', '#c0392b')],
                 foreground=[('disabled', 'white')])

        style.configure("Blue.TButton",
                       background="#3498db",
                       foreground="white",
                       borderwidth=0,
                       focuscolor='none',
                       font=("Arial", 10),
                       padding=(20, 10))
        style.map("Blue.TButton",
                 background=[('active', '#5dade2'), ('pressed', '#2980b9')])

        style.configure("Purple.TButton",
                       background="#9b59b6",
                       foreground="white",
                       borderwidth=0,
                       focuscolor='none',
                       font=("Arial", 10),
                       padding=(20, 10))
        style.map("Purple.TButton",
                 background=[('active', '#bb8fce'), ('pressed', '#8e44ad')])

        style.configure("Gray.TButton",
                       background="#95a5a6",
                       foreground="white",
                       borderwidth=0,
                       focuscolor='none',
                       font=("Arial", 10),
                       padding=(15, 5))
        style.map("Gray.TButton",
                 background=[('active', '#b2babb'), ('pressed', '#7f8c8d')])

        # Header
        header = tk.Frame(self.root, bg="#2c3e50", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title = tk.Label(header, text="🗂️ IPFS Backup Tool",
                        font=("Arial", 20, "bold"), fg="white", bg="#2c3e50")
        title.pack(pady=20)

        # Main container
        main = tk.Frame(self.root, padx=20, pady=20)
        main.pack(fill=tk.BOTH, expand=True)
        
        # Folder selection
        folder_frame = tk.Frame(main)
        folder_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(folder_frame, text="CSV Folder:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.folder_label = tk.Label(folder_frame, text=str(self.csv_folder),
                                     font=("Arial", 10), fg="#3498db")
        self.folder_label.pack(side=tk.LEFT, padx=10)

        ttk.Button(folder_frame, text="Change Folder", command=self.change_folder,
                  style="Blue.TButton").pack(side=tk.RIGHT)
        ttk.Button(folder_frame, text="Refresh", command=self.scan_csv_files,
                  style="Green.TButton").pack(side=tk.RIGHT, padx=5)
        
        # CSV file selection
        selection_frame = tk.LabelFrame(main, text="Select CSV Files to Download", 
                                       font=("Arial", 11, "bold"), padx=10, pady=10)
        selection_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Scrollable frame for checkboxes
        canvas = tk.Canvas(selection_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(selection_frame, orient="vertical", command=canvas.yview)
        self.checkbox_frame = tk.Frame(canvas)
        
        self.checkbox_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.checkbox_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Select all/none buttons
        select_frame = tk.Frame(main)
        select_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(select_frame, text="Select All", command=self.select_all,
                  style="Gray.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(select_frame, text="Select None", command=self.select_none,
                  style="Gray.TButton").pack(side=tk.LEFT)
        
        # Workers selection
        workers_frame = tk.Frame(select_frame)
        workers_frame.pack(side=tk.RIGHT)
        tk.Label(workers_frame, text="Workers:").pack(side=tk.LEFT, padx=5)
        self.workers_var = tk.IntVar(value=1)
        workers_spinbox = tk.Spinbox(workers_frame, from_=1, to=8, width=5, 
                                    textvariable=self.workers_var)
        workers_spinbox.pack(side=tk.LEFT)
        
        # Progress section
        progress_frame = tk.LabelFrame(main, text="Download Progress", 
                                      font=("Arial", 11, "bold"), padx=10, pady=10)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_label = tk.Label(progress_frame, text="Ready to start", font=("Arial", 10))
        self.progress_label.pack()

        # Configure green progress bar style
        style.configure("green.Horizontal.TProgressbar",
                       troughcolor='#ecf0f1',
                       background='#27ae60',
                       darkcolor='#27ae60',
                       lightcolor='#2ecc71',
                       bordercolor='#555555')

        self.progress_bar = ttk.Progressbar(progress_frame, length=600, mode='determinate',
                                           style="green.Horizontal.TProgressbar")
        self.progress_bar.pack(pady=5, fill=tk.X)
        
        self.status_label = tk.Label(progress_frame, text="Checking IPFS status...", font=("Arial", 9), fg="#7f8c8d")
        self.status_label.pack()
        
        # Control buttons
        button_frame = tk.Frame(main)
        button_frame.pack(fill=tk.X)

        self.start_button = ttk.Button(button_frame, text="Start Download",
                                       command=self.start_download,
                                       style="Green.TButton")
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="Stop",
                                      command=self.stop_download,
                                      style="Red.TButton")
        self.stop_button.pack(side=tk.LEFT, padx=5)
        self.stop_button.state(['disabled'])

        self.check_ipfs_button = ttk.Button(button_frame, text="Check IPFS",
                                            command=self.check_ipfs_status,
                                            style="Blue.TButton")
        self.check_ipfs_button.pack(side=tk.RIGHT, padx=5)

        self.open_folder_button = ttk.Button(button_frame, text="Open Files Folder",
                                             command=self.open_files_folder,
                                             style="Purple.TButton")
        self.open_folder_button.pack(side=tk.RIGHT, padx=5)
        
    def change_folder(self):
        folder = filedialog.askdirectory(title="Select CSV Folder")
        if folder:
            self.csv_folder = Path(folder)
            self.folder_label.config(text=str(self.csv_folder))
            self.scan_csv_files()
    
    def scan_csv_files(self):
        # Clear existing checkboxes
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()
        
        self.csv_files = []
        self.checkboxes = []
        self.checkbox_vars = []
        
        # Create CSV folder if it doesn't exist
        self.csv_folder.mkdir(exist_ok=True)
        
        # Find all CSV files
        csv_files = sorted(self.csv_folder.glob("*.csv"))
        
        if not csv_files:
            tk.Label(self.checkbox_frame, 
                    text="No CSV files found in this folder.\nPlace your CSV files in the 'csv_files' folder.",
                    font=("Arial", 10), fg="#e74c3c").pack(pady=20)
            return
        
        # Create checkboxes
        for i, csv_file in enumerate(csv_files):
            var = tk.BooleanVar(value=True)
            self.checkbox_vars.append(var)
            
            # Get file info
            file_size = csv_file.stat().st_size
            size_str = f"{file_size/1024:.1f} KB" if file_size < 1024*1024 else f"{file_size/1024/1024:.1f} MB"
            
            # Count rows
            try:
                with open(csv_file, encoding="utf-8") as f:
                    row_count = sum(1 for _ in csv.DictReader(f))
            except:
                row_count = "?"
            
            frame = tk.Frame(self.checkbox_frame)
            frame.pack(fill=tk.X, pady=5)
            
            cb = tk.Checkbutton(frame, text=csv_file.name, variable=var, 
                               font=("Arial", 10, "bold"))
            cb.pack(side=tk.LEFT)
            
            info = tk.Label(frame, text=f"({row_count} items, {size_str})", 
                          font=("Arial", 9), fg="#7f8c8d")
            info.pack(side=tk.LEFT, padx=10)
            
            self.csv_files.append(csv_file)
            self.checkboxes.append(cb)
    
    def select_all(self):
        for var in self.checkbox_vars:
            var.set(True)
    
    def select_none(self):
        for var in self.checkbox_vars:
            var.set(False)

    def open_files_folder(self):
        """Open the downloaded files folder in file explorer"""
        files_folder = Path("ipfs_backup") / "files"
        files_folder.mkdir(parents=True, exist_ok=True)

        # Open folder in system file explorer
        import os
        if platform.system() == 'Windows':
            os.startfile(files_folder)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', str(files_folder)])
        else:  # Linux
            subprocess.run(['xdg-open', str(files_folder)])

    def check_ipfs_status(self):
        """Check IPFS status and show indicator"""
        if self.ipfs_manager.is_running():
            self.status_label.config(text="✅ IPFS daemon is running", fg="#27ae60")
        else:
            # Check if installed or not
            if not self.ipfs_manager.is_installed():
                self.status_label.config(text="⚠️ IPFS is not installed", fg="#e74c3c")
            else:
                self.status_label.config(text="⚠️ IPFS daemon is not running", fg="#e74c3c")
            # Offer to start or download IPFS
            self.check_and_start_ipfs()
    
    def check_and_start_ipfs(self):
        """Check if IPFS is running, offer to start it if not"""
        if self.ipfs_manager.is_running():
            return True
        
        # IPFS is not running - check if installed
        if not self.ipfs_manager.is_installed():
            # IPFS not installed
            response = messagebox.askyesno(
                "IPFS Not Installed",
                "IPFS is not installed on your system.\n\n"
                "Would you like to download IPFS Desktop?\n\n"
                "(You'll need to install it and restart this application)",
                icon='warning'
            )
            if response:
                webbrowser.open(self.ipfs_manager.get_download_url())
            return False
        
        # IPFS is installed but not running
        response = messagebox.askyesnocancel(
            "IPFS Not Running",
            "IPFS daemon is not running.\n\n"
            "Would you like to:\n"
            "• Yes - Start IPFS daemon now\n"
            "• No - Open IPFS documentation\n"
            "• Cancel - Go back",
            icon='warning'
        )
        
        if response is True:  # Yes - start daemon
            # Show progress dialog
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Starting IPFS")
            progress_window.geometry("300x100")
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            label = tk.Label(progress_window, text="Starting IPFS daemon...\nThis may take a few seconds.", 
                           font=("Arial", 10), pady=20)
            label.pack()
            
            success = [False]
            
            def start_daemon_thread():
                success[0] = self.ipfs_manager.start_daemon()
                progress_window.after(0, progress_window.destroy)
            
            thread = threading.Thread(target=start_daemon_thread, daemon=True)
            thread.start()
            
            # Wait for window to close
            self.root.wait_window(progress_window)
            
            if success[0]:
                messagebox.showinfo("Success", "IPFS daemon started successfully!")
                self.check_ipfs_status()
                return True
            else:
                messagebox.showerror(
                    "Failed to Start",
                    "Could not start IPFS daemon.\n\n"
                    "Please start it manually:\n"
                    "1. Open terminal/command prompt\n"
                    "2. Run: ipfs daemon"
                )
                return False
        
        elif response is False:  # No - open docs
            webbrowser.open("https://docs.ipfs.tech/install/command-line/")
            return False
        
        else:  # Cancel
            return False
    
    def update_progress(self, completed, total, percentage):
        self.root.after(0, lambda: self._update_progress_ui(completed, total, percentage))
    
    def _update_progress_ui(self, completed, total, percentage):
        self.progress_bar['value'] = percentage
        if completed == 0 and total > 0:
            self.progress_label.config(text=f"Starting download of {total} items...")
            self.status_label.config(text="Connecting to IPFS...")
        elif completed >= total:
            self.progress_label.config(text=f"Complete: {completed}/{total} items (100%)")
            self.status_label.config(text="All items processed")
        else:
            self.progress_label.config(text=f"Downloading: {completed}/{total} items ({percentage:.1f}%)")
            self.status_label.config(text=f"{total - completed} items remaining")
    
    def start_download(self):
        # Get selected files
        selected_files = [f for f, var in zip(self.csv_files, self.checkbox_vars) if var.get()]
        
        if not selected_files:
            messagebox.showwarning("No Selection", "Please select at least one CSV file.")
            return
        
        # Check if IPFS is running (and offer to start it)
        if not self.check_and_start_ipfs():
            return

        # Disable start button, enable stop button
        self.start_button.state(['disabled'])
        self.stop_button.state(['!disabled'])
        
        # Reset progress
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Preparing download...")
        self.status_label.config(text="Loading CSV files...")
        
        # Start download in separate thread
        self.download_thread = threading.Thread(
            target=self._run_download, 
            args=(selected_files,),
            daemon=True
        )
        self.download_thread.start()
    
    def _run_download(self, selected_files):
        try:
            # Show loading message
            self.root.after(0, lambda: self.progress_label.config(text="Loading CSV files..."))
            self.root.after(0, lambda: self.status_label.config(text="Please wait..."))
            
            self.downloader = IPFSBackupDownloader("ipfs_backup")
            self.downloader.callback = self.update_progress
            self.downloader.run(selected_files, workers=self.workers_var.get())
            
            if not self.downloader.stop_event.is_set():
                self.root.after(0, lambda: self._show_completion_dialog(
                    len(self.downloader.downloaded),
                    self.downloader.files_dir.resolve()
                ))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Download error: {str(e)}"))
        finally:
            self.root.after(0, self._download_finished)
    
    def stop_download(self):
        if self.downloader:
            self.downloader.stop_event.set()
            self.status_label.config(text="Stopping... (waiting for current downloads to finish)")
    
    def _show_completion_dialog(self, file_count, folder_path):
        """Show completion dialog with option to open folder"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Download Complete")
        dialog.geometry("450x200")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (225)
        y = (dialog.winfo_screenheight() // 2) - (100)
        dialog.geometry(f"450x200+{x}+{y}")

        # Success message
        message_frame = tk.Frame(dialog, padx=20, pady=10)
        message_frame.pack(fill=tk.X)

        tk.Label(message_frame, text="✅ Download Complete!",
                font=("Arial", 14, "bold"), fg="#27ae60").pack(pady=(10, 10))

        tk.Label(message_frame, text=f"{file_count} unique files downloaded",
                font=("Arial", 10)).pack()

        tk.Label(message_frame, text=f"Location: {folder_path}",
                font=("Arial", 9), fg="#7f8c8d", wraplength=400).pack(pady=(5, 10))

        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=15)

        open_btn = ttk.Button(button_frame, text="Open File Location",
                             command=lambda: [self.open_files_folder(), dialog.destroy()],
                             style="Green.TButton")
        open_btn.pack(side=tk.LEFT, padx=5)

        close_btn = ttk.Button(button_frame, text="Close",
                              command=dialog.destroy,
                              style="Gray.TButton")
        close_btn.pack(side=tk.LEFT, padx=5)

    def _download_finished(self):
        self.start_button.state(['!disabled'])
        self.stop_button.state(['disabled'])

def main():
    root = tk.Tk()
    app = IPFSBackupGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
