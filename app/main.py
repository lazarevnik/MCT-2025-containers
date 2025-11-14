from fastapi import FastAPI, Request
import psycopg2
import redis
import os

DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

app = FastAPI()

DB_HOST = os.getenv("DB_HOST", "db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1111")
DB_NAME = os.getenv("DB_NAME", "visitsdb")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME
    )

def get_redis_connection():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


@app.get("/ping")
def ping(request: Request):
    client_ip = request.client.host
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO visits (ip) VALUES (%s);", (client_ip,))
    conn.commit()
    cur.close()
    conn.close()
    
    r = get_redis_connection()
    r.incr("total_visits")

    return {"message": "pong"}

@app.get("/visits")
def visits():
    
    if DEV_MODE:
        return {"visits": -1}
    r = get_redis_connection()
    cached = r.get("total_visits")
    if cached is not None:
        return {"visits": int(cached)}
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM visits;")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()

    r.set("total_visits", count)
    return {"visits": count}
