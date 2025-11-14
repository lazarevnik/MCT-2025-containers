set -e

echo "Waiting for PostgreSQL"

until pg_isready -h db -U user -d app; do
  sleep 2
done

psql -v ON_ERROR_STOP=1 -h db -U user -d app -f /app/init.sql

echo "Database initialization completed successfully"