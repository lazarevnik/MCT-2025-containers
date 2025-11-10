from fastapi import FastAPI, Request
import psycopg2
import os

app = FastAPI()

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "app")
DB_USER = os.getenv("DB_USER", "user")
DB_PASS = os.getenv("DB_PASS", "password")

def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

@app.get("/ping")
async def ping(request: Request):
    ip = request.client.host
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO visits (ip) VALUES (%s);", (ip,))
    conn.commit()
    cur.close()
    conn.close()
    return "pong"

@app.get("/visits")
async def visits():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM visits;")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return str(count)
