from fastapi import FastAPI, Request, HTTPException
import psycopg2
import os
from contextlib import contextmanager

app = FastAPI()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'port': os.getenv('DB_PORT', '5000'),
    'database': os.getenv('DB_NAME', 'app'),
    'user': os.getenv('DB_USER', 'user'),
    'password': os.getenv('DB_PASSWORD', 'password')
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

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/ping")
def ping(request: Request):
    client_ip = request.client.host
    if request.headers.get("x-forwarded-for"):
        client_ip = request.headers["x-forwarded-for"].split(",")[0]
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO visits (ip_address) VALUES (%s)", (client_ip,))
            conn.commit()
    return "pong"

@app.get("/visits")
def get_visits():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM visits")
            count = cur.fetchone()[0]
    return str(count)
