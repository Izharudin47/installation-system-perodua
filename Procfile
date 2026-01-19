web: cd backend && python manage.py migrate && python manage.py seed || true && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
