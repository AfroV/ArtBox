#!/usr/bin/env python3
import tkinter as tk
import subprocess
import sys
import time
from pathlib import Path

# The permanent location where the app is installed
APP_DIR = Path.home() / "nft-system"
USER = Path.home().name

class NFTLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NFT System Launcher")
        
        # Set window size and position
        self.geometry("280x220+50+50")  # Slightly taller for slideshow button
        
        # Make the window non-resizable
        self.resizable(False, False)
        
        # Keep the launcher on top of other windows
        self.wm_attributes("-topmost", True)
        
        # Set window to always be visible
        self.attributes('-alpha', 0.95)  # Slight transparency
        
        # Configure styling
        self.configure(bg="#2E2E2E")
        
        # Create widgets
        self.create_widgets()
        
        # Center the window after creation
        self.center_window()
        
        # Make sure window is visible
        self.deiconify()
        self.lift()
        self.focus_force()
        
        print("NFT Launcher started and positioned")

    def center_window(self):
        """Center the window on screen, but offset to top-left for visibility"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        
        # Position in top-left area but not at edge
        x = 50
        y = 50
        
        self.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        main_frame = tk.Frame(self, bg="#2E2E2E", padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header = tk.Label(
            main_frame, 
            text="NFT System", 
            bg="#2E2E2E", 
            fg="white", 
            font=("Arial", 16, "bold")
        )
        header.pack(pady=(0, 15))

        # Launch button
        launch_button = tk.Button(
            main_frame,
            text="🚀 Launch NFT System",
            command=self.launch_nft_system,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            width=22,
            height=2,
            relief="flat",
            cursor="hand2"
        )
        launch_button.pack(pady=5)

        # Slideshow button
        slideshow_button = tk.Button(
            main_frame,
            text="🎬 NFT Slideshow",
            command=self.launch_slideshow,
            bg="#9C27B0",
            fg="white",
            font=("Arial", 12, "bold"),
            width=22,
            height=2,
            relief="flat",
            cursor="hand2"
        )
        slideshow_button.pack(pady=5)

        # File manager button
        file_manager_button = tk.Button(
            main_frame,
            text="📁 Open Files",
            command=lambda: self.run_command(["pcmanfm", str(APP_DIR)]),
            bg="#2196F3",
            fg="white",
            font=("Arial", 12),
            width=22,
            relief="flat",
            cursor="hand2"
        )
        file_manager_button.pack(pady=5)
        
        # Close button
        close_button = tk.Button(
            main_frame,
            text="✕ Close Launcher",
            command=self.quit_launcher,
            bg="#f44336",
            fg="white",
            font=("Arial", 10),
            width=22,
            relief="flat",
            cursor="hand2"
        )
        close_button.pack(pady=(10, 0))

    def launch_nft_system(self):
        """Launch the NFT system directly without using the shell script"""
        try:
            print("Attempting to launch NFT System...")
            
            # Check if main_app.py exists
            main_app_path = APP_DIR / "main_app.py"
            if not main_app_path.exists():
                error_msg = f"main_app.py not found at {main_app_path}"
                print(f"ERROR: {error_msg}")
                import tkinter.messagebox as mb
                mb.showerror("Error", error_msg)
                return
            
            # Try to launch with virtual environment python first
            venv_python = APP_DIR / "venv" / "bin" / "python3"
            if venv_python.exists():
                print("Using virtual environment Python...")
                subprocess.Popen([str(venv_python), str(main_app_path)], 
                               cwd=str(APP_DIR))
                print("NFT System started with virtual environment Python")
            else:
                print("Virtual environment not found, using system Python...")
                subprocess.Popen(["python3", str(main_app_path)], 
                               cwd=str(APP_DIR))
                print("NFT System started with system Python")
                
        except Exception as e:
            error_msg = f"Failed to launch NFT System: {e}"
            print(f"ERROR: {error_msg}")
            import tkinter.messagebox as mb
            mb.showerror("Launch Error", error_msg)

    def launch_slideshow(self):
        """Launch the standalone NFT slideshow"""
        try:
            print("Attempting to launch NFT Slideshow...")
            
            # Check if slideshow file exists
            slideshow_path = APP_DIR / "nft_slideshow.py"
            if not slideshow_path.exists():
                error_msg = "NFT Slideshow not found. Please ensure nft_slideshow.py is in the NFT system folder."
                print(f"ERROR: {error_msg}")
                import tkinter.messagebox as mb
                mb.showerror("Error", error_msg)
                return
            
            # Try to launch with virtual environment python first
            venv_python = APP_DIR / "venv" / "bin" / "python3"
            if venv_python.exists():
                print("Using virtual environment Python for slideshow...")
                subprocess.Popen([str(venv_python), str(slideshow_path)], 
                               cwd=str(APP_DIR))
                print("NFT Slideshow started with virtual environment Python")
            else:
                print("Virtual environment not found, using system Python for slideshow...")
                subprocess.Popen(["python3", str(slideshow_path)], 
                               cwd=str(APP_DIR))
                print("NFT Slideshow started with system Python")
                
        except Exception as e:
            error_msg = f"Failed to launch NFT Slideshow: {e}"
            print(f"ERROR: {error_msg}")
            import tkinter.messagebox as mb
            mb.showerror("Launch Error", error_msg)

    def run_command(self, command):
        try:
            print(f"Running command: {command}")
            if isinstance(command, str):
                # For shell scripts, use shell=True
                subprocess.Popen(command, shell=True, cwd=APP_DIR)
            else:
                # For command lists
                subprocess.Popen(command, cwd=APP_DIR)
            print("Command started successfully")
        except Exception as e:
            print(f"Failed to run command: {command}\nError: {e}")
            # Show error in a simple dialog
            import tkinter.messagebox as mb
            mb.showerror("Error", f"Failed to run command:\n{e}")

    def quit_launcher(self):
        """Quit the launcher"""
        self.quit()
        self.destroy()

def check_prerequisites():
    """Check if the NFT system is properly installed"""
    if not APP_DIR.exists():
        print(f"ERROR: NFT System not found at {APP_DIR}")
        return False
        
    main_app = APP_DIR / "main_app.py"
    if not main_app.exists():
        print(f"ERROR: Main app not found at {main_app}")
        return False
    
    return True

def main():
    """Main function with error handling"""
    try:
        print("Starting NFT System Launcher...")
        
        # Check if system is properly installed
        if not check_prerequisites():
            print("NFT System not properly installed. Please run install.sh")
            import tkinter as tk
            import tkinter.messagebox as mb
            root = tk.Tk()
            root.withdraw()  # Hide main window
            mb.showerror("Installation Error", 
                        "NFT System not properly installed.\n"
                        "Please run the installer script.")
            root.destroy()
            sys.exit(1)
        
        # Create and run launcher
        app = NFTLauncher()
        
        print("Launcher GUI created, starting main loop...")
        app.mainloop()
        
    except Exception as e:
        print(f"FATAL ERROR in launcher: {e}")
        try:
            import tkinter.messagebox as mb
            mb.showerror("Launcher Error", f"Failed to start launcher:\n{e}")
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()