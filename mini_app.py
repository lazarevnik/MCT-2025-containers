from flask import Flask, request
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import time

app = Flask(__name__)

DB_CONFIG = {
    'dbname': os.getenv('POSTGRES_DB', 'app'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'password'),
    'host': os.getenv('POSTGRES_HOST', 'db'),
    'port': os.getenv('POSTGRES_PORT', '5432')
}

def init_db():
    max_retries = 5
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE IF NOT EXISTS requests (
                    id SERIAL PRIMARY KEY,
                    client_ip VARCHAR(45) NOT NULL,
                    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    endpoint VARCHAR(50) NOT NULL
                )
            ''')
            conn.commit()
            cur.close()
            conn.close()
            print("База данных успешно инициализирована")
            return
        except Exception as e:
            print(f"Попытка {i+1}/{max_retries}: Ошибка подключения к БД: {e}")
            if i < max_retries - 1:
                time.sleep(5)
            else:
                print("Не удалось подключиться к БД после всех попыток")

def log_request(client_ip, endpoint):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO requests (client_ip, endpoint) VALUES (%s, %s)',
            (client_ip, endpoint)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка при записи в БД: {e}")

def get_visits_count():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM requests WHERE endpoint = %s', ('ping',))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count
    except Exception as e:
        print(f"Ошибка при чтении из БД: {e}")
        return 0

init_db()

@app.route('/')
def home():
    return 'Welcome to and3rlex mini-app!'

@app.route('/ping')
def ping():
    client_ip = request.remote_addr
    print(f"Ping request from IP: {client_ip}")
    log_request(client_ip, 'ping')
    return 'pong'

@app.route('/visits')
def visits():
    count = get_visits_count()
    return str(count)

@app.route('/requests')
def all_requests():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM requests ORDER BY request_time DESC LIMIT 100')
        requests = cur.fetchall()
        cur.close()
        conn.close()
        result = []
        for req in requests:
            result.append(dict(req))
        return {'requests': result}
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
