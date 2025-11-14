import psycopg2
import os
import sys
import time

SUPER_USER = os.getenv("DB_SUPER_USER", "postgres")
SUPER_PASSWORD = os.getenv("DB_SUPER_PASSWORD", "1111")
DB_HOST = os.getenv("DB_HOST", "db")
TARGET_DB = os.getenv("DB_NAME", "visitsdb")
TARGET_USER = os.getenv("DB_USER", "user")
TARGET_PASSWORD = os.getenv("DB_PASSWORD", "1111")

def wait_for_postgres():
    """Ждём, пока основной PostgreSQL примет подключение"""
    for _ in range(60):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                user=SUPER_USER,
                password=SUPER_PASSWORD,
                dbname="postgres"
            )
            conn.close()
            return
        except psycopg2.OperationalError:
            time.sleep(1)
    raise Exception("PostgreSQL not ready after 60 seconds")

def create_user_and_db():
    conn = psycopg2.connect(
        host=DB_HOST,
        user=SUPER_USER,
        password=SUPER_PASSWORD,
        dbname="postgres"
    )
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s;", (TARGET_USER,))
    user_exists = cur.fetchone() is not None
    if not user_exists:
        cur.execute(f"CREATE USER {TARGET_USER} WITH ENCRYPTED PASSWORD %s;", (TARGET_PASSWORD,))
        print(f"User '{TARGET_USER}' created.")
    else:
        print(f"User '{TARGET_USER}' already exists.")

    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (TARGET_DB,))
    db_exists = cur.fetchone() is not None
    if not db_exists:
        cur.execute(f"CREATE DATABASE {TARGET_DB} OWNER {TARGET_USER};")
        print(f"Database '{TARGET_DB}' created.")
    else:
        print(f"Database '{TARGET_DB}' already exists.")

    cur.close()
    conn.close()

def create_table():
    for _ in range(30):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                user=TARGET_USER,
                password=TARGET_PASSWORD,
                dbname=TARGET_DB
            )
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS visits (
                    id SERIAL PRIMARY KEY,
                    ip TEXT NOT NULL
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
            print("Table 'visits' created.")
            return
        except psycopg2.OperationalError as e:
            if "does not exist" in str(e):
                time.sleep(2)
            else:
                raise
    raise Exception("Could not connect to target DB after creation")
def grant_privileges():
    conn = psycopg2.connect(
        host=DB_HOST,
        user=SUPER_USER,
        password=SUPER_PASSWORD,
        dbname=TARGET_DB
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"GRANT ALL PRIVILEGES ON SCHEMA public TO {TARGET_USER};")
    cur.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {TARGET_USER};")
    cur.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {TARGET_USER};")
    print(f"Granted privileges on schema public to '{TARGET_USER}'.")
    cur.close()
    conn.close()
def main():
    wait_for_postgres()
    create_user_and_db()
    grant_privileges()
    create_table()
    print("Database initialization completed.")

if __name__ == "__main__":
    main()
