import psycopg2
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import redis
from os import getenv

app = FastAPI()

DB_HOST_NAME = getenv('DB_HOST_NAME', 'db')
DB_NAME = getenv('POSTGRES_DB', 'pings_db')
DB_USER_NAME = getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = getenv('POSTGRES_PASSWORD', '12345678')
DB_PORT = getenv('DB_PORT', '5432')
PINGS_TABLE_NAME = getenv('PINGS_TABLE_NAME', 'pings')

REDIS_HOST_NAME = getenv('REDIS_HOST_NAME', 'visits_cache')
REDIS_PORT = getenv('REDIS_PORT', '6379')

DEV_MODE = getenv('DEV_MODE', '0') # set to '1' to run in developer mode

@app.get('/', response_class=PlainTextResponse)
async def root():
    return ""

@app.get('/ping', response_class=PlainTextResponse) # curl localhost/ping
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
        try:
            with redis.Redis(host=REDIS_HOST_NAME, port=REDIS_PORT, decode_responses=True) as r:
                if r.get("visits") is not None: # else: init in visits(), not there
                    r.incr("visits", 1)
        except redis.RedisError as E:
            print(f'Redis exception on ping(): {E}')
        finally:
            try:
                if r:
                    r.close()
            except NameError:
                pass
    except BaseException as E:
        print(f'Exception on ping(): {E}')
    finally:
        try:
            if conn:
                conn.close()
        except NameError:
            pass
    return 'pong'

@app.get('/visits', response_class=PlainTextResponse)
async def visits():
    if DEV_MODE != '0':
        return str(-1)
    try:
        with redis.Redis(host=REDIS_HOST_NAME, port=REDIS_PORT, decode_responses=True) as r:
            if (cached_visits := r.get("visits")): # else: init in visits(), not there
                return cached_visits
    except redis.RedisError as E:
        print(f'Redis exception on visits(): {E}')
    finally:
        try:
            if r:
                r.close()
        except NameError:
            pass
    # fallthrough: no cached value
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
            value = str(int(cursor.fetchone()[0]))
            try:
                with redis.Redis(host=REDIS_HOST_NAME, port=REDIS_PORT, decode_responses=True) as r:
                    r.set('visits', value)
            except redis.RedisError as E:
                print(f'Redis exception on visits(): {E}')
            finally:
                try:
                    if r:
                        r.close()
                except NameError:
                    pass
            return value
    except BaseException as E:
        print(f'Exception on visits(): {E}')
    finally:
        try:
            if conn:
                conn.close()
        except NameError:
            pass
    return str(-2)