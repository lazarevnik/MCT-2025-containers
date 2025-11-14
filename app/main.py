import os
import time
from contextlib import contextmanager

import psycopg2
from fastapi import FastAPI, Request, Response
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@db/app")

app = FastAPI()

def get_db_connection():
    """Функция для установки соединения с БД с попытками переподключения."""
    while True:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            return conn
        except psycopg2.OperationalError as e:
            print(f"Ошибка подключения к БД: {e}. Повторная попытка через 1 секунду...")
            time.sleep(1)

@contextmanager
def db_cursor():
    """Контекстный менеджер для удобной работы с курсором и транзакциями."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            yield cur
            conn.commit()
    finally:
        conn.close()


# def init_db():
#     with db_cursor() as cur:
#         cur.execute("""
#             CREATE TABLE IF NOT EXISTS visits (
#                 id SERIAL PRIMARY KEY,
#                 ip_address VARCHAR(45) NOT NULL,
#                 created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
#             );
#         """)


@app.get("/")
def read_root():
    return {"status": "ok"}


@app.get("/ping", response_class=Response)
def ping(request: Request):
    client_ip = request.client.host
    with db_cursor() as cur:
        cur.execute("INSERT INTO visits (ip_address) VALUES (%s)", (client_ip,))
    return Response(content="pong", media_type="text/plain")


@app.get("/visits", response_class=Response)
def get_visits():
    with db_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total_visits FROM visits;")
        result = cur.fetchone()
        count = result[0] if result else 0
    return Response(content=str(count), media_type="text/plain")


# init_db()