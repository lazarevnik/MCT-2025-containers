import os
import time
import psycopg2
import redis
from flask import Flask, request
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'database': os.getenv('DB_NAME', 'visits_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'port': os.getenv('DB_PORT', '5432')
}

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

VISITS_COUNT_KEY = 'visits_count'
CACHE_TTL = 60

def get_redis_connection():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=5,
        retry_on_timeout=True
    )

def wait_for_redis(max_retries=30, delay=2):
    for i in range(max_retries):
        try:
            r = get_redis_connection()
            r.ping()
            logger.info("Redis is ready!")
            return True
        except Exception as e:
            logger.warning(f"Redis not ready (attempt {i+1}/{max_retries}): {e}")
            time.sleep(delay)
    logger.error("Redis connection failed after all retries")
    return False

def wait_for_db(max_retries=30, delay=2):
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            conn.close()
            logger.info("Database is ready!")
            return True
        except Exception as e:
            logger.warning(f"Database not ready (attempt {i+1}/{max_retries}): {e}")
            time.sleep(delay)
    logger.error("Database connection failed after all retries")
    return False

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_visits_count_from_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM visits')
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count
    except Exception as e:
        logger.error(f"Error getting visits count from DB: {e}")
        raise

def update_cache():
    try:
        r = get_redis_connection()
        count = get_visits_count_from_db()
        r.setex(VISITS_COUNT_KEY, CACHE_TTL, count)
        logger.info(f"Cache updated with count: {count}")
        return count
    except Exception as e:
        logger.error(f"Error updating cache: {e}")
        raise

def get_visits_count():
    try:
        r = get_redis_connection()
        
        cached_count = r.get(VISITS_COUNT_KEY)
        if cached_count is not None:
            logger.info(f"Cache hit: {cached_count}")
            return int(cached_count)
        
        logger.info("Cache miss, fetching from DB")
        return update_cache()
        
    except Exception as e:
        logger.error(f"Error getting visits count from cache: {e}")
        return get_visits_count_from_db()

@app.route('/')
def home():
    return 'OK', 200

@app.route('/ping')
def ping():
    client_ip = request.remote_addr
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO visits (ip_address) VALUES (%s)', (client_ip,))
        conn.commit()
        cur.close()
        conn.close()
        
        r = get_redis_connection()
        r.delete(VISITS_COUNT_KEY)
        logger.info("Cache invalidated after new visit")
        
        logger.info(f"Saved visit from IP: {client_ip}")
    except Exception as e:
        logger.error(f"Error saving visit: {e}")
        return 'Database error', 500
    
    return 'pong'

@app.route('/visits')
def visits():
    try:
        count = get_visits_count()
        logger.info(f"Visits count: {count}")
        return str(count)
    except Exception as e:
        logger.error(f"Error getting visits count: {e}")
        return '0'

@app.route('/visits/db')
def visits_db():
    try:
        count = get_visits_count_from_db()
        logger.info(f"Visits count from DB: {count}")
        return str(count)
    except Exception as e:
        logger.error(f"Error getting visits count from DB: {e}")
        return '0'

@app.route('/cache/update')
def cache_update():
    try:
        count = update_cache()
        return f'Cache updated with count: {count}', 200
    except Exception as e:
        logger.error(f"Error updating cache: {e}")
        return 'Cache update failed', 500

@app.route('/cache/clear')
def cache_clear():
    try:
        r = get_redis_connection()
        r.delete(VISITS_COUNT_KEY)
        logger.info("Cache cleared")
        return 'Cache cleared', 200
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return 'Cache clear failed', 500

@app.route('/health')
def health():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        
        r = get_redis_connection()
        r.ping()
        
        return 'OK', 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return 'Service connection failed', 500

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    
    if not wait_for_db():
        logger.error("Failed to connect to database. Exiting.")
        exit(1)
    
    if not wait_for_redis():
        logger.error("Failed to connect to redis. Exiting.")
        exit(1)
    
    try:
        update_cache()
        logger.info("Cache initialized on startup")
    except Exception as e:
        logger.error(f"Failed to initialize cache: {e}")
    
    logger.info("Starting Flask server on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
