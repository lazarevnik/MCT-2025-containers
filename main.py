from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
import psycopg2
import redis
import os
from contextlib import contextmanager

app = FastAPI()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'app'),
    'user': os.getenv('DB_USER', 'user'),
    'password': os.getenv('DB_PASSWORD', 'password')
}

REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'redis'),
    'port': os.getenv('REDIS_PORT', 6379),
    'decode_responses': True
}

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        raise HTTPException(status_code=500, detail="Ошибка базы данных")
    finally:
        if conn:
            conn.close()

def get_redis_connection():
    return redis.Redis(**REDIS_CONFIG)

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/ping", response_class=PlainTextResponse)
def ping(request: Request):
    client_ip = request.client.host
    if request.headers.get("x-forwarded-for"):
        client_ip = request.headers["x-forwarded-for"].split(",")[0]
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO visits (ip_address) VALUES (%s)", (client_ip,))
            conn.commit()
    r = get_redis_connection()
    r.delete('visits_count')
    return "pong"

@app.get("/visits", response_class=PlainTextResponse)
def get_visits():
    r = get_redis_connection()
    cached_count = r.get('visits_count')
    if cached_count:
        return cached_cound
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM visits")
            count = cur.fetchone()[0]
    r.setex('visits_count', 30, count)
    return str(count)
