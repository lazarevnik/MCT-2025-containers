import psycopg2
import os
import sys
import time

DB_CONFIG = {
    'dbname': os.getenv('POSTGRES_DB', 'app'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'password'),
    'host': os.getenv('POSTGRES_HOST', 'db'),
    'port': os.getenv('POSTGRES_PORT', '5432')
}

def init_database():
    max_retries = 10
    for i in range(max_retries):
        try:
            print(f"Attempt {i+1}/{max_retries} to connect to database...")
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            
            cur.execute('''
                CREATE TABLE IF NOT EXISTS requests (
                    id SERIAL PRIMARY KEY,
                    client_ip VARCHAR(45) NOT NULL,
                    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    endpoint VARCHAR(50) NOT NULL
                )
            ''')
            
            cur.execute('CREATE INDEX IF NOT EXISTS idx_requests_endpoint ON requests(endpoint)')
            
            conn.commit()
            cur.close()
            conn.close()
            
            print("Database initialized successfully!")
            return True
            
        except Exception as e:
            print(f"Database connection failed: {e}")
            if i < max_retries - 1:
                time.sleep(3)
            else:
                print("Failed to initialize database after all retries")
                return False

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)