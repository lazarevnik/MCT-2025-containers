import psycopg2
from fastapi import FastAPI, Request
from os import getenv

app = FastAPI()

DB_HOST_NAME = getenv('DB_HOST_NAME', 'db')
DB_NAME = getenv('DB_NAME', 'pings_db')
DB_USER_NAME = getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = getenv('POSTGRES_PASSWORD', '12345678')
DB_PORT = getenv('DB_PORT', '5432')
PINGS_TABLE_NAME = getenv('PINGS_TABLE_NAME', 'pings')

@app.get('/ping') # curl localhost/ping
async def ping(request: Request):
    client_ip = request.client.host
    try:
        conn = psycopg2.connect(
            host=DB_HOST_NAME,
            database=DB_NAME,
            user=DB_USER_NAME,
            password=DB_PASSWORD,
            port=DB_PORT,
        )
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(f'INSERT INTO {PINGS_TABLE_NAME} (id, ip) VALUES (DEFAULT, \'{client_ip}\');')
    except BaseException as E:
        with open('log.txt', 'a') as f:
            print(f'Exception on ping(): {E}', file=f)
    finally:
        try:
            if conn:
                conn.close()
        except NameError:
            pass
    return 'pong'

@app.get('/visits')
async def visits():
    try:
        conn = psycopg2.connect(
            host=DB_HOST_NAME,
            database=DB_NAME,
            user=DB_USER_NAME,
            password=DB_PASSWORD,
            port=DB_PORT,
        )
        with conn.cursor() as cursor:
            cursor.execute(f'SELECT COUNT(*) FROM {PINGS_TABLE_NAME};')
            return int(cursor.fetchone()[0])
    except BaseException as E:
        with open('log.txt', 'a') as f:
            print(f'Exception on visits(): {E}', file=f)
    finally:
        try:
            if conn:
                conn.close()
        except NameError:
            pass
    return -1