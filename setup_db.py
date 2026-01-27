#!/usr/bin/env python
"""
MySQL Database Setup Script
Reads database credentials from .env and sets up the database
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import MySQLdb

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Get credentials
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'install_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'installer-Chargers')
DB_NAME = os.getenv('DB_NAME', 'installation_system')

print(f"Connecting to MySQL at {DB_HOST}:{DB_PORT} as {DB_USER}...")

try:
    # Connect to MySQL as root first
    connection = MySQLdb.connect(
        host=DB_HOST,
        port=DB_PORT,
        user='root',
        passwd=input("Enter MySQL root password: ")
    )
    
    cursor = connection.cursor()
    
    # Read and execute setup script
    with open('setup_mysql.sql', 'r') as f:
        sql_script = f.read()
    
    # Execute each statement
    statements = [s.strip() for s in sql_script.split(';') if s.strip()]
    for statement in statements:
        if statement and not statement.startswith('--'):
            print(f"Executing: {statement[:60]}...")
            cursor.execute(statement)
    
    connection.commit()
    print("\n✓ Database setup completed successfully!")
    print(f"✓ Database: {DB_NAME}")
    print(f"✓ User: {DB_USER}")
    
    cursor.close()
    connection.close()
    
except MySQLdb.Error as e:
    print(f"MySQL Error: {e}")
    exit(1)
except Exception as e:
    print(f"Error: {e}")
    exit(1)
