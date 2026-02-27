#!/usr/bin/env bash
set -euo pipefail

host="${POSTGRES_HOST:-db}"
port="${POSTGRES_PORT:-5432}"
user="${POSTGRES_USER:-postgres}"

echo "Waiting for PostgreSQL at ${host}:${port}..."
until pg_isready -h "$host" -p "$port" -U "$user" >/dev/null 2>&1; do
  sleep 1
done

echo "PostgreSQL is ready."
