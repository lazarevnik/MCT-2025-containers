from flask import Flask, request
import psycopg2
import os
import time
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)


def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'db'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'password')
    )
    return conn


@app.route('/ping')
def ping():
    ip = request.remote_addr
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO visits (ip) VALUES (%s)', (ip,))
    conn.commit()
    cur.close()
    conn.close()
    return 'pong'


@app.route('/visits')
def visits():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM visits')
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return str(count)


if __name__ == '__main__':
    logger.info("Starting flask app")
    app.run(host='0.0.0.0', port=5000)