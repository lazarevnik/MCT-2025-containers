#!/usr/bin/env bash
set -euo pipefail

cd ping-visits

# === Загружаем переменные окружения ===
if [ -f .env ]; then
  echo "Loading environment from ping-visits/.env..."
  set -a
  source .env
  set +a
else
  echo ".env file not found"
  exit 1
fi

: "${DB_USER:?Environment variable DB_USER not set}"
: "${DB_PASSWORD:?Environment variable DB_PASSWORD not set}"
: "${DB_NAME:?Environment variable DB_NAME not set}"

PORT=8080
URL="http://localhost:${PORT}"

echo "🧹 Cleaning up old containers..."
docker compose down -v --remove-orphans >/dev/null 2>&1 || true

echo "🚀 Starting services"
docker compose up -d --build

echo "⏳ Waiting PostgreSQL ..."
timeout=60
while ! docker compose exec -T db pg_isready -U "${DB_USER}" -d "${DB_NAME}" >/dev/null 2>&1; do
  ((timeout--))
  if [ $timeout -eq 0 ]; then
    echo "❌ PostgreSQL failed to start!"
    docker compose logs db
    exit 1
  fi
  sleep 1
done
echo "✅ PostgreSQL is ready."

echo "⏳ Check whether database initialized..."
cols=$(docker compose exec -T db psql -U "${DB_USER}" -d "${DB_NAME}" -tAc "SELECT column_name FROM information_schema.columns WHERE table_name='visits' ORDER BY ordinal_position;")
if [[ "$cols" != *"id"* || "$cols" != *"ip_address"* || "$cols" != *"created_at"* ]]; then
  echo "❌ Table 'visits' missing expected columns."
  exit 1
fi
echo "✅ Table 'visits' with columns 'id', 'ip_address' 'created_at' exists."

echo "⏳ Waiting for web service ${URL} ..."
timeout=60
while ! curl -f "${URL}" >/dev/null 2>&1; do
  ((timeout--))
  if [ $timeout -le 0 ]; then
    echo "❌ Web service failed to start!"
    docker compose logs
    exit 1
  fi
  sleep 1
done
echo "✅ Web service is ready"

echo "Testing web response..."
RESPONSE=$(curl -s "${URL}/ping" || true)
if [[ "$RESPONSE" != "pong" ]]; then
  echo "❌ Expected 'pong', got: '$RESPONSE'"
  docker compose logs
  exit 1
else
  echo "✅ Test web respone passed"
fi

echo "Testing Redis cache..."
first=$(curl -s ${URL}/visits)
cached=$(docker compose exec -T redis redis-cli GET nvisits || true)
if [[ -z "$cached" ]]; then
  echo "❌ Redis cache not populated after first /visits"
  docker compose logs
  exit 1
fi
echo "✅ Redis cache populated: $cached"

second=$(curl -s ${URL}/visits)
if [[ "$first" != "$second" ]]; then
  echo "❌ Cache miss: expected $first, got $second"
  docker compose logs
  exit 1
fi
echo "✅ Cache hit is correct"

curl -s ${URL}/ping > /dev/null
sleep 1

echo "Checking Redis cache invalidation..."
after_ping=$(docker compose exec -T redis redis-cli GET nvisits || true)
if [[ -n "$after_ping" ]]; then
  echo "❌ Cache should be invalidated, but found: $after_ping"
  docker compose logs
  exit 1
fi
echo "✅ Redis cache invalidated successfully."

echo "🧹 Stopping and cleaning up containers..."
docker compose down -v

echo "✅ All tests passed"
