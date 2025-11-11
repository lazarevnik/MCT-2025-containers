from fastapi import FastAPI, Request
import psycopg2
import os

app = FastAPI()

def database_connection():
    return psycopg2.connect(host=os.getenv("POSTGRES_HOST"),
                            database=os.getenv("POSTGRES_DB"),
                            user=os.getenv("POSTGRES_USER"),
                            password=os.getenv("POSTGRES_PASSWORD"),
                            port=os.getenv("POSTGRES_PORT"))

@app.get("/ping")
async def pong(request: Request):
    conn = database_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO visits (ip_address) VALUES (%(ip)s);", {"ip": request.client.host})
    conn.commit()
    cursor.close()
    conn.close()
    return 'pong'

@app.get("/visits")
async def visits():
    conn = database_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM visits;")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count

@app.get("/")
async def visits():
    return "GG WP"