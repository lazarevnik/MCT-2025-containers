import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app.main as app_module
from app.main import CACHE_KEY, app, get_visits, lifespan, ping


class DummyConnection:
    def __init__(self):
        self.counter = 0
        self.fetch_calls = 0

    async def execute(self, query: str):
        assert "visits" in query
        self.counter += 1

    async def fetchval(self, query: str):
        assert "SELECT COUNT" in query
        self.fetch_calls += 1
        return self.counter


class DummyAcquire:
    def __init__(self, connection: DummyConnection):
        self.connection = connection

    async def __aenter__(self):
        return self.connection

    async def __aexit__(self, exc_type, exc, tb):
        return False


class DummyPool:
    def __init__(self):
        self.connection = DummyConnection()

    def acquire(self):
        return DummyAcquire(self.connection)


class DummyRedis:
    def __init__(self):
        self.storage = {}
        self.set_calls = 0
        self.get_calls = 0

    async def set(self, key: str, value: str):
        self.set_calls += 1
        self.storage[key] = value

    async def get(self, key: str):
        self.get_calls += 1
        return self.storage.get(key)


def _prepare_state(dev_mode: bool = False):
    app.state.is_dev_mode = dev_mode
    if dev_mode:
        app.state.db_pool = None
        app.state.redis = None
    else:
        app.state.db_pool = DummyPool()
        app.state.redis = DummyRedis()


@pytest.mark.asyncio
async def test_ping_records_visit_and_updates_cache():
    _prepare_state(dev_mode=False)

    response = await ping()

    assert response.body == b"pong"
    assert app.state.db_pool.connection.counter == 1
    assert app.state.redis.storage[CACHE_KEY] == "1"


@pytest.mark.asyncio
async def test_get_visits_returns_cached_value_without_db_hits():
    _prepare_state(dev_mode=False)
    app.state.redis.storage[CACHE_KEY] = "7"

    visits = await get_visits()

    assert visits == 7
    assert app.state.db_pool.connection.fetch_calls == 0


@pytest.mark.asyncio
async def test_dev_mode_visits_returns_placeholder(monkeypatch):
    _prepare_state(dev_mode=True)

    visits = await get_visits()
    response = await ping()

    assert visits == -1
    assert response.body == b"pong"


@pytest.mark.asyncio
async def test_get_visits_reads_from_db_when_cache_is_empty():
    _prepare_state(dev_mode=False)
    app.state.db_pool.connection.counter = 5

    visits = await get_visits()

    assert visits == 5
    assert app.state.redis.storage[CACHE_KEY] == "5"
    assert app.state.db_pool.connection.fetch_calls == 1


@pytest.mark.asyncio
async def test_lifespan_initializes_dependencies_in_prod(monkeypatch):
    fake_pool_closed = {"value": False}
    fake_redis_closed = {"value": False}

    class FakePool:
        async def close(self):
            fake_pool_closed["value"] = True

    class FakeRedis:
        async def aclose(self):
            fake_redis_closed["value"] = True

    async def fake_create_pool(dsn):
        assert dsn == "postgresql://test"
        return FakePool()

    def fake_from_url(url, **kwargs):
        assert url == "redis://test"
        return FakeRedis()

    monkeypatch.setattr(app_module, "DATABASE_URL", "postgresql://test")
    monkeypatch.setattr(app_module, "REDIS_URL", "redis://test")
    monkeypatch.setattr(app_module, "is_dev_mode", lambda: False)
    monkeypatch.setattr(app_module.asyncpg, "create_pool", fake_create_pool)
    monkeypatch.setattr(app_module.redis, "from_url", fake_from_url)

    async with lifespan(app):
        assert app.state.db_pool is not None
        assert app.state.redis is not None

    assert fake_pool_closed["value"] is True
    assert fake_redis_closed["value"] is True


@pytest.mark.asyncio
async def test_lifespan_raises_when_database_url_missing(monkeypatch):
    monkeypatch.setattr(app_module, "DATABASE_URL", None)
    monkeypatch.setattr(app_module, "REDIS_URL", "redis://test")
    monkeypatch.setattr(app_module, "is_dev_mode", lambda: False)

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        async with lifespan(app):
            pass

