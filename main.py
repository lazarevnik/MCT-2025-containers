import os
import psycopg2
from flask import Flask

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'db')
DB_NAME = os.getenv('DB_NAME', 'visits_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

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
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")

@app.route('/ping')
def ping():
    from flask import request
    client_ip = request.remote_addr
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO visits (ip_address) VALUES (%s)', (client_ip,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error saving visit: {e}")
    
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
        return str(count)
    except Exception as e:
        print(f"Error getting visits count: {e}")
        return '0'

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
