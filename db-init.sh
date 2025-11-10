#!/usr/bin/env bash
set -euo pipefail

DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-app}
DB_USER=${DB_USER:-user}
DB_PASS=${DB_PASS:-password}
SQL_PATH=${SQL_PATH:-/sql/init.sql}
MAX_WAIT=${MAX_WAIT:-60}

export PGPASSWORD="$DB_PASS"

echo "db-init: waiting for Postgres at ${DB_HOST}:${DB_PORT} ..."

n=0
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; do
  n=$((n+1))
  if [ "$n" -ge "$MAX_WAIT" ]; then
    echo "db-init: timeout waiting for postgres"
    exit 2
  fi
  sleep 1
done

echo "db-init: Postgres is ready, running init SQL: ${SQL_PATH}"

psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$SQL_PATH"
rc=$?
if [ $rc -eq 0 ]; then
  echo "db-init: SQL executed successfully"
else
  echo "db-init: SQL execution failed with code $rc"
fi

exit $rc
