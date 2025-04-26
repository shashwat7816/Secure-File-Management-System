import tkinter as tk
from PIL import Image, ImageDraw, ImageTk

class ModernUI:
    """Class for modern UI elements and styling"""
    
    @staticmethod
    def create_round_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
        """Draw a rounded rectangle on a canvas"""
        points = [
            x1+radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1
        ]
        return canvas.create_polygon(points, **kwargs, smooth=True)
    
    @staticmethod
    def create_rounded_button(parent, text, command, radius=10, bg="#3498DB", fg="white", **kwargs):
        """Create a rounded button with hover effects"""
        frame = tk.Frame(parent, bg=parent.cget("bg"))
        
        # Create the base canvas for the button
        canvas = tk.Canvas(frame, height=40, bg=parent.cget("bg"), highlightthickness=0)
        canvas.pack(fill=tk.X)
        
        # Create the rounded rectangle button shape
        btn_shape = ModernUI.create_round_rectangle(canvas, 0, 0, canvas.winfo_reqwidth(), 40, 
                                                  radius=radius, fill=bg, outline="")
        
        # Add text
        btn_text = canvas.create_text(canvas.winfo_reqwidth()/2, 20, text=text, fill=fg, 
                                    font=("Arial", 12, "bold"))
        
        # Store original background for later
        canvas.orig_bg = bg
        hover_bg = "#2980B9"  # Slightly darker blue for hover
        
        # Configure the canvas to resize with the frame
        def on_frame_configure(event):
            canvas.itemconfig(btn_shape, width=event.width)
            canvas.coords(btn_text, event.width/2, 20)
            
        canvas.bind("<Configure>", on_frame_configure)
        
        # Hover effects
        def on_enter(e):
            canvas.itemconfig(btn_shape, fill=hover_bg)
        
        def on_leave(e):
            canvas.itemconfig(btn_shape, fill=canvas.orig_bg)
        
        def on_click(e):
            if command:
                command()
        
        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        canvas.bind("<Button-1>", on_click)
        
        return frame
    
    @staticmethod
    def create_icon_button(parent, icon_path, command, tooltip_text="", size=(24, 24), **kwargs):
        """Create a button with an icon and optional tooltip"""
        try:
            # Load icon
            icon = Image.open(icon_path).resize(size, Image.LANCZOS)
            photo = ImageTk.PhotoImage(icon)
            
            # Create a frame with canvas for the button
            frame = tk.Frame(parent, bg=parent.cget("bg"))
            canvas = tk.Canvas(frame, width=size[0]+20, height=size[1]+20, 
                               bg=parent.cget("bg"), highlightthickness=0)
            canvas.pack()
            
            # Add the icon in a circular background
            bg_id = canvas.create_oval(5, 5, size[0]+15, size[1]+15, 
                                     fill="#f0f0f0", outline="")
            icon_id = canvas.create_image(size[0]//2+10, size[1]//2+10, 
                                        image=photo, anchor="center")
            
            # Store the photo reference
            canvas.photo = photo
            
            # Hover and click effects
            def on_enter(e):
                canvas.itemconfig(bg_id, fill="#e0e0e0")
                if tooltip_text:
                    # Show tooltip
                    x, y = frame.winfo_rootx(), frame.winfo_rooty() + size[1] + 20
                    ModernUI._show_tooltip(frame, tooltip_text, x, y)
            
            def on_leave(e):
                canvas.itemconfig(bg_id, fill="#f0f0f0")
                if tooltip_text and hasattr(frame, "tooltip"):
                    frame.tooltip.destroy()
                    delattr(frame, "tooltip")
            
            def on_click(e):
                if command:
                    command()
            
            canvas.bind("<Enter>", on_enter)
            canvas.bind("<Leave>", on_leave)
            canvas.bind("<Button-1>", on_click)
            
            return frame
        
        except Exception as e:
            print(f"Error creating icon button: {e}")
            return tk.Button(parent, text="Error", command=command)
    
    @staticmethod
    def _show_tooltip(widget, text, x, y):
        """Create and show a tooltip"""
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tooltip, text=text, justify='left',
                        background="#333333", foreground="white",
                        relief='solid', borderwidth=1,
                        font=("Arial", "9", "normal"),
                        padx=5, pady=2)
        label.pack()
        
        widget.tooltip = tooltip

    @staticmethod
    def create_tab(parent, text, icon_path=None, **kwargs):
        """Create a modern tab-like button"""
        frame = tk.Frame(parent, **kwargs)
        
        canvas = tk.Canvas(frame, height=40, highlightthickness=0, **kwargs)
        canvas.pack(fill=tk.X)
        
        # Create tab shape (slightly rounded on top corners only)
        tab_shape = ModernUI.create_round_rectangle(canvas, 0, 0, canvas.winfo_reqwidth(), 40, 
                                                   radius=10, fill="#f0f0f0", outline="")
        
        # Position for text (and icon if provided)
        if icon_path:
            try:
                icon = Image.open(icon_path).resize((16, 16), Image.LANCZOS)
                photo = ImageTk.PhotoImage(icon)
                icon_id = canvas.create_image(15, 20, image=photo, anchor="w")
                canvas.photo = photo  # Keep a reference
                text_x = 40
            except:
                text_x = 15
        else:
            text_x = 15
        
        # Add text
        text_id = canvas.create_text(text_x, 20, text=text, fill="#333333", 
                                   font=("Arial", 10), anchor="w")
        
        # Configure resizing
        def on_configure(event):
            canvas.itemconfig(tab_shape, width=event.width)
        
        canvas.bind("<Configure>", on_configure)
        
        return frame
