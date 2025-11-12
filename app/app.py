from flask import Flask, request
import psycopg2
import redis
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)

DEV_MODE = os.getenv('APP_ENV') == 'dev'

def get_db_connection():
    if DEV_MODE:
        return None
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'db'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'password')
    )

def get_redis_connection():
    if DEV_MODE:
        return None
    return redis.Redis(
        host=os.getenv('REDIS_HOST', 'redis'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        decode_responses=True
    )

def get_visits_count():
    if DEV_MODE:
        return -1
    
    try:
        r = get_redis_connection()
        cached_count = r.get('visits_count')
        
        if cached_count is not None:
            logger.info("Cache hit!")
            return int(cached_count)
    except Exception as e:
        logger.warning(f"Redis unavailable: {e}")
    
    logger.info("Cache miss :( Getting from database...")
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM visits')
            count = cur.fetchone()[0]
    
    update_visits_cache(count)
    return count

def update_visits_cache(count=-1):
    if DEV_MODE:
        return
    
    try:
        if count == -1:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('SELECT COUNT(*) FROM visits')
                    count = cur.fetchone()[0]
        
        r = get_redis_connection()
        r.set('visits_count', count, ex=300)
        logger.info("Cache updated")
    except Exception as e:
        logger.warning(f"Failed to update cache: {e}")

@app.route('/')
def index():
    return 'Hello! Use /ping and /visits endpoints.'

@app.route('/ping')
def ping():
    if DEV_MODE:
        return 'pong'
    
    ip = request.remote_addr    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('INSERT INTO visits (ip) VALUES (%s)', (ip,))    
    update_visits_cache()
    return 'pong'

@app.route('/visits')
def visits():
    count = get_visits_count()
    return str(count)

@app.route('/visits/db')
def visits_db():
    if DEV_MODE:
        return "Direct from DB: -1"
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM visits')
            count = cur.fetchone()[0]
    return f"Direct from DB: {count}"

@app.route('/visits/cache')
def visits_cache():
    if DEV_MODE:
        return "From cache: -1"
    
    try:
        r = get_redis_connection()
        cached_count = r.get('visits_count')
        if cached_count is not None:
            return f"From cache: {cached_count}"
        else:
            return "Cache is empty"
    except Exception as e:
        return f"Cache error: {e}"

@app.route('/cache/clear')
def clear_cache():
    if DEV_MODE:
        return "Cache cleared (dev mode)"
    
    try:
        r = get_redis_connection()
        r.delete('visits_count')
        return "Cache cleared"
    except Exception as e:
        return f"Error clearing cache: {e}"

if __name__ == '__main__':
    logger.info("Starting flask app")
    app.run(host='0.0.0.0', port=5000)