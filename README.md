\# 🔐 Secure File Manager (Tkinter)

A secure, user-authenticated file manager built with Python and Tkinter. This desktop application allows users to upload, encrypt, decrypt, preview, rename, and delete files—all while storing data securely in an SQLite database.

## 🚀 Features

- 🔐 User registration & login (passwords hashed with bcrypt)
- 📁 File upload and storage in SQLite (BLOBs)
- 🔑 Encrypt/Decrypt files using Fernet (symmetric encryption)
- 🖼 Preview support for:
  - Text files
  - Image files (PNG, JPG, etc.)
  - PDF files (first page rendered)
- 📝 File metadata viewer
- 🌗 Dark mode toggle
- 🧵 Multithreaded upload for smoother performance

#📂 File Structure
```.
├── main.py              # Main application script
├── file_manager.db      # SQLite database (auto-created)
├── encrypt.png          # Icon images used in GUI
├── decrypt.png
├── upload.png
├── delete.png
├── rename.png
├── preview.png
└── README.md            # This file
```

