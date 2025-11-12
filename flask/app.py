import os
from flask import Flask, request
import psycopg2

app = Flask(__name__)

password = "mysecretpassword"
test_env = os.getenv("TEST_ENV", "False")

@app.route('/')
def start():
    return 'use /ping or /visits'

@app.route('/ping')
def ping():
    if test_env == 'True':
        return 'pong'

    db_host = os.environ.get('DB_HOST')
    conn = psycopg2.connect(database="ping_db",
                            user="postgres",
                            password=password,
                            host=db_host, port="5432")
    cur = conn.cursor()

    cur.execute(
        f'''INSERT INTO ips (client_ip, call_count) \
        VALUES ('{request.remote_addr}', 1) \
        ON CONFLICT (client_ip) \
        DO UPDATE SET call_count = ips.call_count + 1;''')

    conn.commit()

    cur.close()
    conn.close()

    return 'pong'

@app.route('/visits')
def visits():
    if test_env == 'True':
        return '-1'

    db_host = os.environ.get('DB_HOST')
    conn = psycopg2.connect(database="ping_db",
                            user="postgres",
                            password=password,
                            host=db_host, port="5432")
    cur = conn.cursor()

    client_ip = request.remote_addr

    cur.execute(
        f'''SELECT COALESCE( \
            (SELECT call_count FROM ips WHERE client_ip = '{client_ip}'), \
            0 \
        ) AS call_count;''')
    
    count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return str(count)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)