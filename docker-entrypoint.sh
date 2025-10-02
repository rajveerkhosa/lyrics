#!/bin/bash
set -e

echo "Starting Django application..."

# Wait for database to be ready (if using PostgreSQL)
if [ -n "$DATABASE_URL" ]; then
    echo "Waiting for database to be ready..."
    python << END
import sys
import time
import psycopg2
from urllib.parse import urlparse

max_retries = 30
retry_count = 0

# Parse DATABASE_URL
import os
db_url = os.environ.get('DATABASE_URL', '')
if db_url:
    result = urlparse(db_url)
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port or 5432

    while retry_count < max_retries:
        try:
            conn = psycopg2.connect(
                dbname=database,
                user=username,
                password=password,
                host=hostname,
                port=port
            )
            conn.close()
            print("Database is ready!")
            sys.exit(0)
        except psycopg2.OperationalError:
            retry_count += 1
            print(f"Database unavailable, waiting... ({retry_count}/{max_retries})")
            time.sleep(1)

    print("Could not connect to database")
    sys.exit(1)
END
fi

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting application server..."

# Execute the main command
exec "$@"
