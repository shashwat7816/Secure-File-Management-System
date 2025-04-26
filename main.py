import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from cryptography.fernet import Fernet
import hashlib
import base64
import os
import datetime
import sqlite3
import bcrypt
import mimetypes
import threading
from PIL import Image, ImageTk
import io
import fitz
import multiprocessing
import psutil
from tkinter import font as tkfont
import math
from functools import partial
import time
import random  # For particle animations
from themes import get_current_theme_colors, get_glass_colors  # Import theme functions
from custom_dialogs import (login_dialog, register_dialog, show_process_info_dialog, 
                          analyze_storage_dialog, show_file_metadata_dialog)

# Global variables
dark_mode = False
current_user_id = None
file_locks = {}

# Define color schemes
color_schemes = {
    "dark": {
        "bg": "#1E1E1E",
        "fg": "#FFFFFF",
        "accent1": "#3498DB",
        "accent2": "#2ECC71",
        "accent3": "#E74C3C",
        "accent4": "#F39C12",
        "accent5": "#9B59B6",
        "button_bg": "#333333",
        "button_fg": "#FFFFFF",
        "hover_bg": "#555555",
    },
    "light": {
        "bg": "#F5F5F5",
        "fg": "#333333",
        "accent1": "#2980B9",
        "accent2": "#27AE60",
        "accent3": "#C0392B",
        "accent4": "#D35400",
        "accent5": "#8E44AD",
        "button_bg": "#E0E0E0",
        "button_fg": "#333333",
        "hover_bg": "#CCCCCC",
    }
}
current_theme = "dark"

# Create a custom class for styled buttons
class StyledButton(tk.Button):
    def __init__(self, master=None, **kwargs):
        self.hover_bg = kwargs.pop('hover_bg', "#555555")
        self.normal_bg = kwargs.get('bg', "#333333")
        self.normal_fg = kwargs.get('fg', "#FFFFFF")
        super().__init__(master, **kwargs)
        self.configure(relief=tk.FLAT, borderwidth=0, padx=10, pady=5)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        self.config(bg=self.hover_bg)

    def _on_leave(self, e):
        self.config(bg=self.normal_bg)

# Database initialization function
def init_db():
    conn = sqlite3.connect("file_manager.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    file_name TEXT,
                    file_data BLOB,
                    file_size INTEGER,
                    file_type TEXT,
                    action TEXT,
                    timestamp TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )''')
    conn.commit()
    conn.close()

def update_file_dropdown():
    conn = sqlite3.connect("file_manager.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_name FROM files WHERE user_id = ?", (current_user_id,))
    files = cursor.fetchall()
    conn.close()
    file_dropdown['values'] = [file[0] for file in files]

def update_ui_theme():
    scheme = color_schemes[current_theme]
    bg_color = scheme["bg"]
    fg_color = scheme["fg"]
    # Update root and frames
    root.configure(bg=bg_color)
    title_label.config(bg=bg_color, fg=fg_color)
    username_label.config(bg=bg_color, fg=fg_color)
    auth_frame.config(bg=bg_color)
    auth_frame1.config(bg=bg_color)
    auth_frame2.config(bg=bg_color)
    lock_frame.config(bg=bg_color)
    lock_status_label.config(bg=bg_color)
    # Update style for ttk elements
    style = ttk.Style()
    style.configure("TCombobox", fieldbackground=scheme["button_bg"], background=scheme["button_bg"])
    style.map('TCombobox', fieldbackground=[('readonly', scheme["button_bg"])])
    style.configure("TCombobox", selectbackground=scheme["accent1"])
    # Update canvas
    if hasattr(root, 'background_canvas'):
        draw_gradient_background()

def register_user():
    if not hasattr(root, 'after_id'):
        result = register_dialog(root, current_theme)
        if result["success"]:
            messagebox.showinfo("Welcome", f"Welcome, {result['username']}! Your account has been created.")

def login_user():
    global current_user_id, username_label
    result = login_dialog(root, current_theme)
    if result["success"]:
        current_user_id = result["user_id"]
        username_label.config(text=f"Logged in as: {result['username']}")
        update_file_dropdown()

def logout_user():
    global current_user_id, username_label
    current_user_id = None
    messagebox.showinfo("Logout", "Successfully logged out!")
    username_label.config(text="Not logged in")
    file_dropdown['values'] = []

def generate_key(password):
    return base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())

def encrypt_file():
    selected_file = file_dropdown.get()
    password = simpledialog.askstring("Encrypt", "Enter a password for encryption:", show='*')
    if selected_file and password:
        # Start encryption in a separate thread to prevent UI freezing
        threading.Thread(target=_encrypt_file_thread, args=(selected_file, password)).start()
        # Show "Processing" message immediately
        status_message = messagebox.showinfo("Processing", "Encryption started. You can continue working.")

def _encrypt_file_thread(selected_file, password):
    """Background thread for file encryption"""
    try:
        conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        cursor.execute("SELECT file_data FROM files WHERE file_name = ? AND user_id = ?", (selected_file, current_user_id))
        result = cursor.fetchone()
        if result:
            key = generate_key(password)
            cipher = Fernet(key)
            encrypted_data = cipher.encrypt(result[0])
            cursor.execute("UPDATE files SET file_data = ?, action = 'Encrypted' WHERE file_name = ? AND user_id = ?", 
                         (encrypted_data, selected_file, current_user_id))
            conn.commit()
            conn.close()
            # Schedule a message on the main thread
            root.after(0, lambda: messagebox.showinfo("Success", "File encrypted successfully!"))
    except Exception as e:
        # Handle any errors
        root.after(0, lambda: messagebox.showerror("Error", f"Encryption failed: {str(e)}"))

def decrypt_file():
    selected_file = file_dropdown.get()
    password = simpledialog.askstring("Decrypt", "Enter the decryption password:", show='*')
    if selected_file and password:
        # Start decryption in a separate thread
        threading.Thread(target=_decrypt_file_thread, args=(selected_file, password)).start()
        # Show "Processing" message immediately
        status_message = messagebox.showinfo("Processing", "Decryption started. You can continue working.")

def _decrypt_file_thread(selected_file, password):
    """Background thread for file decryption"""
    try:
        conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        cursor.execute("SELECT file_data FROM files WHERE file_name = ? AND user_id = ?", (selected_file, current_user_id))
        result = cursor.fetchone()
        if result:
            try:
                key = generate_key(password)
                cipher = Fernet(key)
                decrypted_data = cipher.decrypt(result[0])
                cursor.execute("UPDATE files SET file_data = ?, action = 'Decrypted' WHERE file_name = ? AND user_id = ?", 
                             (decrypted_data, selected_file, current_user_id))
                conn.commit()
                conn.close()
                # Schedule a message on the main thread
                root.after(0, lambda: messagebox.showinfo("Success", "File decrypted successfully!"))
            except:
                root.after(0, lambda: messagebox.showerror("Error", "Decryption failed. Incorrect password!"))
    except Exception as e:
        # Handle any errors
        root.after(0, lambda: messagebox.showerror("Error", f"Decryption failed: {str(e)}"))

def delete_file():
    selected_file = file_dropdown.get()
    if selected_file:
        conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM files WHERE file_name = ? AND user_id = ?", (selected_file, current_user_id))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "File deleted successfully!")
        update_file_dropdown()

def rename_file():
    selected_file = file_dropdown.get()
    new_name = simpledialog.askstring("Rename", "Enter new file name:")
    if selected_file and new_name:
        conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE files SET file_name = ? WHERE file_name = ? AND user_id = ?", (new_name, selected_file, current_user_id))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "File renamed successfully!")
        update_file_dropdown()

def preview_file():
    selected_file = file_dropdown.get()
    if selected_file:
        # Start loading file data in background thread
        threading.Thread(target=_load_preview_data, args=(selected_file,)).start()
        
def _load_preview_data(selected_file):
    """Background thread for loading file data for preview"""
    try:
        conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        cursor.execute("SELECT file_data, file_type FROM files WHERE file_name = ? AND user_id = ?", 
                     (selected_file, current_user_id))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # Schedule UI updates on the main thread
            root.after(0, lambda: _show_preview_window(selected_file, result[0], result[1]))
        else:
            root.after(0, lambda: messagebox.showerror("Error", "File not found!"))
    except Exception as e:
        root.after(0, lambda: messagebox.showerror("Error", f"Error loading file: {str(e)}"))

def _show_preview_window(selected_file, file_data, file_type):
    """Create and show the preview window (runs on main thread)"""
    # Create a styled preview window
    preview_window = tk.Toplevel(root)
    preview_window.title(f"Preview - {selected_file}")
    preview_window.geometry("800x600")
    preview_window.configure(bg=color_schemes[current_theme]["bg"])
    
    # Add window icon if available
    try:
        preview_window.iconphoto(False, preview_icon)
    except:
        pass
        
    # Create a frame for the preview content
    preview_frame = tk.Frame(preview_window, bg=color_schemes[current_theme]["bg"],
                          padx=20, pady=20)
    preview_frame.pack(expand=True, fill=tk.BOTH)
    
    # Create a loading indicator
    loading_label = tk.Label(preview_frame, text="Loading preview...", 
                           font=("Arial", 14, "italic"),
                           bg=color_schemes[current_theme]["bg"],
                           fg=color_schemes[current_theme]["accent1"])
    loading_label.pack(expand=True)
    
    # Process the preview in a separate thread
    threading.Thread(target=_process_preview, 
                   args=(preview_window, preview_frame, loading_label, file_data, file_type)).start()

def _process_preview(preview_window, preview_frame, loading_label, file_data, file_type):
    """Process and display file preview in background thread"""
    try:
        if file_type and file_type.startswith("text"):
            # Handle Text Files with syntax highlighting
            try:
                file_content = file_data.decode("utf-8")
                
                # Schedule UI update on main thread
                def update_text_preview():
                    loading_label.destroy()
                    preview_text = tk.Text(preview_frame, wrap=tk.WORD, 
                                         font=("Consolas", 12),
                                         bg=color_schemes[current_theme]["button_bg"],
                                         fg=color_schemes[current_theme]["fg"],
                                         padx=10, pady=10,
                                         insertbackground=color_schemes[current_theme]["fg"])
                    preview_text.insert(tk.END, file_content)
                    preview_text.config(state=tk.DISABLED)
                    # Add scrollbar
                    scrollbar = tk.Scrollbar(preview_frame, command=preview_text.yview)
                    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                    preview_text.config(yscrollcommand=scrollbar.set)
                    preview_text.pack(expand=True, fill=tk.BOTH)
                
                root.after(0, update_text_preview)
            except UnicodeDecodeError:
                root.after(0, lambda: messagebox.showerror("Error", "Cannot preview this file. It may be non-text data."))
                root.after(0, loading_label.destroy)
        elif file_type and file_type.startswith("image"):
            # Handle Image Files with enhanced display
            try:
                image = Image.open(io.BytesIO(file_data))
                
                # Calculate proportional resize to fit window
                max_width = 700
                max_height = 500
                img_width, img_height = image.size
                # Calculate aspect ratio
                aspect_ratio = img_width / img_height
                if img_width > max_width:
                    img_width = max_width
                    img_height = int(img_width / aspect_ratio)
                if img_height > max_height:
                    img_height = max_height
                    img_width = int(img_height * aspect_ratio)
                image = image.resize((img_width, img_height), Image.LANCZOS)  
                photo = ImageTk.PhotoImage(image)
                
                # Schedule UI update on main thread
                def update_image_preview():
                    loading_label.destroy()
                    # Create image info label
                    info_label = tk.Label(preview_frame, 
                                        text=f"Image Size: {image.width}x{image.height} px",
                                        font=("Arial", 10),
                                        bg=color_schemes[current_theme]["bg"],
                                        fg=color_schemes[current_theme]["fg"])
                    info_label.pack(pady=(0, 10))
                    # Create a canvas with border
                    img_canvas = tk.Canvas(preview_frame, 
                                         width=img_width+10, 
                                         height=img_height+10,
                                         bg=color_schemes[current_theme]["button_bg"],
                                         bd=0,
                                         highlightthickness=1,
                                         highlightbackground=color_schemes[current_theme]["accent1"])
                    img_canvas.pack(expand=True)
                    img_canvas.create_image(5, 5, anchor=tk.NW, image=photo)
                    img_canvas.image = photo  # Keep a reference
                
                root.after(0, update_image_preview)
            except Exception as e:
                root.after(0, lambda: messagebox.showerror("Error", f"Cannot preview this image.\n{e}"))
                root.after(0, loading_label.destroy)
        # ... Similar changes for PDF handling ...
        else:
            root.after(0, lambda: messagebox.showerror("Error", "File format not supported for preview."))
            root.after(0, loading_label.destroy)
            
        # Add close button on main thread
        root.after(0, lambda: _add_preview_close_button(preview_window))
    except Exception as e:
        root.after(0, lambda: messagebox.showerror("Error", f"Preview failed: {str(e)}"))
        root.after(0, loading_label.destroy)

def _add_preview_close_button(preview_window):
    """Add close button to preview window"""
    close_btn = StyledButton(preview_window, text="Close Preview", 
                          command=preview_window.destroy,
                          bg=color_schemes[current_theme]["accent3"],
                          fg=color_schemes[current_theme]["button_fg"],
                          hover_bg="#D35400",
                          font=("Arial", 12, "bold"))
    close_btn.pack(pady=15)

def show_file_metadata():
    selected_file = file_dropdown.get()
    if selected_file:
        conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        cursor.execute("SELECT file_size, file_type, action, timestamp FROM files WHERE file_name = ? AND user_id = ?", (selected_file, current_user_id))
        result = cursor.fetchone()
        conn.close()
        if result:
            # Pass the file information to the styled metadata dialog
            file_info = (selected_file, result[0], result[1], result[2], result[3])
            show_file_metadata_dialog(root, file_info, current_theme)

def toggle_dark_mode():
    global dark_mode, current_theme
    dark_mode = not dark_mode
    current_theme = "dark" if dark_mode else "light"
    toggle_button.config(text="🌙 Dark Mode" if not dark_mode else "☀️ Light Mode")
    update_ui_theme()
    draw_gradient_background()

def show_process_info():
    show_process_info_dialog(root, current_theme)
    
def upload_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_type = mimetypes.guess_type(file_path)[0] or "Unknown"
        # Memory management for large files
        if file_size > 10 * 1024 * 1024:  # 10MB
            messagebox.showinfo("Large File", "Processing large file with memory mapping")
            # Use memory mapping for large files
            with open(file_path, 'rb') as f:
                import mmap
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    file_data = mm.read()
        else:
            # Regular file reading for smaller files
            with open(file_path, 'rb') as file:
                file_data = file.read()
        conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO files (user_id, file_name, file_data, file_size, file_type, action, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (current_user_id, file_name, file_data, file_size, file_type, "Uploaded", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "File uploaded successfully!")
        update_file_dropdown()

def download_file():
    selected_file = file_dropdown.get()
    if not selected_file:
        messagebox.showerror("Error", "No file selected")
        return
    if selected_file in file_locks and file_locks[selected_file] != current_user_id:
        messagebox.showerror("Error", "File is locked by another user")
        return
    
    # Ask user for save location
    save_path = filedialog.asksaveasfilename(
        defaultextension=".*",
        initialfile=selected_file,
        title="Save File As"
    )
    
    if save_path:
        # Create progress indicator
        progress_window = tk.Toplevel(root)
        progress_window.title("Downloading")
        progress_window.geometry("300x100")
        progress_window.configure(bg=color_schemes[current_theme]["bg"])
        progress_window.resizable(False, False)
        
        # Add progress label
        progress_label = tk.Label(progress_window, text="Downloading file...", 
                                font=("Arial", 12),
                                bg=color_schemes[current_theme]["bg"],
                                fg=color_schemes[current_theme]["fg"])
        progress_label.pack(pady=(20, 10))
        
        # Start download in background thread
        thread = threading.Thread(target=_download_file_thread, 
                                args=(selected_file, save_path, progress_window))
        thread.daemon = True
        thread.start()

def _download_file_thread(selected_file, save_path, progress_window):
    """Background thread for file download"""
    try:
        conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        cursor.execute("SELECT file_data, file_type FROM files WHERE file_name = ? AND user_id = ?", 
                     (selected_file, current_user_id))
        result = cursor.fetchone()
        
        if result:
            file_data, file_type = result
            
            with open(save_path, 'wb') as file:
                file.write(file_data)
            
            # Log download operation
            cursor.execute("UPDATE files SET action = 'Downloaded', timestamp = ? WHERE file_name = ? AND user_id = ?", 
                         (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), selected_file, current_user_id))
            conn.commit()
            conn.close()
            
            # Schedule UI updates on main thread
            root.after(0, lambda: [progress_window.destroy(), 
                                  messagebox.showinfo("Success", f"File saved to {save_path}")])
        else:
            conn.close()
            root.after(0, lambda: [progress_window.destroy(), 
                                  messagebox.showerror("Error", "File not found in database")])
    except Exception as e:
        root.after(0, lambda: [progress_window.destroy(), 
                              messagebox.showerror("Error", f"Failed to save file: {e}")])

def analyze_fragmentation():
    if not current_user_id:
        messagebox.showerror("Error", "Please login first")
        return
    
    # Show immediate feedback
    status_label = tk.Label(root, text="Loading file data...", 
                          font=("Arial", 10, "italic"),
                          fg=color_schemes[current_theme]["accent1"],
                          bg=color_schemes[current_theme]["bg"])
    status_label.pack(pady=5)
    root.update()
    
    # Start analysis in background thread
    threading.Thread(target=_analyze_fragmentation_thread, args=(status_label,)).start()

def _analyze_fragmentation_thread(status_label):
    """Background thread for analyzing file fragmentation"""
    try:
        conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        cursor.execute("SELECT file_name, file_size FROM files WHERE user_id = ? ORDER BY id", (current_user_id,))
        files = cursor.fetchall()
        conn.close()
        
        # Schedule UI update on main thread
        root.after(0, lambda: [status_label.destroy(), analyze_storage_dialog(root, files, current_theme)])
    except Exception as e:
        root.after(0, lambda: [status_label.destroy(), messagebox.showerror("Error", f"Analysis failed: {str(e)}")])

def lock_file():
    selected_file = file_dropdown.get()
    if not selected_file:
        messagebox.showerror("Error", "No file selected")
        return
    if selected_file in file_locks:
        messagebox.showerror("Error", f"File {selected_file} is already locked")
    else:
        file_locks[selected_file] = current_user_id
        messagebox.showinfo("File Lock", f"File {selected_file} has been locked for exclusive access")
        update_lock_status()

def unlock_file():
    selected_file = file_dropdown.get()
    if not selected_file:
        messagebox.showerror("Error", "No file selected")
        return
    if selected_file in file_locks:
        if file_locks[selected_file] == current_user_id:
            del file_locks[selected_file]
            messagebox.showinfo("File Lock", f"File {selected_file} has been unlocked")
            update_lock_status()
        else:
            messagebox.showerror("Error", "You cannot unlock a file locked by another user")
    else:
        messagebox.showinfo("File Lock", f"File {selected_file} is not locked")

def update_lock_status():
    selected_file = file_dropdown.get()
    if selected_file in file_locks:
        lock_status_label.config(text=f"🔒 Locked", fg=color_schemes[current_theme]["accent3"])
        
        # Add animated lock icon effect
        if hasattr(lock_status_label, 'pulse_animation_id'):
            lock_status_label.after_cancel(lock_status_label.pulse_animation_id)
        
        def pulse_animation():
            current_color = lock_status_label.cget("fg")
            new_color = color_schemes[current_theme]["accent3"] if current_color == color_schemes[current_theme]["accent2"] else color_schemes[current_theme]["accent2"]
            lock_status_label.config(fg=new_color)
            lock_status_label.pulse_animation_id = lock_status_label.after(500, pulse_animation)
        
        lock_status_label.pulse_animation_id = lock_status_label.after(0, pulse_animation)
    else:
        lock_status_label.config(text=f"🔓 Unlocked", fg=color_schemes[current_theme]["accent2"])
        if hasattr(lock_status_label, 'pulse_animation_id'):
            lock_status_label.after_cancel(lock_status_label.pulse_animation_id)

def threaded_upload():
    file_path = filedialog.askopenfilename()
    if file_path:
        # Create a progress indicator
        progress_window = tk.Toplevel(root)
        progress_window.title("Uploading")
        progress_window.geometry("300x100")
        progress_window.configure(bg=color_schemes[current_theme]["bg"])
        progress_window.resizable(False, False)
        
        # Add progress label
        progress_label = tk.Label(progress_window, text="Uploading file...", 
                                font=("Arial", 12),
                                bg=color_schemes[current_theme]["bg"],
                                fg=color_schemes[current_theme]["fg"])
        progress_label.pack(pady=(20, 10))
        
        # Start upload in background thread
        thread = threading.Thread(target=_upload_file_thread, args=(file_path, progress_window))
        thread.daemon = True
        thread.start()

def _upload_file_thread(file_path, progress_window):
    """Background thread for file upload"""
    try:
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_type = mimetypes.guess_type(file_path)[0] or "Unknown"
        
        # Memory management for large files
        if file_size > 10 * 1024 * 1024:  # 10MB
            # Use memory mapping for large files
            with open(file_path, 'rb') as f:
                import mmap
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    file_data = mm.read()
        else:
            # Regular file reading for smaller files
            with open(file_path, 'rb') as file:
                file_data = file.read()
                
        conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO files (user_id, file_name, file_data, file_size, file_type, action, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                     (current_user_id, file_name, file_data, file_size, file_type, "Uploaded", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        
        # Schedule UI updates on main thread
        root.after(0, lambda: [progress_window.destroy(), 
                              messagebox.showinfo("Success", "File uploaded successfully!"),
                              update_file_dropdown()])
    except Exception as e:
        root.after(0, lambda: [progress_window.destroy(), 
                              messagebox.showerror("Error", f"Upload failed: {str(e)}")])

def on_dropdown_select(event=None):
    update_lock_status()

def create_tooltip(widget, text):
    """Create a tooltip for a widget"""
    def enter(event):
        x, y, _, height = widget.bbox("insert")
        x += widget.winfo_rootx() + 25
        y += widget.winfo_rooty() + 20
        # Create a toplevel window
        tw = tk.Toplevel(widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=text, justify='left',
                       background=color_schemes[current_theme]["accent1"], 
                       foreground="white",
                       relief='solid', borderwidth=1,
                       font=("Arial", "9", "normal"),
                       padx=5, pady=2)
        label.pack(ipadx=1)
        widget.tooltip = tw
    def leave(event):
        if hasattr(widget, 'tooltip'):
            widget.tooltip.destroy()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)

def draw_gradient_background():
    """Draw a gradient background on the canvas with animated elements"""
    # Limit animation frame rate to reduce CPU usage
    if hasattr(draw_gradient_background, 'last_update'):
        current_time = time.time()
        if current_time - draw_gradient_background.last_update < 0.1:  # Limit to 10 FPS
            background_canvas.after(50, draw_gradient_background)
            return
        draw_gradient_background.last_update = current_time
    else:
        draw_gradient_background.last_update = time.time()
        # Initialize frame_count when last_update is first created
        draw_gradient_background.frame_count = 0
        
    colors = color_schemes[current_theme]
    width = root.winfo_width()
    height = root.winfo_height()
    if width <= 1 or height <= 1:  # Window not initialized yet
        width = 600
        height = 700
    # Clear previous drawing
    background_canvas.delete("all")
            
    # Create gradient based on theme
    if current_theme == "dark":
        start_color = (30, 30, 30)  # Dark gray
        end_color = (10, 10, 30)    # Nearly black with blue tint
    else:
        start_color = (245, 245, 245)  # Light gray
        end_color = (220, 235, 245)    # Light blue tint

    # Draw gradient rectangles
    for i in range(height):
        # Calculate color for this line
        ratio = i / height
        r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
        g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
        b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
        color = f'#{r:02x}{g:02x}{b:02x}'
        background_canvas.create_line(0, i, width, i, fill=color)
    
    # Add some decorative elements to make it more visually interesting
    # Circles in the background
    for i in range(5):
        x = width * (0.1 + (0.8 * (i / 4)))
        y = height * (0.1 + (0.6 * math.sin(i / 2)))
        size = width * 0.1 * ((i % 3) + 1) / 3
        color = colors["accent" + str(i % 5 + 1)]
        # Create very low opacity circles - replace with solid color
        background_canvas.create_oval(x - size, y - size, 
                                    x + size, y + size, 
                                    outline=color,
                                    width=2,
                                    fill="")

    # Add floating particles effect
    if not hasattr(draw_gradient_background, 'particles'):
        # Initialize particles
        draw_gradient_background.particles = []
        for _ in range(15):
            particle = {
                'x': random.randint(0, width),
                'y': random.randint(0, height),
                'size': random.randint(2, 6),
                'speed': random.uniform(0.2, 1.0),
                'color': colors["accent" + str(random.randint(1, 5))]
            }
            draw_gradient_background.particles.append(particle)
        # Initialize frame counter when particles are created
        draw_gradient_background.frame_count = 0
    
    # More efficient particle animation
    particles = draw_gradient_background.particles
    
    # Update only half the particles each frame
    update_count = max(1, len(particles) // 2)
    for i in range(update_count):
        idx = (draw_gradient_background.frame_count + i) % len(particles)
        particle = particles[idx]
        
        # Draw particle
        x, y = particle['x'], particle['y']
        size = particle['size']
        color = particle['color']
        
        # Create a subtle glow effect with concentric circles
        for i in range(3):
            glow_size = size * (1 + i*0.5)
            # Remove opacity, just use solid colors
            
            background_canvas.create_oval(
                x - glow_size, y - glow_size,
                x + glow_size, y + glow_size,
                fill=color if i == 0 else "", 
                outline=color if i > 0 else "",
                width=1
            )
        
        # Update particle position for next draw
        particle['y'] += particle['speed']
        
        # Reset particles that go off screen
        if particle['y'] > height:
            particle['y'] = -particle['size']
            particle['x'] = random.randint(0, width)
    
    # Increment frame counter
    draw_gradient_background.frame_count += 1
    
    # Add some decorative elements like subtle grid lines
    if current_theme == "dark":
        # Replace "#ffffff08" (which has alpha) with a very light solid color
        grid_color = "#333333"  # Very dark gray for dark mode
    else:
        # Replace "#00000008" (which has alpha) with a very light solid color
        grid_color = "#DDDDDD"  # Very light gray for light mode
    
    # Horizontal grid lines
    grid_spacing = 40
    for y in range(0, height, grid_spacing):
        background_canvas.create_line(0, y, width, y, fill=grid_color, dash=(1, 3))
    
    # Vertical grid lines
    for x in range(0, width, grid_spacing):
        background_canvas.create_line(x, 0, x, height, fill=grid_color, dash=(1, 3))
    
    # Schedule next animation frame with lower frequency
    background_canvas.after(100, draw_gradient_background)  # Reduced from 50ms to 100ms
    
    # Fixed: Send the canvas to the back of stacking order
    background_canvas.master.lower(background_canvas)

def apply_glass_effect(widget):
    """Apply a glass-like translucent effect to a widget"""
    # Get glass colors from theme
    glass_colors = get_glass_colors(current_theme)
    
    # Apply the glass background color
    widget.config(bg=glass_colors["bg"])
    
    # Add a thin border
    widget.config(highlightbackground=color_schemes[current_theme]["accent1"], 
                  highlightthickness=1)

def create_animated_button(parent, text, command, **kwargs):
    """Create a button with animation effects"""
    btn = StyledButton(parent, text=text, command=command, **kwargs)
    
    # Add ripple effect on click
    def add_ripple(event):
        # Create ripple effect
        x, y = event.x, event.y
        ripple_radius = 0
        max_radius = max(btn.winfo_width(), btn.winfo_height()) * 1.5
        ripple_color = "#ffffff33" if current_theme == "dark" else "#00000033"
        
        # Create canvas for ripple if it doesn't exist
        if not hasattr(btn, 'ripple_canvas'):
            btn.ripple_canvas = tk.Canvas(btn, highlightthickness=0, bg="")
            btn.ripple_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
            btn.ripple_canvas.lower()  # Place behind text
        
        # Clear previous ripples
        btn.ripple_canvas.delete("ripple")
        
        # Animation function
        def animate_ripple():
            nonlocal ripple_radius
            if ripple_radius < max_radius:
                btn.ripple_canvas.delete("ripple")
                btn.ripple_canvas.create_oval(
                    x - ripple_radius, y - ripple_radius,
                    x + ripple_radius, y + ripple_radius,
                    outline="", fill=ripple_color, tags="ripple"
                )
                ripple_radius += 5
                btn.after(10, animate_ripple)
            else:
                btn.ripple_canvas.delete("ripple")
                
        animate_ripple()
    
    btn.bind("<Button-1>", add_ripple)
    return btn

def show_welcome_animation():
    """Show a welcome animation when app starts"""
    welcome_window = tk.Toplevel(root)
    welcome_window.overrideredirect(True)
    welcome_window.attributes('-alpha', 0.0)  # Start fully transparent
    welcome_window.configure(bg=color_schemes[current_theme]["bg"])
    
    # Position in center of root window
    x = root.winfo_x() + (root.winfo_width() // 2) - 200
    y = root.winfo_y() + (root.winfo_height() // 2) - 100
    welcome_window.geometry(f"400x200+{x}+{y}")
    
    # Create welcome message
    welcome_label = tk.Label(welcome_window, 
                           text="Welcome to\nSecure File Manager", 
                           font=("Helvetica", 24, "bold"),
                           fg=color_schemes[current_theme]["accent1"],
                           bg=color_schemes[current_theme]["bg"])
    welcome_label.pack(expand=True)
    
    # Animation to fade in and out
    def fade_in():
        alpha = welcome_window.attributes('-alpha')
        if alpha < 0.9:
            welcome_window.attributes('-alpha', alpha + 0.1)
            welcome_window.after(50, fade_in)
        else:
            welcome_window.after(1000, fade_out)
    
    def fade_out():
        alpha = welcome_window.attributes('-alpha')
        if alpha > 0.1:
            welcome_window.attributes('-alpha', alpha - 0.1)
            welcome_window.after(50, fade_out)
        else:
            welcome_window.destroy()
    
    fade_in()

# Initialize the GUI
root = tk.Tk()
root.title("Secure File Manager")
root.geometry("800x750")
root.minsize(700, 700)
root.configure(bg=color_schemes[current_theme]["bg"])

# Create canvas for gradient background
background_canvas = tk.Canvas(root, highlightthickness=0)
background_canvas.place(x=0, y=0, relwidth=1, relheight=1)
# Fixed: Manually send the canvas to the back using the correct method
root.lower(background_canvas)  # This properly lowers the canvas in the window's stacking order

# Load icons with error handling
try:
    encrypt_icon = ImageTk.PhotoImage(Image.open("encrypt.png").resize((24, 24)))
    decrypt_icon = ImageTk.PhotoImage(Image.open("decrypt.png").resize((24, 24)))
    upload_icon = ImageTk.PhotoImage(Image.open("upload.png").resize((24, 24)))
    delete_icon = ImageTk.PhotoImage(Image.open("delete.png").resize((24, 24)))
    rename_icon = ImageTk.PhotoImage(Image.open("rename.png").resize((24, 24)))
    preview_icon = ImageTk.PhotoImage(Image.open("preview.png").resize((24, 24)))
    # Try to set window icon
    root.iconphoto(False, preview_icon)
except Exception as e:
    print(f"Error loading icons: {e}")
    try:
        # Try to generate icons
        import generate_icons
        generate_icons.generate_icons()
        
        # Try loading again
        encrypt_icon = ImageTk.PhotoImage(Image.open("encrypt.png").resize((24, 24)))
        decrypt_icon = ImageTk.PhotoImage(Image.open("decrypt.png").resize((24, 24)))
        upload_icon = ImageTk.PhotoImage(Image.open("upload.png").resize((24, 24)))
        delete_icon = ImageTk.PhotoImage(Image.open("delete.png").resize((24, 24)))
        rename_icon = ImageTk.PhotoImage(Image.open("rename.png").resize((24, 24)))
        preview_icon = ImageTk.PhotoImage(Image.open("preview.png").resize((24, 24)))
        # Try to set window icon
        root.iconphoto(False, preview_icon)
    except Exception as e2:
        print(f"Error generating icons: {e2}")
        # Create empty images as fallback
        encrypt_icon = ImageTk.PhotoImage(Image.new('RGBA', (24, 24), (0, 0, 0, 0)))
        decrypt_icon = ImageTk.PhotoImage(Image.new('RGBA', (24, 24), (0, 0, 0, 0)))
        upload_icon = ImageTk.PhotoImage(Image.new('RGBA', (24, 24), (0, 0, 0, 0)))
        delete_icon = ImageTk.PhotoImage(Image.new('RGBA', (24, 24), (0, 0, 0, 0)))
        rename_icon = ImageTk.PhotoImage(Image.new('RGBA', (24, 24), (0, 0, 0, 0)))
        preview_icon = ImageTk.PhotoImage(Image.new('RGBA', (24, 24), (0, 0, 0, 0)))

# Set up ttk style
style = ttk.Style()
style.theme_use('clam')  # Use 'clam' theme as base
style.configure("TCombobox", fieldbackground=color_schemes[current_theme]["button_bg"], 
               foreground=color_schemes[current_theme]["fg"])

# Main title with enhanced shadow effect
title_frame = tk.Frame(root, bg=color_schemes[current_theme]["bg"])
title_frame.pack(pady=(30, 5))

# Create multiple shadow layers for a better shadow effect
for offset in range(3, 0, -1):
    shadow_label = tk.Label(title_frame, text="Secure File Manager", 
                          font=("Helvetica", 34, "bold"), 
                          fg=f"#{30+offset*10:02x}{30+offset*10:02x}{30+offset*10:02x}", 
                          bg=color_schemes[current_theme]["bg"])
    shadow_label.grid(row=0, column=0, padx=offset, pady=offset)

# Main title label on top
title_label = tk.Label(title_frame, text="Secure File Manager", 
                     font=("Helvetica", 34, "bold"), 
                     fg=color_schemes[current_theme]["accent1"], 
                     bg=color_schemes[current_theme]["bg"])
title_label.grid(row=0, column=0)

# Status bar showing login status
username_label = tk.Label(root, text="Not logged in", 
                        font=("Arial", 12, "italic"), 
                        fg=color_schemes[current_theme]["fg"], 
                        bg=color_schemes[current_theme]["bg"])
username_label.pack(pady=10)

# Mode toggle button
toggle_button = StyledButton(root, text="🌙 Dark Mode", command=toggle_dark_mode, 
                           font=("Arial", 12), 
                           bg=color_schemes[current_theme]["button_bg"], 
                           fg=color_schemes[current_theme]["button_fg"],
                           hover_bg=color_schemes[current_theme]["hover_bg"])
toggle_button.pack(pady=5)

# Authentication frame
auth_frame = tk.Frame(root, bg=color_schemes[current_theme]["bg"])
auth_frame.pack(pady=15)

register_button = create_animated_button(auth_frame, text="Register", command=register_user, 
                             font=("Arial", 12, "bold"), 
                             bg=color_schemes[current_theme]["accent1"], 
                             fg="white",
                             hover_bg="#1A5276")
register_button.grid(row=0, column=0, padx=10)

login_button = StyledButton(auth_frame, text="Login", command=login_user, 
                          font=("Arial", 12, "bold"), 
                          bg=color_schemes[current_theme]["accent2"], 
                          fg="white",
                          hover_bg="#1E8449")
login_button.grid(row=0, column=1, padx=10)

logout_button = StyledButton(auth_frame, text="Logout", command=logout_user, 
                           font=("Arial", 12, "bold"), 
                           bg=color_schemes[current_theme]["accent3"], 
                           fg="white",
                           hover_bg="#A93226")
logout_button.grid(row=0, column=2, padx=10)

# Create a frame for the file selection area
file_selection_frame = tk.Frame(root, pady=15)
file_selection_frame.pack(fill=tk.X, padx=20)
apply_glass_effect(file_selection_frame)

# File label
file_label = tk.Label(file_selection_frame, text="Select File:", 
                    font=("Arial", 12, "bold"), 
                    fg=color_schemes[current_theme]["fg"], 
                    bg=color_schemes[current_theme]["bg"])
file_label.pack(side=tk.LEFT, padx=(0, 10))

# File dropdown with styling
file_dropdown = ttk.Combobox(file_selection_frame, state="readonly", width=40, font=("Arial", 12))
file_dropdown.pack(side=tk.LEFT, fill=tk.X, expand=True)
file_dropdown.bind("<<ComboboxSelected>>", on_dropdown_select)

# Main action buttons frame with a more organized layout
main_actions_frame = tk.Frame(root, bg=color_schemes[current_theme]["bg"])
main_actions_frame.pack(pady=15, fill=tk.X, padx=20)

# Upload button (full width)
upload_button = StyledButton(main_actions_frame, text="Upload File", command=threaded_upload,
                           image=upload_icon, compound="left", 
                           font=("Arial", 12, "bold"), 
                           bg=color_schemes[current_theme]["accent2"], 
                           fg="white",
                           hover_bg="#1E8449")
upload_button.pack(fill=tk.X, pady=(0, 10))

# Download and Preview buttons (side by side)
download_preview_frame = tk.Frame(main_actions_frame, bg=color_schemes[current_theme]["bg"])
download_preview_frame.pack(fill=tk.X)

download_button = StyledButton(download_preview_frame, text="Download", command=download_file, 
                             font=("Arial", 12, "bold"), 
                             bg=color_schemes[current_theme]["accent4"], 
                             fg="white",
                             hover_bg="#B9770E")
download_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

preview_button = StyledButton(download_preview_frame, text="Preview File", command=preview_file,
                            image=preview_icon, compound="left", 
                            font=("Arial", 12, "bold"), 
                            bg=color_schemes[current_theme]["accent1"], 
                            fg="white",
                            hover_bg="#1A5276")
preview_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

# File operation buttons in a grid
auth_frame1 = tk.Frame(root, bg=color_schemes[current_theme]["bg"])
auth_frame1.pack(pady=15)

encrypt_button = StyledButton(auth_frame1, text="Encrypt", command=encrypt_file,
                            image=encrypt_icon, compound="left", 
                            font=("Arial", 12, "bold"), 
                            bg=color_schemes[current_theme]["accent4"], 
                            fg="white",
                            hover_bg="#B9770E")
encrypt_button.grid(row=0, column=0, padx=10, pady=10)

decrypt_button = StyledButton(auth_frame1, text="Decrypt", command=decrypt_file,
                            image=decrypt_icon, compound="left", 
                            font=("Arial", 12, "bold"), 
                            bg=color_schemes[current_theme]["accent1"], 
                            fg="white",
                            hover_bg="#1A5276")
decrypt_button.grid(row=0, column=1, padx=10, pady=10)

delete_button = StyledButton(auth_frame1, text="Delete", command=delete_file,
                           image=delete_icon, compound="left", 
                           font=("Arial", 12, "bold"), 
                           bg=color_schemes[current_theme]["accent3"], 
                           fg="white",
                           hover_bg="#A93226")
delete_button.grid(row=1, column=0, padx=10, pady=10)

rename_button = StyledButton(auth_frame1, text="Rename", command=rename_file,
                           image=rename_icon, compound="left", 
                           font=("Arial", 12, "bold"), 
                           bg=color_schemes[current_theme]["accent5"], 
                           fg="white",
                           hover_bg="#6C3483")
rename_button.grid(row=1, column=1, padx=10, pady=10)

# Advanced operations frame
auth_frame2 = tk.Frame(root, bg=color_schemes[current_theme]["bg"])
auth_frame2.pack(pady=15)

metadata_button = StyledButton(auth_frame2, text="File Metadata", command=show_file_metadata,
                             font=("Arial", 12), 
                             bg=color_schemes[current_theme]["button_bg"], 
                             fg=color_schemes[current_theme]["button_fg"],
                             hover_bg=color_schemes[current_theme]["hover_bg"])
metadata_button.grid(row=0, column=0, padx=10)

show_process_button = StyledButton(auth_frame2, text="Process Info", command=show_process_info,
                                 font=("Arial", 12), 
                                 bg=color_schemes[current_theme]["button_bg"], 
                                 fg=color_schemes[current_theme]["button_fg"],
                                 hover_bg=color_schemes[current_theme]["hover_bg"])
show_process_button.grid(row=0, column=1, padx=10)

fragmentation_button = StyledButton(auth_frame2, text="Analyze Storage", command=analyze_fragmentation,
                                  font=("Arial", 12), 
                                  bg=color_schemes[current_theme]["button_bg"], 
                                  fg=color_schemes[current_theme]["button_fg"],
                                  hover_bg=color_schemes[current_theme]["hover_bg"])
fragmentation_button.grid(row=0, column=2, padx=10)

# File locking frame
lock_frame = tk.Frame(root, bg=color_schemes[current_theme]["bg"])
lock_frame.pack(pady=15)

lock_button = StyledButton(lock_frame, text="🔒 Lock File", command=lock_file, 
                         font=("Arial", 12), 
                         bg=color_schemes[current_theme]["accent3"], 
                         fg=color_schemes[current_theme]["button_fg"],
                         hover_bg="#A93226")
lock_button.grid(row=0, column=0, padx=10)

unlock_button = StyledButton(lock_frame, text="🔓 Unlock File", command=unlock_file, 
                           font=("Arial", 12), 
                           bg=color_schemes[current_theme]["accent1"], 
                           fg=color_schemes[current_theme]["button_fg"],
                           hover_bg="#1A5276")
unlock_button.grid(row=0, column=1, padx=10)

# Lock status label
lock_status_label = tk.Label(root, text="🔓 Unlocked", 
                           font=("Arial", 12, "bold"), 
                           fg=color_schemes[current_theme]["accent2"], 
                           bg=color_schemes[current_theme]["bg"])
lock_status_label.pack(pady=5)

# Add tooltips for better usability
create_tooltip(register_button, "Create a new user account")
create_tooltip(login_button, "Log in with your account")
create_tooltip(logout_button, "Log out from current session")
create_tooltip(upload_button, "Upload a file from your computer")
create_tooltip(download_button, "Download selected file to your computer")
create_tooltip(preview_button, "Preview the selected file")
create_tooltip(encrypt_button, "Encrypt the selected file with a password")
create_tooltip(decrypt_button, "Decrypt the selected file with your password")
create_tooltip(delete_button, "Delete the selected file permanently")
create_tooltip(rename_button, "Rename the selected file")
create_tooltip(metadata_button, "View metadata for the selected file")
create_tooltip(lock_button, "Lock the file to prevent modifications")
create_tooltip(unlock_button, "Unlock the file for editing")

# Initialize database
init_db()

# Set current_user_id to None initially
current_user_id = None

# Draw initial gradient background
root.update_idletasks()  # Update UI before drawing
draw_gradient_background()

# Add call to show the welcome animation
root.after(500, show_welcome_animation)

# Register event for window resize to redraw background
def on_resize(event):
    # Only redraw if window is fully visible
    if event.widget == root and root.winfo_viewable():
        draw_gradient_background()

root.bind("<Configure>", on_resize)

# Start the application
root.mainloop()
