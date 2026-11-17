#!/bin/sh
# Container start-up: apply migrations, (re)seed master data, then serve.
# Both steps are idempotent, so restarting the container is always safe.
set -e

echo "Applying database migrations..."
flask db upgrade

echo "Seeding master data..."
flask seed-master

if [ "${SEED_DEMO:-false}" = "true" ] && flask --help | grep -q seed-demo; then
  echo "Seeding demo data..."
  flask seed-demo
fi

echo "Starting gunicorn..."
exec gunicorn --bind 0.0.0.0:5000 --workers "${GUNICORN_WORKERS:-3}" --timeout 60 wsgi:app
