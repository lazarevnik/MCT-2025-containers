from flask import Flask, request
import psycopg2

app = Flask(__name__)
def dataBase():
    conn = psycopg2.connect(
        host='db',
        database='app',
        user='user',
        password='123'
    )
    return conn

@app.route('/ping')
def ping():
    try:
        ip = request.remote_addr
        conn = dataBase()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO visits (ip) VALUES (%s)", (ip,))
        conn.commit()
        cursor.close()
        conn.close()
        return "pong\n"
    except Exception as e:
        conn = dataBase()
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS visits (id SERIAL PRIMARY KEY, ip VARCHAR(50))")
        conn.commit()
        cursor.close()
        conn.close()
        return ping()

@app.route('/visits')
def visits():
    conn = dataBase()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM visits")
    t = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return str(t) + '\n'
