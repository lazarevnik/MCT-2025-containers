from fastapi import FastAPI, Request
import os
import psycopg2

app = FastAPI()

visits_count = 0

DB_NAME = os.getenv("DB_NAME", "request_db")
DB_USER = os.getenv("DB_USER", "user_db")
DB_PASWD = os.getenv("DB_PASWD", "passwd")
DB_PORT = int(os.getenv("DB_PORT", 5432))


def get_db_conn():
    return psycopg2.connect(
        host="db",
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASWD,
        port = DB_PORT
    )

@app.get("/")
async def hello_world():
    return "Hello, user!"

@app.get("/ping")
async def ping_pong(request: Request):
    global visits_count
    visits_count += 1

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO requests (request_src) VALUES (%s);
    """, (request.client.host, ))
    conn.commit()
    cur.close()
    conn.close()
    
    return 'pong'

@app.get("/visits")
async def visits_request():
    return visits_count