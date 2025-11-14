from fastapi import FastAPI, Request, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi.responses import PlainTextResponse
import os
import time

app = FastAPI()

# Параметры подключения к БД из переменных окружения
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "app_db")
DB_USER = os.getenv("POSTGRES_USER", "app_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "app_password")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        cursor_factory=RealDictCursor
    )

@app.get("/")
async def root():
    return {"message": "Welcome to the web server with PostgreSQL"}

@app.get("/ping", response_class=PlainTextResponse)
async def ping(request: Request):
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO visits (ip, user_agent) VALUES (%s, %s)",
            (client_ip, user_agent)
        )
        conn.commit()
        cur.close()
        conn.close()
        return "pong"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/visits")
async def get_visits():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as count FROM visits")
        result = cur.fetchone()
        count = result["count"] if result else 0
        cur.close()
        conn.close()
        return {"total_visits": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
