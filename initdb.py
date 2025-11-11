import os
import psycopg2

def init_db():
    conn = psycopg2.connect(host = os.getenv("POSTGRES_HOST"),
                            database = os.getenv("POSTGRES_DB"),
                            user = os.getenv("POSTGRES_USER"),
                            password = os.getenv("POSTGRES_PASSWORD"),
                            port = os.getenv("POSTGRES_PORT"))

    cursor = conn.cursor()
    cursor.execute("""
                CREATE TABLE IF NOT EXISTS visits (
                    id SERIAL PRIMARY KEY,
                    ip_address VARCHAR(45) NOT NULL
                )
            """)
    conn.commit()

    cursor.close()
    conn.close()

if __name__ == "__main__":
    init_db()
