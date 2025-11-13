from flask import Flask
import psycopg
from config import*


app = Flask(__name__)
dbconn = psycopg.Connection.connect(
        f"""host={DATABASE_HOST}
            port={DATABASE_PORT}
            dbname={DATABASE_NAME}
            user={DATABASE_USER}
            password={DATABASE_PASSWORD}"""
)
cur = dbconn.cursor()


@app.route("/ping")
def ping():
    cur.execute(f"INSERT INTO {TABLE_NAME}(data) VALUES ('');")
    dbconn.commit()
    return "pong"


@app.route("/visits")
def visits():
    query_res = cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME};").fetchone()
    visit_cnt = query_res[0]
    return str(visit_cnt)


def close_db_connection():
    dbconn.close()


if __name__ == "__main__":
    app.teardown_appcontext(close_db_connection)
