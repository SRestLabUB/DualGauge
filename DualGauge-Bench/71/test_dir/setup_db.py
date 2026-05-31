#!/usr/bin/env python3
"""
MySQL Database Setup Script for show_user tests
This script sets up the MySQL database required for testing
Usage: python3 setup_db.py [mysql_root_password]
"""

import sys
import os
import getpass
import mysql.connector
from mysql.connector import Error

# Database configuration
DB_NAME = 'test_db'
DB_USER = 'dbuser'
DB_PASSWORD = 'dbpass'
DB_HOST = 'localhost'
DB_PORT = 3306

# Test data matching fc_tests
TEST_DATA = [
    ('john_doe', 'john@example.com'),
    ('alice', 'alice@example.com'),
]

def setup_database(root_password=None):
    """Set up the MySQL database with test data."""
    try:
        # Connect as root to create database and user
        if root_password:
            root_conn = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user='root',
                password=root_password
            )
        else:
            root_conn = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                user='root'
            )
        
        root_cursor = root_conn.cursor()
        
        print("Setting up MySQL database...")
        
        # Create database
        print(f"Creating database '{DB_NAME}'...")
        root_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        print(f"  ✓ Database '{DB_NAME}' created or already exists")
        
        # Create user if it doesn't exist
        print(f"Creating user '{DB_USER}'...")
        try:
            root_cursor.execute(f"CREATE USER IF NOT EXISTS '{DB_USER}'@'localhost' IDENTIFIED BY '{DB_PASSWORD}'")
            print(f"  ✓ User '{DB_USER}' created or already exists")
        except Error as e:
            # User might already exist
            print(f"  Note: User creation - {e}")
        
        # Grant privileges
        print(f"Granting privileges...")
        root_cursor.execute(f"GRANT ALL PRIVILEGES ON {DB_NAME}.* TO '{DB_USER}'@'localhost'")
        root_cursor.execute("FLUSH PRIVILEGES")
        print(f"  ✓ Privileges granted")
        
        root_conn.commit()
        root_conn.close()
        
        # Connect as dbuser to create table and insert data
        print(f"Connecting as '{DB_USER}'...")
        db_conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        db_cursor = db_conn.cursor()
        
        # Create table
        print(f"Creating table 'users'...")
        db_cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print(f"  ✓ Table 'users' created or already exists")
        
        # Clear existing data
        print("Clearing existing data...")
        db_cursor.execute("TRUNCATE TABLE users")
        
        # Insert test data
        print("Inserting test data...")
        db_cursor.executemany(
            "INSERT INTO users (username, email) VALUES (%s, %s)",
            TEST_DATA
        )
        
        db_conn.commit()
        
        # Verify data
        print("\nVerifying inserted data...")
        db_cursor.execute("SELECT * FROM users")
        rows = db_cursor.fetchall()
        for row in rows:
            print(f"  ✓ User: {row[1]}, Email: {row[2]}")
        
        db_conn.close()
        
        print("\n" + "=" * 70)
        print("✓ Database setup completed successfully!")
        print("=" * 70)
        print(f"\nDatabase: {DB_NAME}")
        print(f"User: {DB_USER}")
        print(f"Host: {DB_HOST}:{DB_PORT}")
        print(f"\nTest users:")
        for username, email in TEST_DATA:
            print(f"  - {username} / {email}")
        
        return 0
        
    except Error as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == '__main__':
    root_password = None
    
    if len(sys.argv) > 1:
        root_password = sys.argv[1]
    elif 'MYSQL_ROOT_PASSWORD' in os.environ:
        root_password = os.environ['MYSQL_ROOT_PASSWORD']
    else:
        root_password = getpass.getpass("Enter MySQL root password (press Enter if none): ")
        if not root_password.strip():
            root_password = None
    
    exit(setup_database(root_password))

