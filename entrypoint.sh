#!/bin/bash

set -e

if [ -n "$DATABASE_HOST" ]; then
    echo "Waiting for database at $DATABASE_HOST:${DATABASE_PORT:-5432}..."
    timeout=30
    while ! nc -z "$DATABASE_HOST" "${DATABASE_PORT:-5432}" 2>/dev/null; do
        timeout=$((timeout - 1))
        if [ $timeout -le 0 ]; then
            echo "Database connection timeout!"
            exit 1
        fi
        sleep 1
    done
    echo "Database is ready!"
fi

chown -R appuser:appgroup /app/media /app/staticfiles

echo "Running Database Migrations..."
python manage.py migrate --noinput

echo "Collecting Static Files..."
python manage.py collectstatic --noinput --clear

echo "Configuring Django crontab..."
python manage.py crontab remove || true
python manage.py crontab add

echo "Starting cron daemon..."
service cron start

echo "Starting Gunicorn server as user 'appuser'..."
exec gosu appuser:appgroup "$@"