import sqlite3
import os

def repair_database():
    """
    Script to repair any corrupted database records or structure
    """
    print("Starting database repair...")
    
    # Check if database exists
    if not os.path.exists("file_manager.db"):
        print("Database file not found. No repair needed.")
        return
    
    try:
        # Create backup first
        if os.path.exists("file_manager.db"):
            print("Creating backup of current database...")
            with open("file_manager.db", "rb") as src:
                with open("file_manager.db.backup", "wb") as dst:
                    dst.write(src.read())
        
        # Connect to database
        conn = sqlite3.connect("file_manager.db")
        cursor = conn.cursor()
        
        # Integrity check
        cursor.execute("PRAGMA integrity_check;")
        integrity_result = cursor.fetchone()[0]
        
        if integrity_result == "ok":
            print("Database integrity check passed.")
        else:
            print(f"Database integrity issues found: {integrity_result}")
            print("Attempting repair...")
            
            # Try to recover data by dumping and recreating
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            # Create new database structure
            new_conn = sqlite3.connect("file_manager_repaired.db")
            new_cursor = new_conn.cursor()
            
            # Recreate tables in new database
            new_cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                username TEXT UNIQUE,
                                password TEXT
                            )''')
            new_cursor.execute('''CREATE TABLE IF NOT EXISTS files (
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
            
            # Copy recoverable data
            try:
                # Copy users
                cursor.execute("SELECT id, username, password FROM users")
                users = cursor.fetchall()
                for user in users:
                    try:
                        new_cursor.execute("INSERT INTO users (id, username, password) VALUES (?, ?, ?)", user)
                    except sqlite3.Error as e:
                        print(f"Could not copy user {user[0]}: {e}")
                
                # Copy files
                cursor.execute("SELECT id, user_id, file_name, file_data, file_size, file_type, action, timestamp FROM files")
                files = cursor.fetchall()
                for file in files:
                    try:
                        new_cursor.execute('''INSERT INTO files 
                                        (id, user_id, file_name, file_data, file_size, file_type, action, timestamp) 
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', file)
                    except sqlite3.Error as e:
                        print(f"Could not copy file {file[0]}: {e}")
                
                new_conn.commit()
                new_conn.close()
                conn.close()
                
                # Replace old database with new one
                os.rename("file_manager.db", "file_manager.db.old")
                os.rename("file_manager_repaired.db", "file_manager.db")
                print("Repair complete. Original database saved as file_manager.db.old")
                
            except Exception as e:
                print(f"Error during data recovery: {e}")
    
    except Exception as e:
        print(f"Error during database repair: {e}")
        
if __name__ == "__main__":
    repair_database()
