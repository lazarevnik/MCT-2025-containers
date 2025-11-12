import os
import psycopg2
from enum import Enum
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

class AppMode(Enum):
    DEV = 0
    PROD = 1

app = FastAPI()

app.state.mode = AppMode.DEV if os.getenv("APP_MODE", "").upper() == "DEV" else AppMode.PROD

app.state.database = os.getenv("DATABASE_URL", "")

if not app.state.database:
    print("Running without database, are you sure this is intended?")

def insert_visit(ip: str):
    if not app.state.database:
        return
    conn = psycopg2.connect(app.state.database)
    with conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO visits (ip_address) VALUES (%s)", (ip,))
    conn.close()

def count_visits() -> int:
    if not app.state.database:
        return
    conn = psycopg2.connect(app.state.database)
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM visits")
            return cur.fetchone()[0]

@app.get("/ping", response_class=PlainTextResponse)
async def ping(request: Request):
    ip = request.client.host
    try:
        insert_visit(ip)
    except Exception as e:
        print("Database insert failed:", e)
    return "pong"

@app.get("/visits", response_class=PlainTextResponse)
async def visits():
    if app.state.mode == AppMode.DEV:
        return "-1"
    try:
        total = count_visits()
        return str(total)
    except Exception as e:
        print("Database count failed:", e)
        return "0"
