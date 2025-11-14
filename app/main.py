import os
from fastapi import FastAPI, Request
import psycopg2

app = FastAPI()

APP_ENV = os.getenv("APP_ENV", "prod")
DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "app")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")


def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


@app.get("/ping")
def ping(request: Request):
    if APP_ENV == "prod":
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO visits(ip) VALUES (%s)", (request.client.host,))
        conn.commit()
        cur.close()
        conn.close()
    return 'pong'


@app.get("/visits")
def visits():
    if APP_ENV == "dev":
        return -1
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM visits")
    n = cur.fetchone()[0]
    cur.close()
    conn.close()
    return n
