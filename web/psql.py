import os
from dotenv import load_dotenv
from psycopg2 import connect, sql


load_dotenv()

def get_connection():
    return connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=int(os.getenv('DB_PORT'))
    )

def make_request(query, params=None, fetch=True):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if fetch:
                result = cur.fetchone()
                return result[0] if result else None
            else:
                conn.commit()
                return cur.rowcount
    except Exception as e:
        raise e
    finally:
        conn.close()

def init_db():
    query = """
        CREATE TABLE IF NOT EXISTS ips (
            id SERIAL PRIMARY KEY,
            ip VARCHAR(45) NOT NULL
        )
    """
    return make_request(query, fetch=False)

def add_ip_request(ip):
    query = "INSERT INTO ips (ip) VALUES (%s)"
    return make_request(query, (ip,), fetch=False)

def requests_count(table_name="ips"):
    query = sql.SQL("SELECT COUNT(*) FROM {}").format(
        sql.Identifier(table_name)
    )
    return make_request(query)


init_db()