# PowerShell script to set up MySQL database for Installation System
# Run this script: .\setup_mysql.ps1

Write-Host "Setting up MySQL database..." -ForegroundColor Green

# SQL commands to execute
$sqlCommands = @"
DROP DATABASE IF EXISTS installation_system;
CREATE DATABASE installation_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
DROP USER IF EXISTS 'install_user'@'localhost';
CREATE USER 'install_user'@'localhost' IDENTIFIED BY 'installer-Chargers';
GRANT ALL PRIVILEGES ON installation_system.* TO 'install_user'@'localhost';
FLUSH PRIVILEGES;
SHOW DATABASES LIKE 'installation_system';
SELECT User, Host FROM mysql.user WHERE User = 'install_user';
"@

# Execute SQL commands
Write-Host "Please enter your MySQL root password when prompted..." -ForegroundColor Yellow
$sqlCommands | mysql -u root -p

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nDatabase setup completed successfully!" -ForegroundColor Green
    Write-Host "Database: installation_system" -ForegroundColor Cyan
    Write-Host "User: install_user" -ForegroundColor Cyan
    Write-Host "Password: installer-Chargers" -ForegroundColor Cyan
} else {
    Write-Host "`nError setting up database. Please check your MySQL connection." -ForegroundColor Red
}




