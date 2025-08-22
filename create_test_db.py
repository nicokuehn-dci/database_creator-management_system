"""
Script to create a test database with sample data for development purposes.
"""
import sqlite3
import os

# Create test database
db_path = os.path.join('databases', 'test.db')

# Remove existing file if it exists
if os.path.exists(db_path):
    os.remove(db_path)

# Create database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create tables
cursor.execute('''
CREATE TABLE test (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    value REAL
)
''')

# Insert test data
query = 'INSERT INTO test (name, value) VALUES (?, ?)'
cursor.execute(query, ('Test Record 1', 42.5))
cursor.execute(query, ('Test Record 2', 99.9))

# Commit and close
conn.commit()
conn.close()

print('Test database created successfully')
