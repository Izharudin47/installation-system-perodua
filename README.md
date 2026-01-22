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

**Important for Local Development:**
- Set `CORS_ORIGIN=http://localhost:5173` (or your frontend dev server port)
- Set `DEBUG=True` for development
- Configure MySQL database settings (or use PostgreSQL via `DATABASE_URL`)

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

**Note:** All API endpoints are aligned with the frontend (`installation-system-mock`) expectations. The backend accepts frontend parameter names and returns data in the nested structure expected by the frontend.

### Authentication
- `POST /api/auth/login` - Login (returns `{ token, user }`)
- `POST /api/auth/register` - Register (admin only, returns `{ user }`)
- `POST /api/auth/register/admin` - Register admin (admin only)
- `GET /api/auth/me` - Get current user (returns `{ user }`)
- `POST /api/auth/refresh` - Refresh token (accepts Bearer token in Authorization header, returns `{ token }`)

### Installations
- `GET /api/installations` - List installations (returns `{ installations: [...] }`)
- `GET /api/installations/:id` - Get installation (returns direct object)
- `POST /api/installations` - Create installation (accepts nested `customer` and `charger` objects, returns `{ id, message }`)
- `PUT /api/installations/:id` - Update installation (accepts nested format, returns `{ id, message }`)
- `PATCH /api/installations/:id/status` - Update status (accepts kebab-case status, returns `{ id, status, message }`)
- `POST /api/installations/:id/assign-installer` - Assign installer (accepts `installerId`, returns `{ id, message }`)
- `POST /api/installations/:id/documents` - Upload document (returns `{ id, fileName, filePath, message }`)
- `GET /api/installations/:id/documents` - Get installation documents (returns `{ documents: [...] }`)

### Installers
- `GET /api/installers` - List installers (returns `{ installers: [...] }`)
- `GET /api/installers/:id` - Get installer (returns direct object with nested `location` and `compliance`)
- `POST /api/installers` - Create installer
- `GET /api/installers/recommendations?lat=X&lng=Y&radius=Z` - Get recommendations (accepts `lat`/`lng` or `latitude`/`longitude`, returns `{ recommendations: [...] }`)
- `POST /api/installers/bulk-import` - Bulk import installers

### Geocoding
- `POST /api/geocoding/forward` - Forward geocode (accepts `{ address: string }`, returns direct `GeocodeResult`)
- `POST /api/geocoding/reverse` - Reverse geocode (accepts `{ lat, lng }` or `{ latitude, longitude }`, returns direct `GeocodeResult`)
- `POST /api/geocoding/autocomplete` - Address autocomplete (accepts `{ query, limit }`, returns `{ results: [...] }`)
- `POST /api/geocoding/radius` - Radius search

### Files/Documents
- `GET /api/files/:id` - Download document file
- `DELETE /api/files/:id` - Delete document

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

## Frontend Alignment

This backend is fully aligned with the frontend (`installation-system-mock`) API expectations:

### Data Structure Transformation
- **Nested Structures**: Backend stores flat fields but serializers transform them to nested structures (e.g., `customer` object, `charger` object, `location` object)
- **Status Values**: Backend stores snake_case (`pending_assignment`) but transforms to kebab-case (`pending-assignment`) for frontend
- **Response Wrapping**: List endpoints return `{ items: [...] }`, detail endpoints return direct objects

### Parameter Name Mapping
- Frontend sends `lat`/`lng` → Backend accepts both `lat`/`lng` and `latitude`/`longitude`
- Frontend sends `installerId` → Backend accepts both `installerId` and `installer_id`
- Frontend sends kebab-case status → Backend converts to snake_case internally

### Key Features
- **Nested Serializers**: `InstallationNestedSerializer` and `InstallerNestedSerializer` transform flat backend data to nested frontend format
- **Status Transformation**: Automatic conversion between snake_case (backend) and kebab-case (frontend)
- **Computed Fields**: Installer job counts (`completedJobs`, `activeJobs`, `pendingJobs`) are computed from related installations
- **Timestamp Management**: Automatic timestamp updates based on status changes

## Migration from Node.js/TypeScript

This Python/Django backend is a complete conversion of the original Node.js/Express/TypeScript backend:

- **Prisma → Django ORM**: Models converted to Django models
- **Express routes → Django REST Framework**: Viewsets replace Express controllers
- **TypeScript → Python**: All business logic converted to Python
- **JWT authentication**: Using django-rest-framework-simplejwt
- **Geocoding service**: Python implementation with multiple provider support

## License

ISC
