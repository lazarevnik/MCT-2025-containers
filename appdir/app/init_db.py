import psycopg2
from os import getenv
from time import sleep

DB_HOST_NAME = getenv('DB_HOST_NAME', 'db')
DB_NAME = getenv('POSTGRES_DB', 'pings_db')
DB_USER_NAME = getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = getenv('POSTGRES_PASSWORD', '12345678')
DB_PORT = getenv('DB_PORT', '5432')
PINGS_TABLE_NAME = getenv('PINGS_TABLE_NAME', 'pings')

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
        cursor.execute(f'CREATE TABLE IF NOT EXISTS {PINGS_TABLE_NAME} ( id serial PRIMARY KEY, ip VARCHAR(15) );')
except BaseException as E:
    with open('log.txt', 'a') as f:
        print(f'[{__file__}] Exception: {E}')
        print(f'[{__file__}] Exception: {E}', file=f)
    exit(1)
finally:
    try:
        if conn:
            conn.close()
    except NameError:
        pass
exit(0)