import psycopg2
import os

def init_db():

    DB_NAME = os.getenv("DB_NAME", "request_db")
    DB_USER = os.getenv("DB_USER", "user_db")
    DB_PASWD = os.getenv("DB_PASWD", "passwd")
    DB_PORT = int(os.getenv("DB_PORT", 5432))

    conn = psycopg2.connect(
        host = "db",
        dbname = DB_NAME, 
        user = DB_USER, 
        password = DB_PASWD, 
        port = DB_PORT
    )

    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id SERIAL PRIMARY KEY,
            request_src VARCHAR(400)
        );
    """)

    conn.commit()
    conn.close()
    print("Database initialized")




if __name__ == "__main__":
    init_db()