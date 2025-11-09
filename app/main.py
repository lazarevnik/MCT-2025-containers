import os
from datetime import datetime

from flask import Flask, request, url_for
from pymemcache.client.base import Client as MemcacheClient
from pymemcache.exceptions import MemcacheError
from sqlalchemy import DateTime, Integer, String, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

MEMCACHED_HOST = "cache"
MEMCACHED_PORT = "11211"

CACHE_KEY = "pings_total"
CACHE_VALID_KEY = "pings_total:valid"

def _database_url() -> str:
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url
    return "postgresql+psycopg2://user:password@db:5432/app"


class Base(DeclarativeBase):
    pass


class Ping(Base):
    __tablename__ = "pings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


engine = create_engine(_database_url(), pool_pre_ping=True)
Base.metadata.create_all(bind=engine)

cache_client = MemcacheClient((MEMCACHED_HOST, MEMCACHED_PORT), connect_timeout=1, timeout=1, no_delay=True)

class CacheManager:
    def __init__(self, client: MemcacheClient, total_key: str, valid_key: str):
        self.client = client
        self.total_key = total_key
        self.valid_key = valid_key

    def _decode(self, value):
        if value is None:
            return None
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="ignore")
        return value

    def get_total(self) -> int | None:
        try:
            value = self.client.get(self.total_key)
        except MemcacheError:
            return None
        value = self._decode(value)
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def set_total(self, value: int) -> None:
        try:
            self.client.set(self.total_key, str(value))
            self.client.set(self.valid_key, "1")
        except MemcacheError:
            pass

    def invalidate(self) -> None:
        try:
            self.client.delete(self.valid_key)
        except MemcacheError:
            pass

    def is_valid(self) -> bool:
        try:
            value = self.client.get(self.valid_key)
        except MemcacheError:
            return False
        value = self._decode(value)
        if value is None:
            return False
        return value == "1"


cache_manager = CacheManager(cache_client, CACHE_KEY, CACHE_VALID_KEY)

app = Flask(__name__)
DEV_MODE = os.environ.get("DEV_MODE", "").lower() == "true"


def get_client_ip() -> str:
    return request.remote_addr or "0.0.0.0"


@app.route("/")
def index() -> tuple[str, int, dict[str, str]]:
    ping_url = url_for("ping")
    visits_url = url_for("visits")
    html = f"""
    <html>
        <head><title>DevOps Tour</title></head>
        <body>
            <h1> Доступные ссылки </h1>
            <ul>
                <li><a href="{ping_url}">{ping_url}</a> - вернёт pong </li>
                <li><a href="{visits_url}">{visits_url}</a> - показывает количество ping-запросов </li>
            </ul>
        </body>
    </html>
    """
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/ping")
def ping() -> tuple[str, int]:
    client_ip = get_client_ip()
    with Session(engine) as session:
        session.add(Ping(ip_address=client_ip))
        session.commit()
    cache_manager.invalidate()
    return "pong", 200


@app.route("/visits")
def visits() -> tuple[str, int]:
    if DEV_MODE:
        return "-1", 200
    if cache_manager.is_valid():
        cached = cache_manager.get_total()
        if cached is not None:
            return str(cached), 200
    with Session(engine) as session:
        total = session.query(Ping).count()
    cache_manager.set_total(total)
    return str(total), 200


if __name__ == "__main__":  # pragma: no cover
    app.run(host="0.0.0.0", port=5000)
