#!/bin/sh
set -e

echo "🚀 Waiting for database..."

poetry run python - <<'EOF'
import os, time
import psycopg2

db = os.getenv("POSTGRES_DB", "expenses")
user = os.getenv("POSTGRES_USER", "expenses_user")
password = os.getenv("POSTGRES_PASSWORD", "expenses_pass")
host = os.getenv("DB_HOST", "db")
port = os.getenv("DB_PORT", "5432")

while True:
    try:
        conn = psycopg2.connect(
            dbname=db,
            user=user,
            password=password,
            host=host,
            port=port,
        )
        conn.close()
        break
    except Exception as e:
        print("⏳ Database not ready, retrying...")
        time.sleep(0.5)
EOF

echo "✅ Database is ready!"

echo "🔄 Running migrations..."
poetry run python -m project.manage migrate --noinput

echo "📦 Collecting static files..."
poetry run python -m project.manage collectstatic --noinput

echo "▶️ Starting Daphne..."
exec poetry run daphne -b 0.0.0.0 -p 8000 project.config.asgi:application
