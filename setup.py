import sqlite3


def start_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Create valid WorkID table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ValidWorkID (
            WORKID TEXT PRIMARY KEY
        )
    ''')

    with open('workids.txt', 'r') as file:
        lines = file.readlines()
        for line in lines:
            
            # Check if the WORKID already exists in the table
            cursor.execute(
                "SELECT * FROM ValidWorkID WHERE WORKID=?", (line.strip(),))
            existing_row = cursor.fetchone()
            if not existing_row:
                # If the WORKID doesn't exist, insert it into the table
                cursor.execute(
                    "INSERT INTO ValidWorkID (WORKID) VALUES (?)", (line.strip(),))

        conn.commit()

    # Create the User table
    # Use WORKID from ValidWorkID as the primary key
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            WORKID TEXT PRIMARY KEY,
            First TEXT,
            Last TEXT,
            Password TEXT,
            Role TEXT
        )
    ''')

    # Create the Files table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Files (
            FileId INTEGER PRIMARY KEY AUTOINCREMENT,
            FileName TEXT,
            FileData BLOB,
            WorkID TEXT
        )
    ''')

    cursor.close()
