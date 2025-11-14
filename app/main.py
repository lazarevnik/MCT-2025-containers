from fastapi import FastAPI, Request
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import os

app = FastAPI()

DB_PARAMS = {
    "host": os.getenv("DB_HOST", "db"),
    "port": os.getenv("DB_PORT", "5432"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "dbname": os.getenv("DB_NAME", "app"),
}

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"


def get_db_connection():
    return psycopg2.connect(**DB_PARAMS, cursor_factory=RealDictCursor)


@app.get("/ping")
def ping(request: Request):
    client_ip = request.client.host
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO visits (ip) VALUES (%s)", (client_ip,))
    conn.commit()
    cur.close()
    conn.close()

    redis_client.incr("ping_count")
    return {"response": "pong"}


@app.get("/visits")
def visits():
    if DEV_MODE:
        return {"visits": -1, "source": "dev"}
    cached = redis_client.get("ping_count")
    if cached is not None:
        return {"visits": int(cached), "source": "cache"}

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM visits")
    row = cur.fetchone()["count"]
    cur.close()
    conn.close()

    redis_client.set("ping_count", row)
    return {"visits": row, "source": "db"}