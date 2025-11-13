from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
import psycopg2
import os
import time

app = FastAPI()

DB_CONFIG = {
    "dbname": "visits_db",
    "user": "user", 
    "password": "password",
    "host": "db",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.get("/ping", response_class=PlainTextResponse)
async def ping(request: Request):
    client_ip = request.client.host
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO visits (ip) VALUES (%s)", (client_ip,))
    conn.commit()
    cur.close()
    conn.close()
    return "pong\n"

@app.get("/visits", response_class=PlainTextResponse)
async def get_visits():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM visits")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return f"Visits: {count}\n"
