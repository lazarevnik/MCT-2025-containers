from flask import Flask, request
import psycopg2
import time

app = Flask(__name__)
time.sleep(15)
def dataBase():
    conn = psycopg2.connect(
        host='db',
        database='postgres',
        user='postgres',
        password='123'
    )
    return conn
    
@app.before_first_request
def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id SERIAL PRIMARY KEY,
            ip VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/ping')
def ping():
    ip = request.remote_addr
    conn = dataBase()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO visits (ip) VALUES (%s)", (ip,))
    conn.commit()
    cursor.close()
    conn.close()
    return "pong\n"

@app.route('/visits')
def visits():
    conn = dataBase()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM visits")
    t = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return str(t) + '\n'
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
