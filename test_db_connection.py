#!/usr/bin/env python
"""Test database connection with credentials from .env"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Get credentials
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 3306))
DB_USER = os.getenv('DB_USER', 'install_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'installer-Chargers')
DB_NAME = os.getenv('DB_NAME', 'installation_system')

print(f"Testing connection with these credentials:")
print(f"  Host: {DB_HOST}")
print(f"  Port: {DB_PORT}")
print(f"  User: {DB_USER}")
print(f"  Database: {DB_NAME}")
print()

try:
    import MySQLdb
    connection = MySQLdb.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        passwd=DB_PASSWORD,
        db=DB_NAME
    )
    
    print("✓ Connection successful!")
    cursor = connection.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()
    print(f"✓ MySQL Version: {version[0]}")
    cursor.close()
    connection.close()
    
except MySQLdb.Error as e:
    print(f"✗ MySQL Error: {e}")
    print(f"  Error Code: {e.args[0]}")
    print(f"  Error Message: {e.args[1]}")
except Exception as e:
    print(f"✗ Error: {e}")
