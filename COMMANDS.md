# Installation System - Commands Reference

This document contains all commands used for the Installation System backend and frontend. Keep this file updated as you add new commands or workflows.

## Backend Commands (Django/Python)

### Environment Setup

#### 1. Install Python Dependencies
```bash
cd installation-system-perodua
pip install -r requirements.txt
```

#### 2. Setup Environment Variables
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your settings:
# - SECRET_KEY
# - Database credentials (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
# - CORS_ORIGIN (e.g., http://localhost:5173,http://localhost:3000)
# - DEBUG=True for local development
```

### Database Setup

#### 3. Create Database Migrations
```bash
cd installation-system-perodua
python manage.py makemigrations
```

#### 4. Apply Database Migrations
```bash
python manage.py migrate
```

#### 5. Seed Database with Default Users
```bash
python manage.py seed
```

This creates:
- **Admin user**: `admin@demo.com` / `mesb1234`
- **Installer user**: `installer@demo.com` / `installer123`

#### 6. Seed Database with Dummy Installers
```bash
python manage.py seed_installers
```

This creates 5 dummy installer accounts with profiles:
- `ahmad.rahman@installer.com` / `installer123` - Ahmad Electrical Services Sdn Bhd
- `lim.seng@installer.com` / `installer123` - Lim & Sons Electrical Works
- `kumar.electrical@installer.com` / `installer123` - Kumar Electrical & Engineering
- `tan.evtech@installer.com` / `installer123` - Tan EV Technology Solutions
- `hassan.charger@installer.com` / `installer123` - Hassan Charger Installation Services

All installers use password: `mesb1234`

#### 7. Create Superuser (Django Admin)
```bash
python manage.py createsuperuser
```

### Running the Server

#### 8. Start Development Server
```bash
python manage.py runserver
# Server runs on http://localhost:8000
```

#### 9. Start Production Server (with Gunicorn)
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### Database Management

#### 10. Access Django Admin Panel
```bash
# Start server first
python manage.py runserver
# Then visit http://localhost:8000/admin
```

#### 11. Reset Database (WARNING: Deletes all data)
```bash
# Delete database file (SQLite) or drop database (MySQL/PostgreSQL)
# Then run migrations again
python manage.py migrate
python manage.py seed
```

### MySQL Database Setup (Windows PowerShell)

#### 12. Setup MySQL Database
```powershell
# Run the setup script
.\setup_mysql.ps1

# Or manually:
# 1. Create database in MySQL
# 2. Run SQL script
mysql -u root -p < setup_mysql.sql
```

### Other Useful Commands

#### 13. Check Django Configuration
```bash
python manage.py check
```

#### 14. Show All Available Commands
```bash
python manage.py help
```

#### 15. Show Help for Specific Command
```bash
python manage.py help <command_name>
# Example: python manage.py help seed
```

#### 16. Run Django Shell
```bash
python manage.py shell
# Useful for testing database queries interactively
```

#### 17. Collect Static Files (for production)
```bash
python manage.py collectstatic
```

## Frontend Commands (React/Vite)

### Environment Setup

#### 18. Install Node Dependencies
```bash
cd installation-system-mock
npm install
```

#### 19. Setup Frontend Environment Variables
```bash
# Create .env file in installation-system-mock/
# Add:
VITE_API_URL=http://localhost:8000
```

### Running the Frontend

#### 20. Start Development Server
```bash
npm run dev
# Server runs on http://localhost:5173
```

#### 21. Build for Production
```bash
npm run build
# Outputs to dist/ directory
```

#### 22. Preview Production Build
```bash
npm run preview
```

### Code Quality

#### 23. Run Linter
```bash
npm run lint
```

## Full Stack Development Workflow

### Initial Setup (First Time)

1. **Backend Setup:**
   ```bash
   cd installation-system-perodua
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your database settings
   python manage.py migrate
   python manage.py seed
   python manage.py runserver
   ```

2. **Frontend Setup:**
   ```bash
   cd installation-system-mock
   npm install
   # Create .env file with VITE_API_URL=http://localhost:8000
   npm run dev
   ```

### Daily Development

1. **Start Backend:**
   ```bash
   cd installation-system-perodua
   python manage.py runserver
   ```

2. **Start Frontend (in another terminal):**
   ```bash
   cd installation-system-mock
   npm run dev
   ```

3. **Access:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - Django Admin: http://localhost:8000/admin

### After Code Changes

#### Backend Changes:
- **Model changes**: Run `python manage.py makemigrations` then `python manage.py migrate`
- **Settings changes**: Restart the server
- **Code changes**: Server auto-reloads (if using runserver)

#### Frontend Changes:
- **Code changes**: Vite auto-reloads
- **Environment changes**: Restart dev server

## Troubleshooting Commands

### Port Already in Use

#### Kill Process on Port 8000 (Backend)
```powershell
# PowerShell
Get-NetTCPConnection -LocalPort 8000 | Select-Object -ExpandProperty OwningProcess | Stop-Process -Force
```

#### Kill Process on Port 5173 (Frontend)
```powershell
# PowerShell
Get-NetTCPConnection -LocalPort 5173 | Select-Object -ExpandProperty OwningProcess | Stop-Process -Force
```

### Database Issues

#### Reset Migrations (WARNING: Use with caution)
```bash
# Delete migration files (keep __init__.py)
# Then recreate:
python manage.py makemigrations
python manage.py migrate
```

#### Check Database Connection
```bash
python manage.py dbshell
# Opens database shell
```

## Deployment Commands

### Render.com Deployment

#### Backend Deployment
- Build Command: `cd installation-system-perodua && pip install -r requirements.txt && python manage.py migrate`
- Start Command: `cd installation-system-perodua && python manage.py migrate && python manage.py seed || true && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`

#### Environment Variables for Render
```
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@host:port/database
JWT_SECRET=your-jwt-secret
CORS_ORIGIN=https://your-frontend-domain.com
GEOCODING_API_KEY=your-api-key
GEOCODING_PROVIDER=locationiq
DEBUG=False
ALLOWED_HOSTS=your-backend.onrender.com
```

## Notes

- Always activate your Python virtual environment before running backend commands
- Keep `.env` files in `.gitignore` (never commit them)
- Update this file whenever you add new commands or workflows
- Test commands in development before using in production

