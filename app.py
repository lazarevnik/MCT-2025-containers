from fastapi import FastAPI, Request
import os
import psycopg2
import redis

app = FastAPI()

# DB config
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "app")
DB_USER = os.getenv("DB_USER", "user")
DB_PASS = os.getenv("DB_PASS", "password")
DB_PORT = int(os.getenv("DB_PORT", 5432))

# Redis config
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_KEY = os.getenv("REDIS_KEY", "visits_count")
REDIS_TTL = int(os.getenv("REDIS_TTL", 0))

def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

# Try create redis client (may not be ready immediately)
def get_redis_client():
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        r.ping()
        return r
    except Exception:
        return None

@app.get("/ping")
async def ping(request: Request):
    ip = request.client.host if request.client else "unknown"

    # insert into DB
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO visits (ip) VALUES (%s);", (ip,))
    conn.commit()
    cur.close()

    # get fresh count from DB to ensure consistency
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM visits;")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()

    # update redis cache (best-effort)
    r = get_redis_client()
    if r:
        try:
            if REDIS_TTL and int(REDIS_TTL) > 0:
                r.setex(REDIS_KEY, int(REDIS_TTL), str(count))
            else:
                r.set(REDIS_KEY, str(count))
        except Exception:
            pass

    return "pong"

@app.get("/visits")
async def visits():
    # try redis first
    r = get_redis_client()
    if r:
        try:
            val = r.get(REDIS_KEY)
            if val is not None:
                return str(int(val))
        except Exception:
            # fall back to db
            pass

    # fallback: read DB and populate redis
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM visits;")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()

    # populate redis best-effort
    if r:
        try:
            if REDIS_TTL and int(REDIS_TTL) > 0:
                r.setex(REDIS_KEY, int(REDIS_TTL), str(count))
            else:
                r.set(REDIS_KEY, str(count))
        except Exception:
            pass

    return str(count)
