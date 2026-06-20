#!/usr/bin/env bash
set -euo pipefail

echo "Running Alembic migrations …"
alembic upgrade head

echo "Starting uvicorn …"
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
