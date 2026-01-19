#!/bin/bash
# Startup script for Render.com deployment
# Runs migrations and seeds database before starting server

set -e

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "📊 Running database migrations..."
python manage.py migrate

echo "🌱 Seeding database..."
python manage.py seed || echo "⚠️  Seeding failed, continuing..."

echo "🚀 Starting server..."
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
