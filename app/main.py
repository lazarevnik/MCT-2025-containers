from flask import Flask, request
import psycopg2
import redis
import os

app = Flask(__name__)

PG_HOST = os.environ.get("POSTGRES_HOST", "db")
PG_DB = os.environ.get("POSTGRES_DB", "app")
PG_USER = os.environ.get("POSTGRES_USER", "user")
PG_PASS = os.environ.get("POSTGRES_PASSWORD", "password")
PG_PORT = os.environ.get("POSTGRES_PORT", 5432)

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

conn = psycopg2.connect(host=PG_HOST, dbname=PG_DB, user=PG_USER, password=PG_PASS, port=PG_PORT)
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

@app.route('/ping', methods=['GET'])
def ping():
    ip = request.remote_addr
    with conn.cursor() as cur:
        cur.execute("INSERT INTO visits (ip) VALUES (%s)", (ip,))
        conn.commit()
        redis_client.incr('visits_count')
    return "pong"

@app.route('/visits', methods=['GET'])
def visits():
    visits = redis_client.get('visits_count')
    if visits is None:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM visits;")
            visits = cur.fetchone()[0]
            redis_client.set('visits_count', visits)
    return str(visits)

@app.route('/', methods=['GET'])
def index():
    return "OK"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
