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
dark_mode = False  


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


def register_user():
    username = simpledialog.askstring("Register", "Enter a username:")
    password = simpledialog.askstring("Register", "Enter a password:", show='*')
    if username and password:
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        try:
            conn = sqlite3.connect("file_manager.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "User registered successfully!")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists!")

def login_user():
    global current_user_id, username_label
    username = simpledialog.askstring("Login", "Enter your username:")
    password = simpledialog.askstring("Login", "Enter your password:", show='*')
    conn = sqlite3.connect("file_manager.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    if result and bcrypt.checkpw(password.encode(), result[2]):
        current_user_id = result[0]
        messagebox.showinfo("Success", "Login successful!")
        username_label.config(text=f"Logged in as: {result[1]}")
        update_file_dropdown()
    else:
        messagebox.showerror("Error", "Invalid username or password!")

def logout_user():
    global current_user_id, username_label
    current_user_id = None
    messagebox.showinfo("Logout", "Successfully logged out!")
    username_label.config(text="Not logged in")
    file_dropdown['values'] = []

init_db()

def upload_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_type = mimetypes.guess_type(file_path)[0] or "Unknown"

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


def generate_key(password):
    return base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())

def encrypt_file():
    selected_file = file_dropdown.get()
    password = simpledialog.askstring("Encrypt", "Enter a password for encryption:", show='*')
    if selected_file and password:
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
            messagebox.showinfo("Success", "File encrypted successfully!")

def decrypt_file():
    selected_file = file_dropdown.get()
    password = simpledialog.askstring("Decrypt", "Enter the decryption password:", show='*')
    if selected_file and password:
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
                messagebox.showinfo("Success", "File decrypted successfully!")
            except:
                messagebox.showerror("Error", "Decryption failed. Incorrect password!")

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
        conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        cursor.execute("SELECT file_data, file_type FROM files WHERE file_name = ? AND user_id = ?", 
                       (selected_file, current_user_id))
        result = cursor.fetchone()
        conn.close()

        if result:
            file_data, file_type = result

            preview_window = tk.Toplevel(root)
            preview_window.title(f"Preview - {selected_file}")
            preview_window.geometry("600x500")

            if file_type and file_type.startswith("text"):
                # Handle Text Files
                try:
                    file_content = file_data.decode("utf-8")  
                    preview_text = tk.Text(preview_window, wrap=tk.WORD, font=("Arial", 12))
                    preview_text.insert(tk.END, file_content)
                    preview_text.config(state=tk.DISABLED)
                    preview_text.pack(expand=True, fill=tk.BOTH)
                except UnicodeDecodeError:
                    messagebox.showerror("Error", "Cannot preview this file. It may be non-text data.")

            elif file_type and file_type.startswith("image"):
                # Handle Image Files
                try:
                    image = Image.open(io.BytesIO(file_data))
                    image = image.resize((500, 400))  
                    photo = ImageTk.PhotoImage(image)

                    label = tk.Label(preview_window, image=photo)
                    label.image = photo  # Keep a reference
                    label.pack(expand=True, fill=tk.BOTH)
                except Exception as e:
                    messagebox.showerror("Error", f"Cannot preview this image.\n{e}")

            elif file_type and file_type == "application/pdf":
                # Handle PDF Files
                try:
                    pdf_stream = io.BytesIO(file_data)
                    pdf_document = fitz.open(stream=pdf_stream, filetype="pdf")
                    pdf_page = pdf_document[0]  # Get the first page
                    pix = pdf_page.get_pixmap()  # Render page as image
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                    img = img.resize((500, 400))  # Resize for better preview
                    photo = ImageTk.PhotoImage(img)

                    label = tk.Label(preview_window, image=photo)
                    label.image = photo  # Keep a reference
                    label.pack(expand=True, fill=tk.BOTH)
                except Exception as e:
                    messagebox.showerror("Error", f"Cannot preview this PDF.\n{e}")

            else:
                messagebox.showerror("Error", "File format not supported for preview.")

        else:
            messagebox.showerror("Error", "File not found!")
def show_file_metadata():
    selected_file = file_dropdown.get()
    if selected_file:
        conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        cursor.execute("SELECT file_size, file_type, action, timestamp FROM files WHERE file_name = ? AND user_id = ?", (selected_file, current_user_id))
        result = cursor.fetchone()
        conn.close()

        if result:
            messagebox.showinfo("File Metadata",
                                f"File Name: {selected_file}\n"
                                f"File Size: {result[0]} bytes\n"
                                f"File Type: {result[1]}\n"
                                f"Last Action: {result[2]}\n"
                                f"Timestamp: {result[3]}")

def toggle_dark_mode():
    global dark_mode
    dark_mode = not dark_mode
    bg_color = "black" if dark_mode else "white"
    fg_color = "white" if dark_mode else "black"
    
    root.configure(bg=bg_color)
    title_label.config(bg=bg_color, fg=fg_color)
    username_label.config(bg=bg_color, fg=fg_color)
    auth_frame.config(bg=bg_color)
    auth_frame1.config(bg=bg_color)
    toggle_button.config(bg="#607D8B" if dark_mode else "#CCCCCC", fg="white")

def threaded_upload():
    thread = threading.Thread(target=upload_file)
    thread.start()


root = tk.Tk()
root.title("Secure File Manager")
root.geometry("600x700")
root.configure(bg="black")

encrypt_icon = ImageTk.PhotoImage(Image.open("encrypt.png").resize((30, 30)))
decrypt_icon = ImageTk.PhotoImage(Image.open("decrypt.png").resize((30, 30)))
upload_icon = ImageTk.PhotoImage(Image.open("upload.png").resize((30, 30)))
delete_icon = ImageTk.PhotoImage(Image.open("delete.png").resize((30, 30)))
rename_icon = ImageTk.PhotoImage(Image.open("rename.png").resize((30, 30)))
preview_icon = ImageTk.PhotoImage(Image.open("preview.png").resize((30, 30)))

title_label = tk.Label(root, text="Secure File Manager", font=("Helvetica", 30), fg="white", bg="black")
title_label.pack(pady=10)

username_label = tk.Label(root, text="Not logged in", font=("Arial", 18), fg="white", bg="black")
username_label.pack(pady=10)

toggle_button = tk.Button(root, text="Dark Mode", command=toggle_dark_mode, font=("Arial", 18), bg="#607D8B", fg="white")
toggle_button.pack(pady=5)

auth_frame = tk.Frame(root, bg="black")
auth_frame.pack(pady=10)

register_button = tk.Button(auth_frame, text="Register", command=register_user, font=("Arial", 18), bg="#2196F3", fg="white")
register_button.grid(row=0, column=0, padx=5)

login_button = tk.Button(auth_frame, text="Login", command=login_user, font=("Arial", 18), bg="#4CAF50", fg="white")
login_button.grid(row=0, column=1, padx=5)

logout_button = tk.Button(auth_frame, text="Logout", command=logout_user, font=("Arial", 18), bg="#FF5722", fg="white")
logout_button.grid(row=0, column=2, padx=5)

file_dropdown = ttk.Combobox(root, state="readonly")
file_dropdown.pack(pady=10)

upload_button = tk.Button(root, text="Upload File", command=threaded_upload,image=upload_icon, compound="left", font=("Arial", 18), bg="#4CAF50", fg="white")
upload_button.pack(pady=5)

preview_button = tk.Button(root, text="Preview File", command=preview_file,image=preview_icon, compound="left", font=("Arial", 18), bg="#FF9800", fg="white")
preview_button.pack(pady=5)

auth_frame1 = tk.Frame(root, bg="black")
auth_frame1.pack(pady=10)

encrypt_button = tk.Button(auth_frame1, text="Encrypt File", command=encrypt_file,image=encrypt_icon, compound="left", font=("Arial", 18), bg="#FFC107", fg="white")
encrypt_button.grid(row=0, column=0, padx=(15),pady=15)

decrypt_button = tk.Button(auth_frame1, text="Decrypt File", command=decrypt_file,image=decrypt_icon, compound="left", font=("Arial", 18), bg="#FF9800", fg="white")
decrypt_button.grid(row=0, column=1, padx=(15),pady=15)

delete_button = tk.Button(auth_frame1, text="Delete File", command=delete_file,image=delete_icon, compound="left", font=("Arial", 18), bg="#F44336", fg="white")
delete_button.grid(row=1, column=0, padx=(15),pady=15)

rename_button = tk.Button(auth_frame1, text="Rename File", command=rename_file,image=rename_icon, compound="left", font=("Arial", 18), bg="#9C27B0", fg="white")
rename_button.grid(row=1, column=1, padx=(15),pady=15)

metadata_button = tk.Button(root, text="File Metadata", command=show_file_metadata, font=("Arial", 18), bg="#FF9800", fg="white",relief="flat",borderwidth=5,highlightthickness=0) 
metadata_button.pack(pady=5)


root.mainloop()
