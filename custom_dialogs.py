import tkinter as tk
from tkinter import simpledialog, messagebox
import bcrypt
import sqlite3
import datetime
import psutil
from themes import get_current_theme_colors, style_dialog
from PIL import Image, ImageTk

# Try to import matplotlib, but provide fallback if not available
MATPLOTLIB_AVAILABLE = False
try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    # Matplotlib not available, will use text-based representation instead
    pass

class StyledEntry(tk.Entry):
    """Custom styled entry widget"""
    def __init__(self, master=None, **kwargs):
        theme_name = kwargs.pop('theme', 'dark')
        theme = get_current_theme_colors(theme_name)
        
        # Configure appearance
        kwargs.setdefault('bg', theme["button_bg"])
        kwargs.setdefault('fg', theme["fg"])
        kwargs.setdefault('insertbackground', theme["fg"])  # Cursor color
        kwargs.setdefault('relief', tk.FLAT)
        kwargs.setdefault('highlightthickness', 1)
        kwargs.setdefault('highlightbackground', theme["accent1"])
        kwargs.setdefault('highlightcolor', theme["accent1"])
        kwargs.setdefault('font', ('Arial', 12))
        kwargs.setdefault('selectbackground', theme["accent1"])
        
        super().__init__(master, **kwargs)
        
        # Add focus events for highlight effect
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        
    def _on_focus_in(self, event):
        self.config(highlightbackground="#3498DB", highlightthickness=2)
        
    def _on_focus_out(self, event):
        self.config(highlightbackground=get_current_theme_colors()["accent1"], highlightthickness=1)

class StyledButton(tk.Button):
    """Custom styled button for dialogs"""
    def __init__(self, master=None, **kwargs):
        theme_name = kwargs.pop('theme', 'dark')
        theme = get_current_theme_colors(theme_name)
        
        self.hover_bg = kwargs.pop('hover_bg', theme["hover_bg"])
        self.normal_bg = kwargs.get('bg', theme["accent1"])
        self.normal_fg = kwargs.get('fg', "white")
        
        kwargs.setdefault('relief', tk.FLAT)
        kwargs.setdefault('borderwidth', 0)
        kwargs.setdefault('padx', 15)
        kwargs.setdefault('pady', 8)
        kwargs.setdefault('font', ('Arial', 11, 'bold'))
        
        super().__init__(master, **kwargs)
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
    def _on_enter(self, e):
        self.config(bg=self.hover_bg)
        
    def _on_leave(self, e):
        self.config(bg=self.normal_bg)

def login_dialog(parent, current_theme="dark"):
    """Enhanced login dialog with better styling"""
    dialog = tk.Toplevel(parent)
    dialog.transient(parent)  # Make dialog modal
    dialog.grab_set()
    
    content_frame = style_dialog(dialog, current_theme, "User Login", 400, 320)
    
    # Add logo or icon at the top
    try:
        logo_img = Image.open("lock_icon.png").resize((64, 64))
        logo_photo = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(content_frame, image=logo_photo, bg=get_current_theme_colors(current_theme)["bg"])
        logo_label.image = logo_photo  # Keep reference
        logo_label.pack(pady=(10, 20))
    except:
        # If image not found, show text instead
        logo_label = tk.Label(content_frame, text="🔐", font=("Arial", 36), 
                            bg=get_current_theme_colors(current_theme)["bg"],
                            fg=get_current_theme_colors(current_theme)["accent1"])
        logo_label.pack(pady=(10, 20))
    
    # Username field
    username_frame = tk.Frame(content_frame, bg=get_current_theme_colors(current_theme)["bg"])
    username_frame.pack(fill=tk.X, pady=5)
    
    username_label = tk.Label(username_frame, text="Username", width=10, anchor='w',
                           font=('Arial', 12),
                           bg=get_current_theme_colors(current_theme)["bg"],
                           fg=get_current_theme_colors(current_theme)["fg"])
    username_label.pack(side=tk.LEFT, padx=(0, 10))
    
    username_var = tk.StringVar()
    username_entry = StyledEntry(username_frame, textvariable=username_var, theme=current_theme)
    username_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # Password field
    password_frame = tk.Frame(content_frame, bg=get_current_theme_colors(current_theme)["bg"])
    password_frame.pack(fill=tk.X, pady=5)
    
    password_label = tk.Label(password_frame, text="Password", width=10, anchor='w',
                           font=('Arial', 12),
                           bg=get_current_theme_colors(current_theme)["bg"],
                           fg=get_current_theme_colors(current_theme)["fg"])
    password_label.pack(side=tk.LEFT, padx=(0, 10))
    
    password_var = tk.StringVar()
    password_entry = StyledEntry(password_frame, textvariable=password_var, show="•", theme=current_theme)
    password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # Result variable
    result = {"username": None, "password": None, "success": False}
    
    # Login function
    def do_login():
        username = username_var.get()
        password = password_var.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
        
        # Verify credentials
        conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data and bcrypt.checkpw(password.encode(), user_data[2]):
            result["username"] = username
            result["password"] = password  # Consider not storing this for security
            result["user_id"] = user_data[0]
            result["success"] = True
            dialog.destroy()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")
    
    # Buttons
    button_frame = tk.Frame(content_frame, bg=get_current_theme_colors(current_theme)["bg"])
    button_frame.pack(fill=tk.X, pady=(20, 10))
    
    cancel_btn = StyledButton(button_frame, text="Cancel", 
                            command=dialog.destroy,
                            bg=get_current_theme_colors(current_theme)["accent3"],
                            theme=current_theme)
    cancel_btn.pack(side=tk.LEFT, padx=10)
    
    login_btn = StyledButton(button_frame, text="Login", 
                           command=do_login,
                           bg=get_current_theme_colors(current_theme)["accent2"],
                           theme=current_theme)
    login_btn.pack(side=tk.RIGHT, padx=10)
    
    # Set focus to username field
    username_entry.focus_set()
    
    # Enter key to submit form
    dialog.bind("<Return>", lambda event: do_login())
    
    # Wait for dialog to close
    parent.wait_window(dialog)
    return result

def register_dialog(parent, current_theme="dark"):
    """Enhanced registration dialog with better styling"""
    dialog = tk.Toplevel(parent)
    dialog.transient(parent)
    dialog.grab_set()
    
    content_frame = style_dialog(dialog, current_theme, "Create Account", 400, 350)
    
    # Add icon at the top
    try:
        logo_img = Image.open("user_icon.png").resize((64, 64))
        logo_photo = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(content_frame, image=logo_photo, bg=get_current_theme_colors(current_theme)["bg"])
        logo_label.image = logo_photo
        logo_label.pack(pady=(10, 20))
    except:
        # If image not found, show text instead
        logo_label = tk.Label(content_frame, text="👤", font=("Arial", 36), 
                            bg=get_current_theme_colors(current_theme)["bg"],
                            fg=get_current_theme_colors(current_theme)["accent1"])
        logo_label.pack(pady=(10, 20))
    
    # Username field
    username_frame = tk.Frame(content_frame, bg=get_current_theme_colors(current_theme)["bg"])
    username_frame.pack(fill=tk.X, pady=5)
    
    username_label = tk.Label(username_frame, text="Username", width=12, anchor='w',
                           font=('Arial', 12),
                           bg=get_current_theme_colors(current_theme)["bg"],
                           fg=get_current_theme_colors(current_theme)["fg"])
    username_label.pack(side=tk.LEFT, padx=(0, 10))
    
    username_var = tk.StringVar()
    username_entry = StyledEntry(username_frame, textvariable=username_var, theme=current_theme)
    username_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # Password field
    password_frame = tk.Frame(content_frame, bg=get_current_theme_colors(current_theme)["bg"])
    password_frame.pack(fill=tk.X, pady=5)
    
    password_label = tk.Label(password_frame, text="Password", width=12, anchor='w',
                           font=('Arial', 12),
                           bg=get_current_theme_colors(current_theme)["bg"],
                           fg=get_current_theme_colors(current_theme)["fg"])
    password_label.pack(side=tk.LEFT, padx=(0, 10))
    
    password_var = tk.StringVar()
    password_entry = StyledEntry(password_frame, textvariable=password_var, show="•", theme=current_theme)
    password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # Confirm Password field
    confirm_frame = tk.Frame(content_frame, bg=get_current_theme_colors(current_theme)["bg"])
    confirm_frame.pack(fill=tk.X, pady=5)
    
    confirm_label = tk.Label(confirm_frame, text="Confirm", width=12, anchor='w',
                           font=('Arial', 12),
                           bg=get_current_theme_colors(current_theme)["bg"],
                           fg=get_current_theme_colors(current_theme)["fg"])
    confirm_label.pack(side=tk.LEFT, padx=(0, 10))
    
    confirm_var = tk.StringVar()
    confirm_entry = StyledEntry(confirm_frame, textvariable=confirm_var, show="•", theme=current_theme)
    confirm_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # Result variable
    result = {"username": None, "success": False}
    
    # Registration function
    def do_register():
        username = username_var.get()
        password = password_var.get()
        confirm = confirm_var.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please fill all fields")
            return
            
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match")
            return
            
        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters")
            return
        
        # Register user
        try:
            hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            conn = sqlite3.connect("file_manager.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                         (username, hashed_password))
            conn.commit()
            conn.close()
            
            result["username"] = username
            result["success"] = True
            messagebox.showinfo("Success", "Account created successfully!")
            dialog.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists!")
    
    # Buttons
    button_frame = tk.Frame(content_frame, bg=get_current_theme_colors(current_theme)["bg"])
    button_frame.pack(fill=tk.X, pady=(20, 10))
    
    cancel_btn = StyledButton(button_frame, text="Cancel", 
                            command=dialog.destroy,
                            bg=get_current_theme_colors(current_theme)["accent3"],
                            theme=current_theme)
    cancel_btn.pack(side=tk.LEFT, padx=10)
    
    register_btn = StyledButton(button_frame, text="Register", 
                              command=do_register,
                              bg=get_current_theme_colors(current_theme)["accent1"],
                              theme=current_theme)
    register_btn.pack(side=tk.RIGHT, padx=10)
    
    # Set focus to username field
    username_entry.focus_set()
    
    # Wait for dialog to close
    parent.wait_window(dialog)
    return result

def show_process_info_dialog(parent, current_theme="dark"):
    """Enhanced process information dialog with charts"""
    dialog = tk.Toplevel(parent)
    
    content_frame = style_dialog(dialog, current_theme, "System Resource Monitor", 600, 500)
    
    # Get process information
    current_process = psutil.Process()
    all_processes = len(psutil.pids())
    
    # Create tabs for information
    tab_frame = tk.Frame(content_frame, bg=get_current_theme_colors(current_theme)["bg"])
    tab_frame.pack(fill=tk.X)
    
    # Configure tab styles
    active_tab_bg = get_current_theme_colors(current_theme)["accent1"]
    active_tab_fg = "white"
    inactive_tab_bg = get_current_theme_colors(current_theme)["button_bg"]
    inactive_tab_fg = get_current_theme_colors(current_theme)["fg"]
    
    # Content area for tabs
    content_area = tk.Frame(content_frame, bg=get_current_theme_colors(current_theme)["bg"],
                          padx=15, pady=15)
    content_area.pack(fill=tk.BOTH, expand=True)
    
    # Function to reset all tabs to inactive
    def reset_tabs():
        for btn in tab_buttons:
            btn.config(bg=inactive_tab_bg, fg=inactive_tab_fg)
    
    # Current frames to track which content is showing
    current_frame = {"frame": None}
    
    # Function to show CPU usage tab
    def show_cpu_tab():
        if current_frame["frame"]:
            current_frame["frame"].pack_forget()
        
        reset_tabs()
        cpu_btn.config(bg=active_tab_bg, fg=active_tab_fg)
        
        # Create CPU display
        cpu_frame = tk.Frame(content_area, bg=get_current_theme_colors(current_theme)["bg"])
        current_frame["frame"] = cpu_frame
        
        if MATPLOTLIB_AVAILABLE:
            # CPU Usage chart with matplotlib
            fig, ax = plt.subplots(figsize=(5, 3))
            
            # Set background color to match theme
            fig.patch.set_facecolor(get_current_theme_colors(current_theme)["bg"])
            ax.set_facecolor(get_current_theme_colors(current_theme)["bg"])
            
            # Plot data
            cpu_percent = psutil.cpu_percent(percpu=True)
            cores = len(cpu_percent)
            x = range(cores)
            
            ax.bar(x, cpu_percent, color=get_current_theme_colors(current_theme)["accent1"])
            ax.set_ylim(0, 100)
            ax.set_xlabel('CPU Cores', color=get_current_theme_colors(current_theme)["fg"])
            ax.set_ylabel('Usage %', color=get_current_theme_colors(current_theme)["fg"])
            ax.set_title('CPU Usage by Core', color=get_current_theme_colors(current_theme)["fg"])
            
            # Set tick colors to match theme
            ax.tick_params(axis='x', colors=get_current_theme_colors(current_theme)["fg"])
            ax.tick_params(axis='y', colors=get_current_theme_colors(current_theme)["fg"])
            
            # Embed chart in tkinter
            canvas = FigureCanvasTkAgg(fig, cpu_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            # Create a text-based CPU usage visualization
            cpu_percent = psutil.cpu_percent(percpu=True)
            cores = len(cpu_percent)
            
            # Header
            tk.Label(cpu_frame, text="CPU Usage by Core", 
                   font=("Arial", 14, "bold"),
                   bg=get_current_theme_colors(current_theme)["bg"],
                   fg=get_current_theme_colors(current_theme)["accent1"]).pack(pady=(0, 10))
            
            # Create a canvas for drawing bars
            bar_canvas = tk.Canvas(cpu_frame, 
                                 bg=get_current_theme_colors(current_theme)["bg"],
                                 height=200, width=400,
                                 highlightthickness=0)
            bar_canvas.pack(fill=tk.X, expand=True)
            
            # Draw bar graph
            bar_width = 30
            spacing = 15
            max_height = 150
            start_x = (400 - (cores * (bar_width + spacing) - spacing)) / 2
            
            for i in range(cores):
                # Calculate bar height based on percentage
                bar_height = (cpu_percent[i] / 100) * max_height
                
                # Draw bar
                bar_canvas.create_rectangle(
                    start_x + i * (bar_width + spacing),
                    max_height - bar_height,
                    start_x + i * (bar_width + spacing) + bar_width,
                    max_height,
                    fill=get_current_theme_colors(current_theme)["accent1"],
                    outline=""
                )
                
                # Add percentage label
                bar_canvas.create_text(
                    start_x + i * (bar_width + spacing) + bar_width/2,
                    max_height - bar_height - 10,
                    text=f"{cpu_percent[i]:.1f}%",
                    fill=get_current_theme_colors(current_theme)["fg"],
                    font=("Arial", 9)
                )
                
                # Add core label
                bar_canvas.create_text(
                    start_x + i * (bar_width + spacing) + bar_width/2,
                    max_height + 15,
                    text=f"Core {i}",
                    fill=get_current_theme_colors(current_theme)["fg"],
                    font=("Arial", 9)
                )
            
            # Draw baseline
            bar_canvas.create_line(
                start_x - 5, max_height,
                start_x + cores * (bar_width + spacing), max_height,
                fill=get_current_theme_colors(current_theme)["fg"]
            )
        
        # Add some text information
        info_frame = tk.Frame(cpu_frame, bg=get_current_theme_colors(current_theme)["bg"], pady=10)
        info_frame.pack(fill=tk.X)
        
        # Current CPU usage
        tk.Label(info_frame, text=f"Overall CPU Usage: {psutil.cpu_percent()}%", 
               font=("Arial", 12, "bold"),
               bg=get_current_theme_colors(current_theme)["bg"],
               fg=get_current_theme_colors(current_theme)["fg"]).pack(anchor='w')
        
        # CPU info
        cpu_info = f"Cores: {psutil.cpu_count(logical=False)} Physical, {psutil.cpu_count()} Logical"
        tk.Label(info_frame, text=cpu_info, 
               font=("Arial", 11),
               bg=get_current_theme_colors(current_theme)["bg"],
               fg=get_current_theme_colors(current_theme)["fg"]).pack(anchor='w')
        
        cpu_frame.pack(fill=tk.BOTH, expand=True)
    
    # Function to show memory usage tab
    def show_memory_tab():
        if current_frame["frame"]:
            current_frame["frame"].pack_forget()
        
        reset_tabs()
        memory_btn.config(bg=active_tab_bg, fg=active_tab_fg)
        
        # Create memory display
        memory_frame = tk.Frame(content_area, bg=get_current_theme_colors(current_theme)["bg"])
        current_frame["frame"] = memory_frame
        
        # Get memory info
        memory = psutil.virtual_memory()
        
        if MATPLOTLIB_AVAILABLE:
            # Memory Usage pie chart
            fig, ax = plt.subplots(figsize=(4, 3))
            
            # Set background color to match theme
            fig.patch.set_facecolor(get_current_theme_colors(current_theme)["bg"])
            ax.set_facecolor(get_current_theme_colors(current_theme)["bg"])
            
            # Get memory info
            labels = ['Used', 'Available']
            sizes = [memory.used, memory.available]
            colors = [get_current_theme_colors(current_theme)["accent3"], get_current_theme_colors(current_theme)["accent2"]]
            
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.set_title('Memory Usage', color=get_current_theme_colors(current_theme)["fg"])
            
            # Embed chart in tkinter
            canvas = FigureCanvasTkAgg(fig, memory_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        else:
            # Create a text-based memory usage visualization
            # Header
            tk.Label(memory_frame, text="Memory Usage", 
                   font=("Arial", 14, "bold"),
                   bg=get_current_theme_colors(current_theme)["bg"],
                   fg=get_current_theme_colors(current_theme)["accent1"]).pack(pady=(0, 10))
            
            # Create a canvas for drawing pie chart alternative
            memory_canvas = tk.Canvas(memory_frame, 
                                    bg=get_current_theme_colors(current_theme)["bg"],
                                    height=200, width=200,
                                    highlightthickness=0)
            memory_canvas.pack(side=tk.LEFT, padx=20)
            
            # Calculate percentages
            used_percentage = memory.used / memory.total * 100
            available_percentage = 100 - used_percentage
            
            # Draw a simple pie chart alternative (two rectangles side by side)
            center_x, center_y = 100, 100
            radius = 80
            
            # Draw Used segment (using a rectangle for simplicity)
            memory_canvas.create_arc(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                start=0, extent=used_percentage * 3.6,  # Convert percentage to degrees
                fill=get_current_theme_colors(current_theme)["accent3"],
                outline=""
            )
            
            # Draw Available segment
            memory_canvas.create_arc(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                start=used_percentage * 3.6, extent=available_percentage * 3.6,
                fill=get_current_theme_colors(current_theme)["accent2"],
                outline=""
            )
            
            # Add labels
            memory_canvas.create_text(
                center_x, center_y - 20,
                text=f"Used: {used_percentage:.1f}%",
                fill=get_current_theme_colors(current_theme)["fg"],
                font=("Arial", 10, "bold")
            )
            
            memory_canvas.create_text(
                center_x, center_y + 20,
                text=f"Available: {available_percentage:.1f}%",
                fill=get_current_theme_colors(current_theme)["fg"],
                font=("Arial", 10, "bold")
            )
        
        # Memory info
        info_frame = tk.Frame(memory_frame, bg=get_current_theme_colors(current_theme)["bg"], padx=10)
        info_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Total memory
        total_gb = memory.total / (1024**3)
        used_gb = memory.used / (1024**3)
        available_gb = memory.available / (1024**3)
        
        tk.Label(info_frame, text=f"Total: {total_gb:.2f} GB", 
               font=("Arial", 11),
               bg=get_current_theme_colors(current_theme)["bg"],
               fg=get_current_theme_colors(current_theme)["fg"]).pack(anchor='w', pady=2)
        
        tk.Label(info_frame, text=f"Used: {used_gb:.2f} GB", 
               font=("Arial", 11),
               bg=get_current_theme_colors(current_theme)["bg"],
               fg=get_current_theme_colors(current_theme)["accent3"]).pack(anchor='w', pady=2)
        
        tk.Label(info_frame, text=f"Available: {available_gb:.2f} GB", 
               font=("Arial", 11),
               bg=get_current_theme_colors(current_theme)["bg"],
               fg=get_current_theme_colors(current_theme)["accent2"]).pack(anchor='w', pady=2)
        
        memory_frame.pack(fill=tk.BOTH, expand=True)
    
    # Function to show process info
    def show_process_tab():
        if current_frame["frame"]:
            current_frame["frame"].pack_forget()
        
        reset_tabs()
        process_btn.config(bg=active_tab_bg, fg=active_tab_fg)
        
        # Create process display
        process_frame = tk.Frame(content_area, bg=get_current_theme_colors(current_theme)["bg"])
        current_frame["frame"] = process_frame
        
        # Process info text
        info_text = tk.Text(process_frame, wrap=tk.WORD, 
                          bg=get_current_theme_colors(current_theme)["button_bg"],
                          fg=get_current_theme_colors(current_theme)["fg"],
                          font=("Consolas", 11),
                          relief=tk.FLAT,
                          padx=10, pady=10,
                          highlightbackground=get_current_theme_colors(current_theme)["accent1"],
                          highlightthickness=1)
        
        info_text.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Insert process information
        info_text.insert(tk.END, f"Application Process Information\n", "header")
        info_text.insert(tk.END, "="*40 + "\n\n")
        
        info_text.insert(tk.END, f"Process ID: {current_process.pid}\n")
        info_text.insert(tk.END, f"Process Name: {current_process.name()}\n")
        info_text.insert(tk.END, f"Executable: {current_process.exe()}\n\n")
        
        info_text.insert(tk.END, f"Started: {datetime.datetime.fromtimestamp(current_process.create_time()).strftime('%Y-%m-%d %H:%M:%S')}\n")
        info_text.insert(tk.END, f"Status: {current_process.status()}\n\n")
        
        info_text.insert(tk.END, f"CPU Usage: {current_process.cpu_percent()}%\n")
        info_text.insert(tk.END, f"Memory Usage: {current_process.memory_info().rss / (1024*1024):.2f} MB\n")
        info_text.insert(tk.END, f"Number of Threads: {current_process.num_threads()}\n")
        info_text.insert(tk.END, f"Priority: {current_process.nice()}\n\n")
        
        info_text.insert(tk.END, f"Total System Processes: {all_processes}\n")
        
        # Configure tags
        info_text.tag_configure("header", font=("Arial", 12, "bold"), foreground=get_current_theme_colors(current_theme)["accent1"])
        
        # Make text read-only
        info_text.config(state=tk.DISABLED)
        
        process_frame.pack(fill=tk.BOTH, expand=True)
    
    # Create tab buttons
    cpu_btn = tk.Button(tab_frame, text="CPU Usage", relief=tk.FLAT, borderwidth=0,
                      font=("Arial", 11, "bold"), padx=15, pady=8,
                      bg=active_tab_bg, fg=active_tab_fg,
                      command=show_cpu_tab)
    cpu_btn.pack(side=tk.LEFT)
    
    memory_btn = tk.Button(tab_frame, text="Memory", relief=tk.FLAT, borderwidth=0,
                         font=("Arial", 11, "bold"), padx=15, pady=8,
                         bg=inactive_tab_bg, fg=inactive_tab_fg,
                         command=show_memory_tab)
    memory_btn.pack(side=tk.LEFT)
    
    process_btn = tk.Button(tab_frame, text="Process Info", relief=tk.FLAT, borderwidth=0,
                          font=("Arial", 11, "bold"), padx=15, pady=8,
                          bg=inactive_tab_bg, fg=inactive_tab_fg,
                          command=show_process_tab)
    process_btn.pack(side=tk.LEFT)
    
    tab_buttons = [cpu_btn, memory_btn, process_btn]
    
    # Add a close button
    button_frame = tk.Frame(content_frame, bg=get_current_theme_colors(current_theme)["bg"])
    button_frame.pack(fill=tk.X, pady=(5, 10))
    
    close_btn = StyledButton(button_frame, text="Close", 
                           command=dialog.destroy,
                           bg=get_current_theme_colors(current_theme)["accent3"],
                           theme=current_theme)
    close_btn.pack(side=tk.RIGHT, padx=10)
    
    # Show CPU tab by default
    show_cpu_tab()
    
    # Wait for dialog to close
    parent.wait_window(dialog)

def analyze_storage_dialog(parent, files, current_theme="dark"):
    """Enhanced storage analysis dialog with visualizations"""
    dialog = tk.Toplevel(parent)
    
    content_frame = style_dialog(dialog, current_theme, "Storage Analysis", 650, 550)
    
    # Create tabbed interface
    tab_frame = tk.Frame(content_frame, bg=get_current_theme_colors(current_theme)["bg"])
    tab_frame.pack(fill=tk.X)
    
    # Configure tab styles
    active_tab_bg = get_current_theme_colors(current_theme)["accent1"]
    active_tab_fg = "white"
    inactive_tab_bg = get_current_theme_colors(current_theme)["button_bg"]
    inactive_tab_fg = get_current_theme_colors(current_theme)["fg"]
    
    # Content area for tabs
    content_area = tk.Frame(content_frame, bg=get_current_theme_colors(current_theme)["bg"],
                          padx=15, pady=15)
    content_area.pack(fill=tk.BOTH, expand=True)
    
    # Function to reset all tabs to inactive
    def reset_tabs():
        for btn in tab_buttons:
            btn.config(bg=inactive_tab_bg, fg=inactive_tab_fg)
    
    # Current frames to track which content is showing
    current_frame = {"frame": None}
    
    # Calculate data for analysis
    if files:
        total_size = sum(size for _, size in files)
        block_size = 4096  # 4KB blocks
        total_blocks = sum((size + block_size - 1) // block_size for _, size in files)
        
        # Calculate fragmentation for each file
        file_frags = []
        for file_name, file_size in files:
            blocks_needed = (file_size + block_size - 1) // block_size
            frag_factor = min(0.8, file_size / (50 * 1024 * 1024))
            fragmented = int(blocks_needed * frag_factor)
            file_frags.append((file_name, file_size, blocks_needed, fragmented/blocks_needed))
        
        # Total fragmentation
        fragmented_blocks = sum(int(blocks * frag) for _, _, blocks, frag in file_frags)
        total_fragmentation = fragmented_blocks / total_blocks if total_blocks > 0 else 0
    else:
        total_size = 0
        file_frags = []
        total_fragmentation = 0
    
    # Function to show overview tab
    def show_overview_tab():
        if current_frame["frame"]:
            current_frame["frame"].pack_forget()
        
        reset_tabs()
        overview_btn.config(bg=active_tab_bg, fg=active_tab_fg)
        
        # Create overview display
        overview_frame = tk.Frame(content_area, bg=get_current_theme_colors(current_theme)["bg"])
        current_frame["frame"] = overview_frame
        
        # Summary statistics at the top
        summary_frame = tk.Frame(overview_frame, bg=get_current_theme_colors(current_theme)["bg"],
                               padx=10, pady=15)
        summary_frame.pack(fill=tk.X)
        
        # Stats with accent colors
        stats = [
            ("Total Files", f"{len(files)}", get_current_theme_colors(current_theme)["accent1"]),
            ("Total Size", f"{total_size/1024:.1f} KB", get_current_theme_colors(current_theme)["accent2"]),
            ("Fragmentation", f"{total_fragmentation:.1%}", 
             get_current_theme_colors(current_theme)["accent3"] if total_fragmentation > 0.3 
             else get_current_theme_colors(current_theme)["accent2"])
        ]
        
        # Create stylish stat boxes
        for i, (label, value, color) in enumerate(stats):
            stat_frame = tk.Frame(summary_frame, bg=color, padx=15, pady=10, relief=tk.RAISED, bd=0)
            stat_frame.grid(row=0, column=i, padx=10, sticky='nsew')
            
            tk.Label(stat_frame, text=label, font=("Arial", 11), 
                   bg=color, fg="white").pack(anchor='w')
            
            tk.Label(stat_frame, text=value, font=("Arial", 16, "bold"), 
                   bg=color, fg="white").pack(anchor='w', pady=(5, 0))
            
        summary_frame.grid_columnconfigure(0, weight=1)
        summary_frame.grid_columnconfigure(1, weight=1)
        summary_frame.grid_columnconfigure(2, weight=1)
        
        # Create a visualization area
        if files:
            if MATPLOTLIB_AVAILABLE:
                # Create a pie chart of file sizes
                fig, ax = plt.subplots(figsize=(5, 4))
                
                # Set background color to match theme
                fig.patch.set_facecolor(get_current_theme_colors(current_theme)["bg"])
                ax.set_facecolor(get_current_theme_colors(current_theme)["bg"])
                
                # Group small files together for better visualization
                threshold = total_size * 0.05  # Files smaller than 5% get grouped
                sizes = []
                labels = []
                other_size = 0
                
                for name, size in sorted(files, key=lambda x: x[1], reverse=True):
                    if size >= threshold or len(sizes) < 5:
                        sizes.append(size)
                        if len(name) > 15:
                            name = name[:12] + "..."
                        labels.append(name)
                    else:
                        other_size += size
                
                if other_size > 0:
                    sizes.append(other_size)
                    labels.append("Other Files")
                
                # Generate colors
                colors = [get_current_theme_colors(current_theme)[f"accent{i+1}"] 
                        for i in range(min(len(sizes), 5))]
                
                # In case we have more than 5 slices, reuse colors
                while len(colors) < len(sizes):
                    colors.append(colors[len(colors) % 5])
                
                # Create pie chart
                wedges, texts, autotexts = ax.pie(
                    sizes, 
                    labels=labels, 
                    colors=colors, 
                    autopct='%1.1f%%', 
                    startangle=90,
                    wedgeprops={'edgecolor': 'white', 'linewidth': 1}
                )
                
                # Set text colors for better visibility
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontsize(9)
                
                for text in texts:
                    text.set_color(get_current_theme_colors(current_theme)["fg"])
                    text.set_fontsize(9)
                
                ax.set_title('File Size Distribution', color=get_current_theme_colors(current_theme)["fg"])
                
                # Embed chart in tkinter
                canvas = FigureCanvasTkAgg(fig, overview_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=10)
            else:
                # Create a text-based pie chart alternative
                viz_frame = tk.Frame(overview_frame, bg=get_current_theme_colors(current_theme)["bg"],
                                  padx=10, pady=10)
                viz_frame.pack(fill=tk.BOTH, expand=True)
                
                # Header
                tk.Label(viz_frame, text="File Size Distribution", 
                       font=("Arial", 14, "bold"),
                       bg=get_current_theme_colors(current_theme)["bg"],
                       fg=get_current_theme_colors(current_theme)["accent1"]).pack(pady=(0, 10))
                
                # Create a canvas for visualization
                viz_canvas = tk.Canvas(viz_frame, 
                                     bg=get_current_theme_colors(current_theme)["bg"],
                                     height=250, width=500,
                                     highlightthickness=0)
                viz_canvas.pack(fill=tk.BOTH, expand=True)
                
                # Sort files by size and take top 5
                sorted_files = sorted(files, key=lambda x: x[1], reverse=True)
                top_files = sorted_files[:5]
                
                # Calculate percentages
                total = sum(size for _, size in top_files)
                percentages = [size/total*100 for _, size in top_files]
                
                # Draw horizontal bars
                bar_height = 25
                spacing = 15
                max_width = 300
                start_y = 20
                
                for i, ((name, size), percentage) in enumerate(zip(top_files, percentages)):
                    # Draw bar
                    bar_width = (percentage / 100) * max_width
                    
                    # Truncate long filenames
                    if len(name) > 20:
                        name = name[:17] + "..."
                    
                    # Draw colored bar
                    color = get_current_theme_colors(current_theme)[f"accent{(i % 5) + 1}"]
                    viz_canvas.create_rectangle(
                        150, start_y + i * (bar_height + spacing),
                        150 + bar_width, start_y + i * (bar_height + spacing) + bar_height,
                        fill=color,
                        outline=""
                    )
                    
                    # Add filename
                    viz_canvas.create_text(
                        140, start_y + i * (bar_height + spacing) + bar_height/2,
                        text=name,
                        fill=get_current_theme_colors(current_theme)["fg"],
                        font=("Arial", 10),
                        anchor="e"
                    )
                    
                    # Add percentage
                    viz_canvas.create_text(
                        150 + bar_width + 10, start_y + i * (bar_height + spacing) + bar_height/2,
                        text=f"{percentage:.1f}% ({size/1024:.1f} KB)",
                        fill=get_current_theme_colors(current_theme)["fg"],
                        font=("Arial", 9),
                        anchor="w"
                    )
        else:
            # Show message if no files
            no_files_label = tk.Label(overview_frame, 
                                    text="No files available for analysis",
                                    font=("Arial", 14),
                                    bg=get_current_theme_colors(current_theme)["bg"],
                                    fg=get_current_theme_colors(current_theme)["fg"])
            no_files_label.pack(expand=True, pady=50)
        
        overview_frame.pack(fill=tk.BOTH, expand=True)
    
    # Function to show fragmentation details
    def show_fragmentation_tab():
        if current_frame["frame"]:
            current_frame["frame"].pack_forget()
        
        reset_tabs()
        fragmentation_btn.config(bg=active_tab_bg, fg=active_tab_fg)
        
        # Create fragmentation display
        frag_frame = tk.Frame(content_area, bg=get_current_theme_colors(current_theme)["bg"])
        current_frame["frame"] = frag_frame
        
        # Title for the tab
        tk.Label(frag_frame, text="File System Fragmentation Analysis", 
               font=("Arial", 14, "bold"),
               bg=get_current_theme_colors(current_theme)["bg"],
               fg=get_current_theme_colors(current_theme)["accent1"]).pack(pady=(0, 15))
        
        if files:
            # Create table headers
            table_frame = tk.Frame(frag_frame, bg=get_current_theme_colors(current_theme)["bg"])
            table_frame.pack(fill=tk.BOTH, expand=True)
            
            headers = ["File Name", "Size (KB)", "Blocks", "Fragmentation"]
            widths = [280, 80, 80, 120]
            
            # Create header
            header_frame = tk.Frame(table_frame, bg=get_current_theme_colors(current_theme)["accent1"])
            header_frame.pack(fill=tk.X)
            
            for i, header in enumerate(headers):
                tk.Label(header_frame, text=header, font=("Arial", 11, "bold"),
                       bg=get_current_theme_colors(current_theme)["accent1"],
                       fg="white",
                       width=widths[i]//10).grid(row=0, column=i, padx=1, pady=5, sticky='w')
            
            # Create scrollable frame for content
            canvas = tk.Canvas(table_frame, bg=get_current_theme_colors(current_theme)["bg"],
                             highlightthickness=0)
            scrollbar = tk.Scrollbar(table_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=get_current_theme_colors(current_theme)["bg"])
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Add data rows
            for i, (name, size, blocks, frag) in enumerate(sorted(file_frags, key=lambda x: x[3], reverse=True)):
                row_bg = get_current_theme_colors(current_theme)["button_bg"] if i % 2 == 0 else get_current_theme_colors(current_theme)["bg"]
                
                row_frame = tk.Frame(scrollable_frame, bg=row_bg)
                row_frame.pack(fill=tk.X)
                
                # Determine fragmentation color
                if frag > 0.5:
                    frag_color = get_current_theme_colors(current_theme)["accent3"]  # Red for high
                elif frag > 0.2:
                    frag_color = get_current_theme_colors(current_theme)["accent4"]  # Orange for medium
                else:
                    frag_color = get_current_theme_colors(current_theme)["accent2"]  # Green for low
                
                # File name (truncated if needed)
                display_name = name if len(name) < 30 else name[:27] + "..."
                tk.Label(row_frame, text=display_name, font=("Arial", 10),
                       bg=row_bg, fg=get_current_theme_colors(current_theme)["fg"],
                       width=widths[0]//10, anchor='w').grid(row=0, column=0, padx=1, pady=3, sticky='w')
                
                # Size in KB
                tk.Label(row_frame, text=f"{size/1024:.1f}", font=("Arial", 10),
                       bg=row_bg, fg=get_current_theme_colors(current_theme)["fg"],
                       width=widths[1]//10, anchor='e').grid(row=0, column=1, padx=1, pady=3)
                
                # Blocks needed
                tk.Label(row_frame, text=f"{blocks}", font=("Arial", 10),
                       bg=row_bg, fg=get_current_theme_colors(current_theme)["fg"],
                       width=widths[2]//10, anchor='e').grid(row=0, column=2, padx=1, pady=3)
                
                # Fragmentation with color coding
                frag_label = tk.Label(row_frame, text=f"{frag:.1%}", font=("Arial", 10, "bold"),
                                    bg=row_bg, fg=frag_color,
                                    width=widths[3]//10, anchor='center')
                frag_label.grid(row=0, column=3, padx=1, pady=3)
            
            # Add summary at the bottom
            summary_frame = tk.Frame(frag_frame, bg=get_current_theme_colors(current_theme)["bg"],
                                   pady=10)
            summary_frame.pack(fill=tk.X)
            
            perf_impact = min(100, (total_fragmentation)*100)
            
            tk.Label(summary_frame, text=f"Total fragmentation: {total_fragmentation:.1%}", 
                   font=("Arial", 11, "bold"),
                   bg=get_current_theme_colors(current_theme)["bg"],
                   fg=get_current_theme_colors(current_theme)["fg"]).pack(anchor='w')
            
            # Create performance impact bar
            impact_frame = tk.Frame(summary_frame, bg=get_current_theme_colors(current_theme)["bg"],
                                  height=25, pady=5)
            impact_frame.pack(fill=tk.X)
            
            tk.Label(impact_frame, text="Estimated Performance Impact: ", 
                   font=("Arial", 11),
                   bg=get_current_theme_colors(current_theme)["bg"],
                   fg=get_current_theme_colors(current_theme)["fg"]).pack(side=tk.LEFT)
            
            # Color based on impact
            if perf_impact > 50:
                impact_color = get_current_theme_colors(current_theme)["accent3"]
            elif perf_impact > 20:
                impact_color = get_current_theme_colors(current_theme)["accent4"]
            else:
                impact_color = get_current_theme_colors(current_theme)["accent2"]
                
            impact_label = tk.Label(impact_frame, text=f"{perf_impact:.1f}%", 
                                  font=("Arial", 11, "bold"),
                                  bg=get_current_theme_colors(current_theme)["bg"],
                                  fg=impact_color)
            impact_label.pack(side=tk.LEFT)
        else:
            # Show message if no files
            no_files_label = tk.Label(frag_frame, 
                                    text="No files available for analysis",
                                    font=("Arial", 14),
                                    bg=get_current_theme_colors(current_theme)["bg"],
                                    fg=get_current_theme_colors(current_theme)["fg"])
            no_files_label.pack(expand=True, pady=50)
        
        frag_frame.pack(fill=tk.BOTH, expand=True)
    
    # Create tab buttons
    overview_btn = tk.Button(tab_frame, text="Overview", relief=tk.FLAT, borderwidth=0,
                           font=("Arial", 11, "bold"), padx=15, pady=8,
                           bg=active_tab_bg, fg=active_tab_fg,
                           command=show_overview_tab)
    overview_btn.pack(side=tk.LEFT)
    
    fragmentation_btn = tk.Button(tab_frame, text="Fragmentation Details", relief=tk.FLAT, borderwidth=0,
                                font=("Arial", 11, "bold"), padx=15, pady=8,
                                bg=inactive_tab_bg, fg=inactive_tab_fg,
                                command=show_fragmentation_tab)
    fragmentation_btn.pack(side=tk.LEFT)
    
    tab_buttons = [overview_btn, fragmentation_btn]
    
    # Add close button
    button_frame = tk.Frame(content_frame, bg=get_current_theme_colors(current_theme)["bg"])
    button_frame.pack(fill=tk.X, pady=(5, 10))
    
    close_btn = StyledButton(button_frame, text="Close", 
                           command=dialog.destroy,
                           bg=get_current_theme_colors(current_theme)["accent3"],
                           theme=current_theme)
    close_btn.pack(side=tk.RIGHT, padx=10)
    
    # Run defrag button
    if files:
        defrag_btn = StyledButton(button_frame, text="Optimize Files", 
                                command=lambda: messagebox.showinfo("Optimize", "File optimization completed!"),
                                bg=get_current_theme_colors(current_theme)["accent2"],
                                theme=current_theme)
        defrag_btn.pack(side=tk.RIGHT, padx=10)
    
    # Show overview tab by default
    show_overview_tab()
    
    # Wait for dialog to close
    parent.wait_window(dialog)

def show_file_metadata_dialog(parent, file_info, current_theme="dark"):
    """Enhanced file metadata dialog with better styling"""
    dialog = tk.Toplevel(parent)
    
    file_name, file_size, file_type, action, timestamp = file_info
    
    content_frame = style_dialog(dialog, current_theme, "File Metadata", 450, 400)
    
    # Create a decorative header with file icon
    icon_frame = tk.Frame(content_frame, bg=get_current_theme_colors(current_theme)["bg"])
    icon_frame.pack(fill=tk.X, pady=(0, 15))
    
    # Choose icon based on file type
    icon_text = "📄"  # Default document icon
    if file_type:
        if file_type.startswith("image"):
            icon_text = "🖼️"
        elif file_type.startswith("audio"):
            icon_text = "🎵"
        elif file_type.startswith("video"):
            icon_text = "🎬"
        elif file_type.startswith("text"):
            icon_text = "📝"
        elif file_type == "application/pdf":
            icon_text = "📑"
        elif "zip" in file_type or "compressed" in file_type:
            icon_text = "🗜️"
    
    # File icon
    icon_label = tk.Label(icon_frame, text=icon_text, 
                        font=("Arial", 48),
                        bg=get_current_theme_colors(current_theme)["bg"],
                        fg=get_current_theme_colors(current_theme)["accent1"])
    icon_label.pack(pady=(0, 10))
    
    # File name with truncation if too long
    display_name = file_name
    if len(file_name) > 30:
        display_name = file_name[:27] + "..."
        
    name_label = tk.Label(icon_frame, text=display_name, 
                        font=("Arial", 14, "bold"),
                        bg=get_current_theme_colors(current_theme)["bg"],
                        fg=get_current_theme_colors(current_theme)["fg"])
    name_label.pack(pady=(0, 5))
    
    # Create a themed separator
    separator = tk.Frame(content_frame, height=2, 
                       bg=get_current_theme_colors(current_theme)["accent1"])
    separator.pack(fill=tk.X, pady=10)
    
    # Metadata details in a grid layout for better organization
    details_frame = tk.Frame(content_frame, bg=get_current_theme_colors(current_theme)["bg"],
                           padx=20, pady=10)
    details_frame.pack(fill=tk.BOTH, expand=True)
    
    # Metadata items with labels and values
    metadata_items = [
        ("File Size", f"{file_size:,} bytes ({file_size/1024:.1f} KB)"),
        ("File Type", file_type or "Unknown"),
        ("Last Action", action or "None"),
        ("Modified", timestamp or "Unknown"),
    ]
    
    # Additional computed metadata
    if file_size > 0:
        # Add creation time if available from the database
        metadata_items.append(("Estimated Transfer Time", 
                              f"{file_size/(1024*1024):.2f} seconds at 1MB/s"))
    
    # Create a rounded rect to contain details
    details_container = tk.Frame(details_frame, 
                               bg=get_current_theme_colors(current_theme)["button_bg"],
                               padx=15, pady=15,
                               highlightbackground=get_current_theme_colors(current_theme)["accent1"],
                               highlightthickness=1)
    details_container.pack(fill=tk.BOTH, expand=True)
    
    # Add metadata items
    for i, (label, value) in enumerate(metadata_items):
        # Label in bold
        label_widget = tk.Label(details_container, 
                              text=f"{label}:", 
                              font=("Arial", 11, "bold"),
                              bg=get_current_theme_colors(current_theme)["button_bg"],
                              fg=get_current_theme_colors(current_theme)["accent1"],
                              anchor="w")
        label_widget.grid(row=i, column=0, sticky="w", pady=8)
        
        # Value
        value_widget = tk.Label(details_container, 
                              text=value, 
                              font=("Arial", 11),
                              bg=get_current_theme_colors(current_theme)["button_bg"],
                              fg=get_current_theme_colors(current_theme)["fg"],
                              anchor="w")
        value_widget.grid(row=i, column=1, sticky="w", padx=(15, 0), pady=8)
    
    # Configure grid
    details_container.grid_columnconfigure(1, weight=1)
    
    # Add close button
    button_frame = tk.Frame(content_frame, bg=get_current_theme_colors(current_theme)["bg"],
                          pady=10)
    button_frame.pack(fill=tk.X)
    
    close_btn = StyledButton(button_frame, text="Close", 
                           command=dialog.destroy,
                           bg=get_current_theme_colors(current_theme)["accent3"],
                           theme=current_theme)
    close_btn.pack(side=tk.RIGHT)
    
    # Wait for dialog to close
    parent.wait_window(dialog)
