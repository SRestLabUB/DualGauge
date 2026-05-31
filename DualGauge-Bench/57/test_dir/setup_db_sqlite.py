#!/usr/bin/env python3
"""
SQLite database setup script for getUserBankAccount tests
Run this script to create a SQLite database with test data
"""

import sqlite3
import os

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), 'testdb.db')

# Connect to SQLite database (creates if doesn't exist)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create table
cursor.execute('''
CREATE TABLE IF NOT EXISTS bank_accounts (
    user_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    balance REAL NOT NULL DEFAULT 0.0
)
''')

# Insert test data
test_data = [
    ('000', '000', 0.0),
    ('123', '123', 5000.0),
    ('321', '321', 7890.0),
    ('456', '456', 250.0),
    ('999', '999', 12000.0)
]

cursor.executemany('''
INSERT OR REPLACE INTO bank_accounts (user_id, account_id, balance)
VALUES (?, ?, ?)
''', test_data)

conn.commit()

# Verify data
print("Database setup complete!")
print(f"Database file: {DB_PATH}")
print("\nTest data in bank_accounts table:")
cursor.execute("SELECT * FROM bank_accounts")
for row in cursor.fetchall():
    print(f"  User ID: {row[0]}, Account ID: {row[1]}, Balance: {row[2]}")

conn.close()
print(f"\nDatabase created successfully at: {DB_PATH}")

