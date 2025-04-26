# Simple color schemes for the application
import tkinter as tk

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
        "glass_bg": "#333333",  # Glass effect background (no alpha)
        "glass_fg": "#FFFFFF",  # Glass effect foreground
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
        "glass_bg": "#E0E0E0",  # Glass effect background (no alpha)
        "glass_fg": "#333333",  # Glass effect foreground
    }
}

def get_current_theme_colors(theme_name="dark"):
    """Get colors for the specified theme"""
    return color_schemes.get(theme_name, color_schemes["dark"])

def get_glass_colors(theme_name="dark"):
    """Get glass effect colors for the specified theme"""
    theme = get_current_theme_colors(theme_name)
    return {
        "bg": theme["glass_bg"],
        "fg": theme["glass_fg"]
    }

def style_dialog(dialog, theme_name="dark", title=None, width=400, height=300):
    """Apply consistent styling to dialog boxes"""
    theme = get_current_theme_colors(theme_name)
    
    # Configure basic properties
    if title:
        dialog.title(title)
    dialog.geometry(f"{width}x{height}")
    dialog.configure(bg=theme["bg"])
    
    # Add a style frame with gradient effect
    header_frame = tk.Frame(dialog, bg=theme["accent1"], height=40)
    header_frame.pack(fill=tk.X, side=tk.TOP)
    
    # Add title label if provided
    if title:
        title_label = tk.Label(header_frame, text=title, 
                             font=("Helvetica", 14, "bold"),
                             bg=theme["accent1"], fg="white")
        title_label.pack(pady=8)
    
    # Create content frame with padding
    content_frame = tk.Frame(dialog, bg=theme["bg"], padx=20, pady=15)
    content_frame.pack(fill=tk.BOTH, expand=True)
    
    # Return the content frame where widgets should be placed
    return content_frame
