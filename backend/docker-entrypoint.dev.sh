#!/bin/sh
# Dev entrypoint: wait for Postgres, apply migrations, then run uvicorn with reload.
set -e

echo "Applying database migrations..."
alembic upgrade head

echo "Starting scryme (dev, reload)..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
