import importlib
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def app_module(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    sys.modules.pop("app.main", None)
    module = importlib.import_module("app.main")
    mock_cache = MockMemcache()
    module.cache_manager = module.CacheManager(mock_cache, "test_pings_total", "test_pings_total_valid")
    module.Base.metadata.create_all(bind=module.engine)
    with module.Session(module.engine) as session:
        session.query(module.Ping).delete()
        session.commit()
    return module

@pytest.fixture
def client(app_module):
    return app_module.app.test_client()

def test_ping_stores_ip_and_returns_pong(app_module, client):
    response = client.get("/ping", environ_base={"REMOTE_ADDR": "1.2.3.4"})
    assert response.status_code == 200
    assert response.data.decode() == "pong"
    with app_module.Session(app_module.engine) as session:
        ping = session.query(app_module.Ping).one()
        assert ping.ip_address == "1.2.3.4"


def test_visits_counts_and_uses_cache(app_module, client):
    assert client.get("/visits").data.decode() == "0"
    client.get("/ping")
    client.get("/ping")
    assert client.get("/visits").data.decode() == "2"

    manager = app_module.cache_manager
    manager.client.set(manager.total_key, 10)
    manager.client.set(manager.valid_key, "1")
    assert client.get("/visits").data.decode() == "10"
    client.get("/ping")
    assert client.get("/visits").data.decode() == "3"


def test_visits_invalid_cached_value_falls_back_to_db(app_module, client):
    client.get("/ping")
    assert client.get("/visits").data.decode() == "1"
    manager = app_module.cache_manager
    manager.client.set(manager.total_key, "not-a-number")
    manager.client.set(manager.valid_key, "1")
    assert client.get("/visits").data.decode() == "1"
    assert manager.client.get(manager.total_key) == "1"


def test_ping_invalidate_cache_flag(app_module, client):
    manager = app_module.cache_manager
    client.get("/ping")
    client.get("/visits")
    assert manager.client.get(manager.valid_key) == "1"
    client.get("/ping", environ_base={"REMOTE_ADDR": "9.8.7.6"})
    assert manager.client.get(manager.valid_key) is None
    with app_module.Session(app_module.engine) as session:
        ip_addresses = [row.ip_address for row in session.query(app_module.Ping).all()]
    assert "9.8.7.6" in ip_addresses


def test_client_ip_uses_remote_addr(app_module, client):
    client.get("/ping", environ_base={"REMOTE_ADDR": "1.1.1.1"})
    with app_module.Session(app_module.engine) as session:
        ping = session.query(app_module.Ping).order_by(app_module.Ping.id.desc()).first()
    assert ping.ip_address == "1.1.1.1"


def test_dev_mode_visits_returns_minus_one(app_module, client, monkeypatch):
    monkeypatch.setattr(app_module, "DEV_MODE", True)
    assert client.get("/visits").data.decode() == "-1"


def test_cache_get_handles_bytes_and_errors(app_module, monkeypatch):
    manager = app_module.cache_manager
    manager.client.set(manager.total_key, b"123")
    assert manager.get_total() == 123
    manager.client.set(manager.total_key, "bad")
    assert manager.get_total() is None
    class BrokenCache(MockMemcache):
        def get(self, key):
            from pymemcache.exceptions import MemcacheError

            raise MemcacheError("memcache error")
    app_module.cache_manager = app_module.CacheManager(BrokenCache(), manager.total_key, manager.valid_key)
    assert app_module.cache_manager.get_total() is None

class MockMemcache:
    def __init__(self):
        self.store: dict[str, object] = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value
        return True

    def delete(self, key):
        self.store.pop(key, None)
        return True


def test_index_lists_available_routes(client):
    body = client.get("/")
    text = body.data.decode()
    assert "/ping" in text
    assert "/visits" in text
