#!/bin/sh
set -e

echo "Waiting for Postgres..."
python - <<'PY'
import os, time
import psycopg

host = os.getenv("DB_HOST", "db")
port = os.getenv("DB_PORT", "5432")
name = os.getenv("DB_NAME", "dhyan")
user = os.getenv("DB_USER", "dhyan")
pw = os.getenv("DB_PASSWORD", "dhyan")

dsn = f"host={host} port={port} dbname={name} user={user} password={pw}"

t0 = time.time()
while True:
    try:
        psycopg.connect(dsn).close()
        break
    except Exception:
        if time.time() - t0 > 60:
            raise
        time.sleep(1)

print("Postgres is ready")
PY

echo "Running migrations..."
python manage.py migrate

echo "Seeding roles..."
python manage.py seed_roles

echo "Starting gunicorn..."
exec gunicorn core.wsgi:application -b 0.0.0.0:8000 --workers 3 --timeout 60
