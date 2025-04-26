from flask import Flask, request, jsonify, render_template, send_file, abort
import sqlite3
import os
import bcrypt
import base64
import hashlib
import io
import datetime
import logging
from cryptography.fernet import Fernet
from werkzeug.utils import secure_filename
from flask_cors import CORS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for templates directory
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))

# Create templates directory if it doesn't exist
if not os.path.exists(template_dir):
    os.makedirs(template_dir)
    logger.info(f"Created template directory: {template_dir}")

# Create a simple index.html file if not exists
index_html_path = os.path.join(template_dir, 'index.html')
if not os.path.exists(index_html_path):
    with open(index_html_path, 'w') as f:
        f.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Secure File Management System</title>
        </head>
        <body>
            <h1>Secure File Management System</h1>
            <p>Welcome to the Secure File Management System.</p>
        </body>
        </html>
        """)
    logger.info(f"Created index.html at: {index_html_path}")

# Create Flask app
app = Flask(__name__, 
            template_folder=template_dir, 
            static_folder=static_dir)
app.config['PROPAGATE_EXCEPTIONS'] = True
# Add CORS support
CORS(app, supports_credentials=True)

# Error handlers
@app.errorhandler(500)
def handle_500(error):
    logger.error(f"500 error: {error}")
    return jsonify({"error": "Internal Server Error", "message": str(error)}), 500

@app.errorhandler(404)
def handle_404(error):
    logger.error(f"404 error: {error}")
    return jsonify({"error": "Not Found", "message": str(error)}), 404

# Initialize database
def init_db():
    try:
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
        logger.info("Database initialized successfully")
        
        # Create a test user for Vercel environments
        if 'VERCEL' in os.environ:
            try:
                # Use the same connection
                hashed_password = bcrypt.hashpw("testuser123".encode('utf-8'), bcrypt.gensalt())
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                            ("testuser", hashed_password))
                conn.commit()
                logger.info("Created test user for Vercel environment")
            except Exception as e:
                logger.error(f"Error creating test user: {e}")
        
        # Only close connection if not on Vercel
        if 'VERCEL' not in os.environ:
            conn.close()
            return None
        return conn  # Return connection for Vercel environment
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

# Global variable to hold in-memory database connection for Vercel
db_connection = None

try:
    # Initialize database and keep connection for Vercel
    db_connection = init_db()
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")

# Function to get database connection
def get_db_connection():
    global db_connection
    if 'VERCEL' in os.environ:
        if db_connection is None:
            db_connection = init_db()
        return db_connection
    else:
        return sqlite3.connect("file_manager.db")

# Session management (simple implementation for demonstration)
sessions = {}

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'})
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                     (username, hashed_password))
        conn.commit()
        if 'VERCEL' not in os.environ:
            conn.close()
        
        response = jsonify({'success': True, 'message': f'User {username} registered successfully'})
        # Add CORS headers
        return response
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
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        if 'VERCEL' not in os.environ:
            conn.close()
        
        if result and bcrypt.checkpw(password.encode('utf-8'), result[1]):
            user_id = result[0]
            session_id = base64.b64encode(os.urandom(24)).decode('utf-8')
            sessions[session_id] = {'user_id': user_id, 'username': username}
            response = jsonify({'success': True, 'message': 'Login successful', 'session_id': session_id})
            # Set SameSite=None for cross-site requests
            response.set_cookie('session_id', session_id, httponly=True, secure=True, samesite='None')
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
        response.delete_cookie('session_id', httponly=True, secure=True, samesite='None')
        return response
    return jsonify({'success': False, 'message': 'Not logged in'})

@app.route('/api/status')
def status():
    return jsonify({
        "status": "ok",
        "environment": "Vercel"
    })

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
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO files (user_id, file_name, file_data, file_size, file_type, action, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (sessions[session_id]['user_id'], filename, file_data, file_size, file_type, "Uploaded", 
             datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        if 'VERCEL' not in os.environ:
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
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, file_name, file_size, file_type, action, timestamp FROM files WHERE user_id = ?", 
            (sessions[session_id]['user_id'],)
        )
        rows = cursor.fetchall()
        if 'VERCEL' not in os.environ:
            conn.close()
        
        files = [{
            'id': row[0],
            'name': row[1],
            'size': row[2],
            'type': row[3],
            'action': row[4],
            'timestamp': row[5]
        } for row in rows]
        
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
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT file_data, file_type FROM files WHERE file_name = ? AND user_id = ?", 
            (filename, sessions[session_id]['user_id'])
        )
        result = cursor.fetchone()
        
        if not result:
            if 'VERCEL' not in os.environ:
                conn.close()
            return jsonify({'success': False, 'message': 'File not found'})
        
        file_data, file_type = result
        
        # Log the download
        cursor.execute(
            "UPDATE files SET action = 'Downloaded', timestamp = ? WHERE file_name = ? AND user_id = ?", 
            (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), filename, sessions[session_id]['user_id'])
        )
        conn.commit()
        if 'VERCEL' not in os.environ:
            conn.close()
        
        response = send_file(
            io.BytesIO(file_data),
            mimetype=file_type,
            as_attachment=True,
            download_name=filename
        )
        return response
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
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM files WHERE file_name = ? AND user_id = ?", 
            (filename, sessions[session_id]['user_id'])
        )
        conn.commit()
        if 'VERCEL' not in os.environ:
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
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT file_data FROM files WHERE file_name = ? AND user_id = ?", 
            (filename, sessions[session_id]['user_id'])
        )
        result = cursor.fetchone()
        
        if not result:
            if 'VERCEL' not in os.environ:
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
        if 'VERCEL' not in os.environ:
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
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT file_data FROM files WHERE file_name = ? AND user_id = ?", 
            (filename, sessions[session_id]['user_id'])
        )
        result = cursor.fetchone()
        
        if not result:
            if 'VERCEL' not in os.environ:
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
            if 'VERCEL' not in os.environ:
                conn.close()
            
            return jsonify({'success': True, 'message': 'File decrypted successfully'})
        except:
            if 'VERCEL' not in os.environ:
                conn.close()
            return jsonify({'success': False, 'message': 'Decryption failed. Incorrect password!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Decryption failed: {str(e)}'})

# Add a health check endpoint for Vercel
@app.route('/api/health')
def health_check():
    try:
        # Test database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        if 'VERCEL' not in os.environ:
            conn.close()
        return jsonify({'status': 'healthy', 'environment': 'Vercel' if 'VERCEL' in os.environ else 'Local'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/debug')
def debug_info():
    """Route to show debug info for troubleshooting"""
    debug_data = {
        'template_dir': template_dir,
        'template_dir_exists': os.path.exists(template_dir),
        'index_html_exists': os.path.exists(os.path.join(template_dir, 'index.html')),
        'static_dir': static_dir,
        'static_dir_exists': os.path.exists(static_dir),
        'env_vars': {k: v for k, v in os.environ.items() if not k.startswith('AWS_') and not k.startswith('VERCEL_')}
    }
    return jsonify(debug_data)

# Catch-all route to handle all other paths
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return jsonify({
        "status": "alive",
        "message": "API is running on Vercel",
        "path": path
    })

if __name__ == '__main__':
    app.run(debug=True)
