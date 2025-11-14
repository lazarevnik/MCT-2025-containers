import os
import time
import psycopg2

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "app")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")


def main():
    conn = None
    for _ in range(30):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
            )
            break
        except psycopg2.OperationalError:
            time.sleep(1)
    if conn is None:
        raise SystemExit(1)

    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS visits (id SERIAL PRIMARY KEY, ip VARCHAR(64) NOT NULL)"
    )
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
