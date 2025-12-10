#!/bin/sh

set -e

echo "Esecuzione delle migrazioni del database..."
python manage.py migrate

exec "$@"