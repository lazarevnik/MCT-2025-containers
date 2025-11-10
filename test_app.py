import os
import time
import socket
import pytest
import redis
import psycopg2
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

def wait_for_tcp(host, port, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            sock = socket.create_connection((host, int(port)), timeout=1)
            sock.close()
            return True
        except Exception:
            time.sleep(0.5)
    return False

@pytest.fixture(scope="module", autouse=True)
def wait_services():
    db_host = os.getenv("DB_HOST", "db")
    db_port = int(os.getenv("DB_PORT", 5432))
    redis_host = os.getenv("REDIS_HOST", "redis")
    redis_port = int(os.getenv("REDIS_PORT", 6379))

    assert wait_for_tcp(db_host, db_port, timeout=60), "Postgres did not become available"
    assert wait_for_tcp(redis_host, redis_port, timeout=60), "Redis did not become available"

    time.sleep(1)
    yield

def _strip_response_text(resp):
    return resp.text.strip().strip('"').strip()

def test_ping_and_visits_count():
    r1 = client.get("/ping")
    assert r1.status_code == 200
    assert _strip_response_text(r1) == "pong"

    r2 = client.get("/ping")
    assert r2.status_code == 200
    assert _strip_response_text(r2) == "pong"

    rv = client.get("/visits")
    assert rv.status_code == 200
    val = int(_strip_response_text(rv))
    assert val >= 2

def test_cache_consistency_with_db():
    redis_host = os.getenv("REDIS_HOST", "redis")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    redis_key = os.getenv("REDIS_KEY", "visits_count")

    r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
    time.sleep(0.5)
    cache_val = r.get(redis_key)
    assert cache_val is not None, "Redis cache missing"
    cache_val = int(cache_val)

    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME", "app"),
        user=os.getenv("DB_USER", "user"),
        password=os.getenv("DB_PASS", "password"),
    )
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM visits;")
    db_count = cur.fetchone()[0]
    cur.close()
    conn.close()

    assert cache_val == db_count
