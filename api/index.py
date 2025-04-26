from flask import Flask, request, jsonify, render_template, send_file
import sqlite3
import os
import bcrypt
import base64
import hashlib
import io
import datetime
from cryptography.fernet import Fernet
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Initialize database
def init_db():
    # For Vercel deployment, use in-memory database
    # This is a temporary solution - data will be lost on restart
    # For production, consider using a database service like PostgreSQL, MongoDB, etc.
    if 'VERCEL' in os.environ:
        conn = sqlite3.connect(":memory:")
    else:
        # For local development, use file-based database
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

init_db()

# Session management (simple implementation for demonstration)
sessions = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'})
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        # Use in-memory database on Vercel
        if 'VERCEL' in os.environ:
            conn = sqlite3.connect(":memory:")
        else:
            conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                     (username, hashed_password))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'User {username} registered successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Username already exists'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Registration failed: {str(e)}'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'})
    
    try:
        # Use in-memory database on Vercel
        if 'VERCEL' in os.environ:
            conn = sqlite3.connect(":memory:")
        else:
            conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        conn.close()
        
        if result and bcrypt.checkpw(password.encode('utf-8'), result[1]):
            user_id = result[0]
            session_id = base64.b64encode(os.urandom(24)).decode('utf-8')
            sessions[session_id] = {'user_id': user_id, 'username': username}
            response = jsonify({'success': True, 'message': 'Login successful', 'session_id': session_id})
            response.set_cookie('session_id', session_id, httponly=True, secure=True)
            return response
        else:
            return jsonify({'success': False, 'message': 'Invalid username or password'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Login failed: {str(e)}'})

@app.route('/api/logout', methods=['POST'])
def logout():
    session_id = request.cookies.get('session_id')
    if session_id and session_id in sessions:
        del sessions[session_id]
        response = jsonify({'success': True, 'message': 'Logout successful'})
        response.delete_cookie('session_id')
        return response
    return jsonify({'success': False, 'message': 'Not logged in'})

@app.route('/api/status')
def status():
    session_id = request.cookies.get('session_id')
    if session_id and session_id in sessions:
        return jsonify({
            'logged_in': True, 
            'username': sessions[session_id]['username']
        })
    return jsonify({'logged_in': False})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    session_id = request.cookies.get('session_id')
    if not (session_id and session_id in sessions):
        return jsonify({'success': False, 'message': 'Please login first'})
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'})
    
    try:
        filename = secure_filename(file.filename)
        file_data = file.read()
        file_size = len(file_data)
        file_type = file.content_type or 'application/octet-stream'
        
        # Use in-memory database on Vercel
        if 'VERCEL' in os.environ:
            conn = sqlite3.connect(":memory:")
        else:
            conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO files (user_id, file_name, file_data, file_size, file_type, action, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (sessions[session_id]['user_id'], filename, file_data, file_size, file_type, "Uploaded", 
             datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'File uploaded successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Upload failed: {str(e)}'})

@app.route('/api/files')
def get_files():
    session_id = request.cookies.get('session_id')
    if not (session_id and session_id in sessions):
        return jsonify({'success': False, 'message': 'Please login first'})
    
    try:
        # Use in-memory database on Vercel
        if 'VERCEL' in os.environ:
            conn = sqlite3.connect(":memory:")
        else:
            conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT file_name FROM files WHERE user_id = ?", 
            (sessions[session_id]['user_id'],)
        )
        files = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to get files: {str(e)}'})

@app.route('/api/download')
def download_file():
    session_id = request.cookies.get('session_id')
    if not (session_id and session_id in sessions):
        return jsonify({'success': False, 'message': 'Please login first'})
    
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'success': False, 'message': 'Filename is required'})
    
    try:
        # Use in-memory database on Vercel
        if 'VERCEL' in os.environ:
            conn = sqlite3.connect(":memory:")
        else:
            conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT file_data, file_type FROM files WHERE file_name = ? AND user_id = ?", 
            (filename, sessions[session_id]['user_id'])
        )
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({'success': False, 'message': 'File not found'})
        
        file_data, file_type = result
        
        # Log the download
        cursor.execute(
            "UPDATE files SET action = 'Downloaded', timestamp = ? WHERE file_name = ? AND user_id = ?", 
            (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), filename, sessions[session_id]['user_id'])
        )
        conn.commit()
        conn.close()
        
        return send_file(
            io.BytesIO(file_data),
            mimetype=file_type,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'success': False, 'message': f'Download failed: {str(e)}'})

@app.route('/api/delete', methods=['DELETE'])
def delete_file():
    session_id = request.cookies.get('session_id')
    if not (session_id and session_id in sessions):
        return jsonify({'success': False, 'message': 'Please login first'})
    
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'success': False, 'message': 'Filename is required'})
    
    try:
        # Use in-memory database on Vercel
        if 'VERCEL' in os.environ:
            conn = sqlite3.connect(":memory:")
        else:
            conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM files WHERE file_name = ? AND user_id = ?", 
            (filename, sessions[session_id]['user_id'])
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'File deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Delete failed: {str(e)}'})

@app.route('/api/encrypt', methods=['POST'])
def encrypt_file():
    session_id = request.cookies.get('session_id')
    if not (session_id and session_id in sessions):
        return jsonify({'success': False, 'message': 'Please login first'})
    
    data = request.json
    filename = data.get('filename')
    password = data.get('password')
    
    if not filename or not password:
        return jsonify({'success': False, 'message': 'Filename and password are required'})
    
    try:
        # Use in-memory database on Vercel
        if 'VERCEL' in os.environ:
            conn = sqlite3.connect(":memory:")
        else:
            conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT file_data FROM files WHERE file_name = ? AND user_id = ?", 
            (filename, sessions[session_id]['user_id'])
        )
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({'success': False, 'message': 'File not found'})
        
        # Generate key from password
        key = base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())
        cipher = Fernet(key)
        
        # Encrypt file data
        encrypted_data = cipher.encrypt(result[0])
        
        # Update database
        cursor.execute(
            "UPDATE files SET file_data = ?, action = 'Encrypted', timestamp = ? WHERE file_name = ? AND user_id = ?", 
            (encrypted_data, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
             filename, sessions[session_id]['user_id'])
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'File encrypted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Encryption failed: {str(e)}'})

@app.route('/api/decrypt', methods=['POST'])
def decrypt_file():
    session_id = request.cookies.get('session_id')
    if not (session_id and session_id in sessions):
        return jsonify({'success': False, 'message': 'Please login first'})
    
    data = request.json
    filename = data.get('filename')
    password = data.get('password')
    
    if not filename or not password:
        return jsonify({'success': False, 'message': 'Filename and password are required'})
    
    try:
        # Use in-memory database on Vercel
        if 'VERCEL' in os.environ:
            conn = sqlite3.connect(":memory:")
        else:
            conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT file_data FROM files WHERE file_name = ? AND user_id = ?", 
            (filename, sessions[session_id]['user_id'])
        )
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({'success': False, 'message': 'File not found'})
        
        # Generate key from password
        key = base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())
        cipher = Fernet(key)
        
        try:
            # Decrypt file data
            decrypted_data = cipher.decrypt(result[0])
            
            # Update database
            cursor.execute(
                "UPDATE files SET file_data = ?, action = 'Decrypted', timestamp = ? WHERE file_name = ? AND user_id = ?", 
                (decrypted_data, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                 filename, sessions[session_id]['user_id'])
            )
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'File decrypted successfully'})
        except:
            conn.close()
            return jsonify({'success': False, 'message': 'Decryption failed. Incorrect password!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Decryption failed: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True)
