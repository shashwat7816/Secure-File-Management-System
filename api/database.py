import sqlite3
import os
import logging
import bcrypt
import datetime

logger = logging.getLogger(__name__)

class Database:
    _instance = None
    _connection = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Database()
        return cls._instance
    
    def __init__(self):
        if Database._instance is not None:
            raise Exception("This class is a singleton. Use get_instance() instead.")
        self._initialize_db()
    
    def _initialize_db(self):
        try:
            # For Vercel deployment, use in-memory database
            if 'VERCEL' in os.environ:
                self._connection = sqlite3.connect(":memory:", check_same_thread=False)
            else:
                # For local development, use file-based database
                self._connection = sqlite3.connect("file_manager.db", check_same_thread=False)
            
            cursor = self._connection.cursor()
            
            # Create users table
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                username TEXT UNIQUE,
                                password TEXT
                            )''')
            
            # Create files table
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
            
            self._connection.commit()
            logger.info("Database initialized successfully")
            
            # Create a test user for Vercel environments
            if 'VERCEL' in os.environ:
                try:
                    cursor.execute("SELECT id FROM users WHERE username = ?", ("testuser",))
                    if not cursor.fetchone():
                        hashed_password = bcrypt.hashpw("testuser123".encode('utf-8'), bcrypt.gensalt())
                        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                                    ("testuser", hashed_password))
                        self._connection.commit()
                        logger.info("Created test user for Vercel environment")
                except Exception as e:
                    logger.error(f"Error creating test user: {e}")
        
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def get_connection(self):
        if 'VERCEL' in os.environ:
            return self._connection
        else:
            # For local development, return a new connection each time
            return sqlite3.connect("file_manager.db")
    
    def execute_query(self, query, params=(), fetch_all=False, commit=False):
        """
        Execute a query and return results
        """
        try:
            if 'VERCEL' in os.environ:
                conn = self._connection
                close_after = False
            else:
                conn = sqlite3.connect("file_manager.db")
                close_after = True
                
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            result = None
            if fetch_all:
                result = cursor.fetchall()
            else:
                result = cursor.fetchone()
                
            if commit:
                conn.commit()
                
            if close_after:
                conn.close()
                
            return result
        except Exception as e:
            logger.error(f"Database query error: {e}")
            raise
