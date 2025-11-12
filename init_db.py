import psycopg2
import os

DB_HOST = os.getenv('DB_HOST')
DB_DATABASE = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

conn = psycopg2.connect(
    host = DB_HOST,
    database = DB_DATABASE,
    user = DB_USER,
    password = DB_PASSWORD
)

cur = conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS ping_requests (ip_address VARCHAR(45) NOT NULL)')
conn.commit()
cur.close()
conn.close()