# Installation System Backend (Python/Django)

Backend API for the Installation System - A fullstack EV charger installation management system.

## Technology Stack

- **Runtime**: Python 3.11+
- **Framework**: Django 5.0
- **API**: Django REST Framework
- **Database**: PostgreSQL
- **ORM**: Django ORM
- **Authentication**: JWT with Simple JWT
- **Geocoding**: LocationIQ (primary) + Geoapify (fallback) + Nominatim

## Project Structure

```
backend/
├── manage.py                 # Django management script
├── config/                   # Django project settings
│   ├── settings.py          # Main settings
│   ├── urls.py              # Root URL configuration
│   ├── wsgi.py              # WSGI config
│   └── asgi.py              # ASGI config
├── api/                      # Main application
│   ├── models.py            # Database models
│   ├── serializers.py       # DRF serializers
│   ├── views.py             # API views/viewsets
│   ├── urls.py              # API URL routing
│   ├── admin.py             # Django admin configuration
│   ├── services/            # Service layer
│   │   └── geocoding.py     # Geocoding service
│   └── management/          # Management commands
│       └── commands/
│           └── seed.py      # Database seeding
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
└── parse_installers.py      # CSV parser script
```

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Setup Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

### 3. Setup Database

```bash
# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Seed database with default users
python manage.py seed
```

**Default Users Created:**
- **Admin:** `admin@demo.com` / `admin123`
- **Installer:** `installer@demo.com` / `installer123`

### 4. Start Server

```bash
# Development
python manage.py runserver

# Production (with Gunicorn)
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login
- `POST /api/auth/register` - Register (admin only)
- `POST /api/auth/register/admin` - Register admin (admin only)
- `GET /api/auth/me` - Get current user
- `POST /api/auth/refresh` - Refresh token

### Installations
- `GET /api/installations` - List installations
- `GET /api/installations/:id` - Get installation
- `POST /api/installations` - Create installation
- `PUT /api/installations/:id` - Update installation
- `PATCH /api/installations/:id/status` - Update status
- `POST /api/installations/:id/assign-installer` - Assign installer

### Installers
- `GET /api/installers` - List installers
- `GET /api/installers/:id` - Get installer
- `POST /api/installers` - Create installer
- `GET /api/installers/recommendations` - Get recommendations by location
- `POST /api/installers/bulk-import` - Bulk import installers

### Geocoding
- `POST /api/geocoding/forward` - Forward geocode (address → coordinates)
- `POST /api/geocoding/reverse` - Reverse geocode (coordinates → address)
- `POST /api/geocoding/autocomplete` - Address autocomplete
- `POST /api/geocoding/radius` - Radius search

## Development

### Database Management

```bash
# Create migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Access Django admin
python manage.py runserver
# Then visit http://localhost:8000/admin
```

### Parse Installers from CSV

```bash
python parse_installers.py
```

This will generate a Postman collection for bulk importing installers.

## Environment Variables

See `.env.example` for all required environment variables.

### Required Variables

- `SECRET_KEY` - Django secret key
- `DATABASE_URL` or individual DB settings - PostgreSQL connection
- `JWT_SECRET` - JWT signing key (can use SECRET_KEY)
- `CORS_ORIGIN` - Allowed CORS origins (comma-separated)

### Optional Variables

- `GEOCODING_API_KEY` - API key for geocoding service
- `GEOCODING_PROVIDER` - Provider to use (locationiq, geoapify, nominatim)
- `DEBUG` - Debug mode (True/False)
- `ALLOWED_HOSTS` - Allowed hosts (comma-separated)

## Deployment

### Render.com Deployment

1. **PostgreSQL Database:**
   - Create new PostgreSQL database on Render.com
   - Copy connection string to `DATABASE_URL` environment variable

2. **Web Service:**
   - Create new Web Service
   - Connect Git repository
   - Build command: `cd backend && pip install -r requirements.txt && python manage.py migrate`
   - Start command: `cd backend && python manage.py migrate && python manage.py seed && gunicorn config.wsgi:application`
   - Add environment variables

### Environment Variables for Render

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

## Migration from Node.js/TypeScript

This Python/Django backend is a complete conversion of the original Node.js/Express/TypeScript backend:

- **Prisma → Django ORM**: Models converted to Django models
- **Express routes → Django REST Framework**: Viewsets replace Express controllers
- **TypeScript → Python**: All business logic converted to Python
- **JWT authentication**: Using django-rest-framework-simplejwt
- **Geocoding service**: Python implementation with multiple provider support

## License

ISC
