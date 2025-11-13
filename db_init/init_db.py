import psycopg2
import os
import time

PG_HOST = os.environ.get("POSTGRES_HOST", "db")
PG_DB = os.environ.get("POSTGRES_DB", "app")
PG_USER = os.environ.get("POSTGRES_USER", "user")
PG_PASS = os.environ.get("POSTGRES_PASSWORD", "password")
PG_PORT = os.environ.get("POSTGRES_PORT", 5432)

while True:
    try:
        conn = psycopg2.connect(host=PG_HOST, dbname=PG_DB, user=PG_USER, password=PG_PASS, port=PG_PORT)
        break
    except Exception:
        time.sleep(2)

with conn.cursor() as cur:
    cur.execute("""
    CREATE TABLE IF NOT EXISTS visits (
        id SERIAL PRIMARY KEY,
        ip VARCHAR(64),
        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
conn.close()
