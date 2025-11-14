from flask import Flask, request
from pg_config import get_pg_conn

app = Flask(__name__)


@app.route("/")
def home():
    return "easter egg"


@app.route("/ping")
def ping():
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute(
        'insert into visits (ip) values (%s)',
        (request.remote_addr,)
    )
    conn.commit()
    cur.close()
    conn.close()
    return "pong"


@app.route("/visits")
def visits():
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute('select count(1) as visit_count from visits')
    result = cur.fetchone()
    cur.close()
    conn.close()
    return str(result[0])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1337)