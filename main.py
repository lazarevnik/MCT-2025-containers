import os
import psycopg2
import redis
from flask import Flask, request

app = Flask(__name__)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'database': os.getenv('DB_NAME', 'visits_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'port': os.getenv('DB_PORT', '5432')
}

REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'redis'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': int(os.getenv('REDIS_DB', 0)),
    'decode_responses': True
}

VISITS_COUNT_KEY = 'visits_count'

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_redis_connection():
    return redis.Redis(**REDIS_CONFIG)

def get_visits_count_from_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM visits')
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count

def update_cache():
    r = get_redis_connection()
    count = get_visits_count_from_db()
    r.setex(VISITS_COUNT_KEY, 60, count)
    return count

def get_visits_count():
    r = get_redis_connection()
    cached_count = r.get(VISITS_COUNT_KEY)
    if cached_count is not None:
        return int(cached_count)
    return update_cache()

@app.route('/')
def home():
    return 'OK', 200

@app.route('/ping')
def ping():
    client_ip = request.remote_addr
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO visits (ip_address) VALUES (%s)', (client_ip,))
    conn.commit()
    cur.close()
    conn.close()
    
    r = get_redis_connection()
    r.delete(VISITS_COUNT_KEY)
    
    return 'pong'

@app.route('/visits')
def visits():
    count = get_visits_count()
    return str(count)

@app.route('/visits/db')
def visits_db():
    count = get_visits_count_from_db()
    return str(count)

@app.route('/cache/update')
def cache_update():
    count = update_cache()
    return f'Cache updated: {count}', 200

@app.route('/health')
def health():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT 1')
    cur.close()
    conn.close()
    
    r = get_redis_connection()
    r.ping()
    
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
