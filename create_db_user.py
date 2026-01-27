#!/usr/bin/env python
"""Create MySQL user if it doesn't exist"""

import MySQLdb
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

DB_USER = os.getenv('DB_USER', 'install_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'installer-Chargers')
DB_NAME = os.getenv('DB_NAME', 'installation_system')
DB_HOST = os.getenv('DB_HOST', 'localhost')

print("Attempting to connect as root...")

try:
    # Try connecting as root with no password first
    connection = MySQLdb.connect(host=DB_HOST, user='root')
    print("✓ Connected as root (no password)")
except MySQLdb.Error as e:
    print(f"Root (no password) failed: {e}")
    print("Trying root with empty password...")
    try:
        connection = MySQLdb.connect(host=DB_HOST, user='root', passwd='')
        print("✓ Connected as root (empty password)")
    except MySQLdb.Error as e2:
        print(f"✗ Both attempts failed: {e2}")
        root_pass = input("Enter MySQL root password: ")
        connection = MySQLdb.connect(host=DB_HOST, user='root', passwd=root_pass)
        print("✓ Connected as root")

cursor = connection.cursor()

try:
    # Drop existing user if exists
    print(f"Dropping user '{DB_USER}'@'{DB_HOST}' if exists...")
    cursor.execute(f"DROP USER IF EXISTS '{DB_USER}'@'{DB_HOST}'")
    print("✓ Done")
except Exception as e:
    print(f"Note: {e}")

try:
    # Drop existing database if exists
    print(f"Dropping database '{DB_NAME}' if exists...")
    cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
    print("✓ Done")
except Exception as e:
    print(f"Note: {e}")

try:
    # Create database
    print(f"Creating database '{DB_NAME}'...")
    cursor.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    print("✓ Database created")
except Exception as e:
    print(f"✗ Error creating database: {e}")

try:
    # Create user
    print(f"Creating user '{DB_USER}'@'{DB_HOST}'...")
    cursor.execute(f"CREATE USER '{DB_USER}'@'{DB_HOST}' IDENTIFIED BY '{DB_PASSWORD}'")
    print("✓ User created")
except Exception as e:
    print(f"✗ Error creating user: {e}")

try:
    # Grant privileges
    print(f"Granting privileges...")
    cursor.execute(f"GRANT ALL PRIVILEGES ON {DB_NAME}.* TO '{DB_USER}'@'{DB_HOST}'")
    cursor.execute("FLUSH PRIVILEGES")
    print("✓ Privileges granted")
except Exception as e:
    print(f"✗ Error granting privileges: {e}")

connection.commit()
cursor.close()
connection.close()

print("\n✓ Setup complete! Testing connection with new user...")

import time
time.sleep(1)

try:
    test_conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)
    print(f"✓ Successfully connected as '{DB_USER}'!")
    test_conn.close()
except MySQLdb.Error as e:
    print(f"✗ Connection test failed: {e}")
