#!/usr/bin/env bash
set -euo pipefail

/app/deployment/scripts/wait-for-postgres.sh

if [[ "${RUN_MIGRATIONS:-1}" == "1" ]]; then
  echo "Applying Alembic migrations..."
  (cd /app/backend && alembic upgrade head)
fi

echo "Starting API..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers "${UVICORN_WORKERS:-2}"
