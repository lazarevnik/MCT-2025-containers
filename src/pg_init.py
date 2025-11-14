import sys
import psycopg2
from pg_config import get_pg_conn

MAX_RETRIES = 25

DELAY = 5

INIT_QUERY = """
create table if not exists visits (
            id serial primary key,
            ip inet not null,
            processed_timestamp timestamp default current_timestamp
)
"""

def pg_init():
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute(INIT_QUERY)
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    pg_init()

    for i in range(MAX_RETRIES):
        try:
            conn = get_pg_conn()
            conn.close()
            print("Database ready")
            sys.exit(0)
        except psycopg2.OperationalError as e:
            print(f"Waiting for database initialization ({i + 1}/{max_retries}) - {e}")
            time.sleep(DELAY)
    sys.exit(1)
    