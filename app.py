from flask import Flask, request
import psycopg2
import os

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_DATABASE = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

@app.route('/')
def root():
    return "/ping or /visits"


@app.route('/ping') 
def ping():

    client_ip = request.remote_addr
    
    conn = psycopg2.connect(
        host = os.getenv('DB_HOST'),
        database = os.getenv('DB_NAME'),
        user = os.getenv('DB_USER'),
        password = os.getenv('DB_PASSWORD')
    )
    cur = conn.cursor()
    cur.execute('INSERT INTO ping_requests (ip_address) VALUES (%s)', (client_ip,))
    conn.commit()
    cur.close()
    conn.close()
    
    return 'pong'


@app.route('/visits')
def visits():

    if os.getenv('APP_MODE') == 'dev':
        return '-1'

    conn = psycopg2.connect(
        host = os.getenv('DB_HOST'),
        database = os.getenv('DB_NAME'),
        user = os.getenv('DB_USER'),
        password = os.getenv('DB_PASSWORD')
    )
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) FROM ping_requests')
    cnt = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    return str(cnt)

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000)
