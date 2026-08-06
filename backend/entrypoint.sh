#!/bin/bash
set -e

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting Gunicorn server..."
exec gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
