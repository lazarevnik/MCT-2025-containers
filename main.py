from fastapi import FastAPI, Request, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
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

def init_db():
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS visits (
                    id SERIAL PRIMARY KEY,
                    ip VARCHAR(45) NOT NULL,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            cur.close()
            conn.close()
            print("Database initialized successfully")
            return
        except Exception as e:
            print(f"Database connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"🔄 Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("All database connection attempts failed")
                raise

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
async def root():
    return {"message": "Welcome to the web server with PostgreSQL"}

@app.get("/ping")
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
