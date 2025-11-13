#!/bin/bash

set -e

echo "Starting database initialization..."

until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q'; do
  echo "Waiting for database to be ready..."
  sleep 2
done

echo "Database is ready! Running initialization script..."

PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f /scripts/init.sql

echo "Database initialization completed successfully!"
