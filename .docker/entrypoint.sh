#!/bin/sh
set -e

echo "🚀 Waiting for database..."

python - <<'EOF'
import os, time
import psycopg2

db = os.getenv("POSTGRES_DB", "piece_of_shit")
user = os.getenv("POSTGRES_USER", "piece_of_shit_user")
password = os.getenv("POSTGRES_PASSWORD", "piece_of_shit_password")
host = os.getenv("POSTGRES_HOST", "db")
port = os.getenv("POSTGRES_PORT", "5432")

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
        print(f"⏳ Database not ready ({e}), retrying...")
        time.sleep(1)
EOF

echo "✅ Database is ready!"

echo "🔄 Running migrations (project/manage.py migrate)..."
python project/manage.py migrate --noinput
echo "✅ Migrations done."

echo "📦 Collecting static files..."
python project/manage.py collectstatic --noinput

echo "▶️ Starting Daphne..."
exec daphne -b 0.0.0.0 -p 8000 project.config.asgi:application
