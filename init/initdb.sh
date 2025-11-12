#!/bin/bash
set -e

echo "Database is ready. Running init script..."
psql "$DATABASE_URL" -f /server/init/initdb.sql
echo "Initialization complete."
