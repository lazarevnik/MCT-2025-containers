from flask import Flask, request
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import time
import redis
import json

app = Flask(__name__)

DB_CONFIG = {
    'dbname': os.getenv('POSTGRES_DB', 'app'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'password'),
    'host': os.getenv('POSTGRES_HOST', 'db'),
    'port': os.getenv('POSTGRES_PORT', '5432')
}

REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'redis'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': 0,
    'decode_responses': True
}

redis_client = redis.Redis(**REDIS_CONFIG)

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

        redis_client.delete('visits_count')
    except Exception as e:
        print(f"Ошибка при записи в БД: {e}")

def get_visits_count():
    cached_count = redis_client.get('visits_count')
    if cached_count:
        print("Получено из кэша")
        return int(cached_count)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM requests WHERE endpoint = %s', ('ping',))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        
        redis_client.setex('visits_count', 30, count)
        print("Получено из БД и сохранено в кэш")
        return count
    except Exception as e:
        print(f"Ошибка при чтении из БД: {e}")
        return 0

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

@app.route('/cache/clear')
def clear_cache():
    redis_client.flushdb()
    return 'Cache cleared'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
