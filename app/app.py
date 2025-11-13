import os
import time
import psycopg2
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "db"),
    "user": os.getenv("DB_USER", "user"),
    "password": os.getenv("DB_PASSWORD", "pass"),
    "dbname": os.getenv("DB_NAME", "app"),
}

ENV = os.getenv("ENV", "prod")

def connect_db(max_retries=3, delay=1):
    for attempt in range(1, max_retries + 1):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            logger.info("DB connection established")
            return conn
        except psycopg2.OperationalError as e:
            logger.warning(f"DB connection attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(delay)
            else:
                logger.error("DB connection failed -> max retries reached :(")
                raise

@app.route("/")
def index():
    return jsonify({"status": "ok"})

@app.route('/ping')
def ping():
    ip = request.remote_addr

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO visits (ip) VALUES (%s)", (ip,))
    conn.commit()
    cur.close()
    conn.close()
    return "pong"

@app.route('/visits')
def visits():
    if ENV == "dev":
        return "-1"
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM visits")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return str(count)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)