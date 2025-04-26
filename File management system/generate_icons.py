from PIL import Image, ImageDraw, ImageFont
import os

def generate_icons():
    """Generate icons for the file management system if they don't exist"""
    
    # Define icon specifications with their colors and shapes
    icon_specs = {
        "encrypt": {
            "color": "#F39C12",
            "shape": "lock",
            "filename": "encrypt.png"
        },
        "decrypt": {
            "color": "#3498DB",
            "shape": "unlock",
            "filename": "decrypt.png"
        },
        "upload": {
            "color": "#2ECC71",
            "shape": "arrow_up",
            "filename": "upload.png"
        },
        "delete": {
            "color": "#E74C3C",
            "shape": "trash",
            "filename": "delete.png"
        },
        "rename": {
            "color": "#9B59B6",
            "shape": "edit",
            "filename": "rename.png"
        },
        "preview": {
            "color": "#3498DB",
            "shape": "eye",
            "filename": "preview.png"
        }
    }
    
    # Create icons directory if it doesn't exist
    if not os.path.exists("icons"):
        os.makedirs("icons")
    
    for name, spec in icon_specs.items():
        # Skip if icon already exists
        if os.path.exists(spec["filename"]):
            continue
            
        # Create a new image with transparency
        img = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Convert hex color to RGB
        color = spec["color"]
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        
        # Draw the appropriate shape based on the type
        if spec["shape"] == "lock":
            # Draw a lock
            draw.rectangle((40, 50, 88, 98), fill=(r, g, b, 255), outline=(r, g, b, 255))
            draw.rectangle((48, 35, 80, 50), fill=(0, 0, 0, 0), outline=(r, g, b, 255), width=8)
            draw.rectangle((52, 60, 76, 75), fill=(255, 255, 255, 150))
            
        elif spec["shape"] == "unlock":
            # Draw an unlocked lock
            draw.rectangle((40, 50, 88, 98), fill=(r, g, b, 255), outline=(r, g, b, 255))
            draw.arc((25, 20, 80, 60), 270, 90, fill=(r, g, b, 255), width=8)
            draw.rectangle((52, 60, 76, 75), fill=(255, 255, 255, 150))
            
        elif spec["shape"] == "arrow_up":
            # Draw an up arrow
            draw.polygon([(64, 30), (30, 70), (50, 70), (50, 98), (78, 98), (78, 70), (98, 70)], 
                         fill=(r, g, b, 255))
            
        elif spec["shape"] == "trash":
            # Draw a trash can
            draw.rectangle((40, 40, 88, 98), fill=(r, g, b, 255))
            draw.rectangle((30, 30, 98, 40), fill=(r, g, b, 255))
            draw.rectangle((55, 20, 73, 30), fill=(r, g, b, 255))
            # Draw lines on the trash
            for i in range(50, 81, 10):
                draw.line([(i, 50), (i, 90)], fill=(255, 255, 255, 150), width=3)
            
        elif spec["shape"] == "edit":
            # Draw a pencil
            draw.polygon([(40, 88), (30, 98), (50, 98)], fill=(r, g, b, 255))
            draw.polygon([(40, 88), (88, 40), (98, 30), (50, 98)], fill=(r, g, b, 255))
            draw.polygon([(88, 40), (98, 30), (98, 40), (88, 50)], fill=(r, g, b, 180))
            
        elif spec["shape"] == "eye":
            # Draw an eye
            draw.ellipse((20, 44, 108, 84), fill=(r, g, b, 255))
            draw.ellipse((48, 52, 80, 76), fill=(255, 255, 255, 255))
            draw.ellipse((58, 58, 70, 70), fill=(0, 0, 0, 255))
        
        # Resize to the desired size (48x48 for app icons)
        img_resized = img.resize((48, 48), Image.LANCZOS)
        
        # Save the icon
        img_resized.save(spec["filename"])
        print(f"Generated icon: {spec['filename']}")

if __name__ == "__main__":
    generate_icons()
    print("Icons generated successfully!")
