#!/bin/sh
# Production entrypoint: apply migrations, then serve.
set -e

echo "Applying database migrations..."
alembic upgrade head

echo "Starting scryme..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
