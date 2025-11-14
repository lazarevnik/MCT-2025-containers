import os
from flask import Flask, request
import psycopg

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'dbname': os.getenv('DB_NAME', 'app'),
    'user': os.getenv('DB_USER', 'user'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'port': os.getenv('DB_PORT', 5432)
}

app = Flask(__name__)

ping_count = 0


@app.route('/')
def index():
    return {
        'endpoints': {
            '/ping': 'Return "pong" and logs your request',
            '/visits': 'Return number of ping call count',
        },
    }


@app.route('/ping')
def ping():
    global ping_count
    ping_count += 1

    client_ip = request.remote_addr
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO ping_requests (ip_address) VALUES (%s)',
                (client_ip,)
            )
        conn.commit()

    return 'pong'


@app.route('/visits')
def visits():
    return f'{ping_count}'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
