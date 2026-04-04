import sqlite3
import os
from pathlib import Path

def init_db():
    """Initialize the SQLite database with required tables"""
    # Create database directory if it doesn't exist
    db_dir = Path("data/processed")
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_dir / "users.db")
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )
    ''')
    
    # Create user_profiles table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_profiles (
        user_id INTEGER PRIMARY KEY,
        full_name TEXT,
        date_of_birth DATE,
        gender TEXT,
        phone_number TEXT,
        address TEXT,
        education_level TEXT,
        current_cgpa REAL,
        current_percentage REAL,
        preferred_career_fields TEXT,
        preferred_college_tier TEXT,
        preferred_location TEXT,
        budget_range TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create user_career_matches table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_career_matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        career_id INTEGER,
        match_score REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (career_id) REFERENCES careers (id)
    )
    ''')
    
    # Create user_college_matches table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_college_matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        college_id INTEGER,
        match_score REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (college_id) REFERENCES colleges (id)
    )
    ''')
    
    # Commit changes and close connection
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db() 