from fastapi import FastAPI, Request
import psycopg2
import os

app = FastAPI()

DB_HOST = os.getenv("DB_HOST", "db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1111")
DB_NAME = os.getenv("DB_NAME", "visitsdb")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME
    )



@app.get("/ping")
def ping(request: Request):
    client_ip = request.client.host
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO visits (ip) VALUES (%s);", (client_ip,))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "pong"}

@app.get("/visits")
def visits():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM visits;")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return {"visits": count}
