import os
import time
from contextlib import contextmanager

import psycopg2
from fastapi import FastAPI, Request, Response

import redis


APP_ENV = os.environ.get("APP_ENV", "prod")

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@db/app")
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")

app = FastAPI()
redis_client = None

if APP_ENV == "prod":
    print("Production mode")
    try:
        redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
        redis_client.ping()
    except redis.exceptions.ConnectionError as e:
        print(f"Не удалось подключиться к Redis: {e}")
        redis_client = None

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

else:
    print("Development mode.")
    db_cursor = contextmanager(lambda: (yield None))


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
    if APP_ENV == "prod":
        client_ip = request.client.host
        with db_cursor() as cur:
            cur.execute("INSERT INTO visits (ip_address) VALUES (%s)", (client_ip,))
        
        if redis_client:
            try:
                redis_client.incr("visits_count")
            except redis.exceptions.ConnectionError as e:
                print(f"Ошибка Redis при инкременте счетчика: {e}")

    return Response(content="pong", media_type="text/plain")


@app.get("/visits", response_class=Response)
def get_visits():
    if APP_ENV == "dev":
        return Response(content="-1", media_type="text/plain")
    
    count = 0

    if redis_client:
        try:
            cached_count = redis_client.get("visits_count")
            if cached_count is not None:
                return Response(content=str(cached_count), media_type="text/plain")
        except redis.exceptions.ConnectionError as e:
            print(f"Ошибка Redis при получении счетчика: {e}")

    with db_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total_visits FROM visits;")
        result = cur.fetchone()
        count = result[0] if result else 0

    if redis_client:
        try:
            redis_client.set("visits_count", count)
        except redis.exceptions.ConnectionError as e:
            print(f"Ошибка Redis при установке счетчика: {e}")
            
    return Response(content=str(count), media_type="text/plain")


# init_db()