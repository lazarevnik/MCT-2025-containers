import os
import redis
from flask import Flask, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from init_db import Visit

DB_USER = os.getenv("POSTGRES_USER", "user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "apppw")
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "app")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

redis_client = redis.Redis(host=REDIS_HOST, port=int(REDIS_PORT), decode_responses=True)

app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    session = SessionLocal()
    total_visits = session.query(Visit).count()
    unique_ips = session.query(Visit.ip_address).distinct().count()
    session.close()

    return f"""
        <html>
        <body>
            <h3>Visitor Tracker</h3>
            <p>Всего посещений: {total_visits}</p>
            <p>Уникальных посетителей: {unique_ips}</p>
        </body>
        </html>
        """


@app.route("/ping", methods=["GET"])
def ping():
    ip = request.remote_addr
    session = SessionLocal()
    visit = Visit(ip_address=ip)
    session.add(visit)
    session.commit()
    session.close()

    redis_client.delete("visits_count")
    return "pong"


@app.route("/visits", methods=["GET"])
def visits():
    if DEV_MODE:
        return "-1"

    cached_count = redis_client.get("visits_count")

    if cached_count is not None:
        return str(cached_count)

    session = SessionLocal()
    count = session.query(Visit).count()
    session.close()

    redis_client.set("visits_count", count)

    return str(count)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
