#!/bin/sh
set -e

echo "Starting database initialization..."

go run init-db.go

echo "Database initialization complete"