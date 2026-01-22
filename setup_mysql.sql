-- MySQL Database Setup Script for Installation System
-- Run this script as MySQL root user: mysql -u root -p < setup_mysql.sql
-- Or copy and paste these commands into MySQL command line

-- Drop database if it exists (use with caution!)
DROP DATABASE IF EXISTS installation_system;

-- Create the database
CREATE DATABASE installation_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Drop user if exists (use with caution!)
DROP USER IF EXISTS 'install_user'@'localhost';

-- Create the user
CREATE USER 'install_user'@'localhost' IDENTIFIED BY 'installer-Chargers';

-- Grant all privileges on the database to the user
GRANT ALL PRIVILEGES ON installation_system.* TO 'install_user'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;

-- Verify the setup
SHOW DATABASES LIKE 'installation_system';
SELECT User, Host FROM mysql.user WHERE User = 'install_user';




