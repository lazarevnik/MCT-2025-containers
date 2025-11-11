from flask import Flask, request
import psycopg2
import os

app = Flask(__name__)

def get_db():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'db'),
        database=os.getenv('DB_NAME', 'app'),
        user=os.getenv('DB_USER', 'user'),
        password=os.getenv('DB_PASSWORD', 'user')
    )

@app.route('/')
def health():
    return "OK"

@app.route('/ping')
def ping():
    conn = get_db()
    cur = conn.cursor()
    ip = request.remote_addr
    cur.execute("""
        INSERT INTO visits (ip, count) VALUES (%s, 1)
        ON CONFLICT (ip) DO UPDATE SET count = visits.count + 1
    """, (ip,))
    conn.commit()
    cur.close()
    conn.close()
    return "pong"

@app.route('/visits')
def visits():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(count), 0) FROM visits")
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    return str(total)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
