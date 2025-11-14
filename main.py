from flask import Flask, request
import psycopg2

app = Flask(__name__)

def dataBase():
    conn = psycopg2.connect(
        host='db'
        database='postgres'
        user='user'
        password='<123>'
    )
    return conn
    
    
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
