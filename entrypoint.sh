#!/bin/sh

set -e

chown -R appuser:appgroup /app/media /app/staticfiles /var/log

printenv > /etc/environment

echo "Running Database Migrations..."
su-exec appuser:appgroup python manage.py migrate --noinput

echo "Collecting Static Files..."
su-exec appuser:appgroup python manage.py collectstatic --noinput

echo "Configuring Django crontab..."
su-exec appuser:appgroup python manage.py crontab remove
su-exec appuser:appgroup python manage.py crontab add

echo "Starting cron daemon..."
crond -b -l 2 -L /var/log/cron.log

echo "Starting Gunicorn server as user 'appuser'..."
exec su-exec appuser:appgroup "$@"