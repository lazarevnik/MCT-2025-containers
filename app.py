from flask import Flask, request
import psycopg2
import os
import time

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_DATABASE = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')


def init_db():
    time.sleep(10)
    
    conn = psycopg2.connect(
        host = DB_HOST,
        database = DB_DATABASE,
        user = DB_USER,
        password = DB_PASSWORD
    )
    cur = conn.cursor()
    
    
    cur.execute(''' CREATE TABLE IF NOT EXISTS ping_requests ( ip_address VARCHAR(45) NOT NULL ) ''')
    
    conn.commit()
    cur.close()
    conn.close()



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



init_db()

if __name__ == '__main__':
    # Запускаем приложение на порту 5000
    app.run(host = '0.0.0.0', port = 5000)
