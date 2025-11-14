from flask import Flask, request
import os
import psycopg2

app = Flask(__name__)

params = {
    'host': os.getenv('HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('USER'),
    'password': os.getenv('PASSWORD')
}

@app.route('/ping')
def ping():
    connect = psycopg2.connect(**params)
    cursor = connect.cursor()
    cursor.execute('INSERT INTO visits (ip_addr) VALUES (%s)', (request.remote_addr,))
    connect.commit()
    
    cursor.close()
    connect.close()
    
    answer = "pong\n"
    return answer

@app.route('/visits')
def visits():
    connect = psycopg2.connect(**params)
    cursor = connect.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM visits')
    res = cursor.fetchone()
    
    cursor.close()
    connect.close()
    
    if res:
        answer = str(res[0]) + "\n"
    else:
        answer = "0\n"
    return answer

if __name__ == '__main__':
    connect = psycopg2.connect(**params)
    cursor = connect.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visits (
            id SERIAL PRIMARY KEY,
            ip_addr VARCHAR(45)
        )
    ''')
    connect.commit()
    
    cursor.close()
    connect.close()
    
    app.run(host='0.0.0.0', port=5000)