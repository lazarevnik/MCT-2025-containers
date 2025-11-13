import os
import time
import psycopg2
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

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS visits (
                id SERIAL PRIMARY KEY,
                ip_address VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Database table created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

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
        logger.info(f"Saved visit from IP: {client_ip}")
    except Exception as e:
        logger.error(f"Error saving visit: {e}")
        return 'Database error', 500
    
    return 'pong'

@app.route('/visits')
def visits():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM visits')
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        logger.info(f"Visits count: {count}")
        return str(count)
    except Exception as e:
        logger.error(f"Error getting visits count: {e}")
        return '0'

@app.route('/health')
def health():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        return 'OK', 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return 'Database connection failed', 500

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    
    if not wait_for_db():
        logger.error("Failed to connect to database. Exiting.")
        exit(1)
    
    init_db()
    
    logger.info("Starting Flask server on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
