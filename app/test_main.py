from typing import Generator, Dict
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import MagicMock, patch

from main import app, get_db, get_cached_count, update_cache, increment_cache
from db import Base, Visit


# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL: str = "sqlite:///:memory:"

# Create engine with StaticPool to share connection across tests
engine: Engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=None,
)

TestingSessionLocal: sessionmaker[Session] = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    # Create tables before each test
    Base.metadata.create_all(bind=engine)

    connection = engine.connect()
    transaction = connection.begin()

    # Create session bound to this connection
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session: Session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        # Drop tables after each test to ensure clean state
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with overridden DB dependency."""

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_redis() -> Generator[MagicMock, None, None]:
    """Mock Redis client for all tests."""
    with patch("main.redis_client") as mock:
        yield mock


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check(self, client: TestClient) -> None:
        """Test that health endpoint returns OK status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestPingEndpoint:
    """Tests for /ping endpoint."""

    def test_ping_creates_visit(self, client: TestClient, test_db: Session, mock_redis: MagicMock) -> None:
        """Test that /ping creates a visit in the database."""
        mock_redis.incr.return_value = 1

        response = client.get("/ping")
        assert response.status_code == 200
        assert response.json() == "pong"

        # Verify visit was created in DB
        visit_count: int = test_db.query(Visit).count()
        assert visit_count == 1

        # Verify Redis cache was incremented
        mock_redis.incr.assert_called_once()

    def test_ping_multiple_times(self, client: TestClient, test_db: Session, mock_redis: MagicMock) -> None:
        """Test that multiple pings create multiple visits."""
        mock_redis.incr.return_value = None

        # Call ping 3 times
        for _ in range(3):
            response = client.get("/ping")
            assert response.status_code == 200

        # Verify 3 visits were created
        visit_count: int = test_db.query(Visit).count()
        assert visit_count == 3

    def test_ping_with_redis_failure(self, client: TestClient, test_db: Session, mock_redis: MagicMock) -> None:
        """Test that ping works even if Redis fails."""
        mock_redis.incr.side_effect = Exception("Redis connection error")

        response = client.get("/ping")
        assert response.status_code == 200
        assert response.json() == "pong"

        # Verify visit was still created in DB
        visit_count: int = test_db.query(Visit).count()
        assert visit_count == 1


class TestVisitsEndpoint:
    """Tests for /visits endpoint."""

    def test_visits_returns_count_from_cache(self, client: TestClient, test_db: Session, mock_redis: MagicMock) -> None:
        """Test that /visits returns cached count when available."""
        mock_redis.get.return_value = "42"

        response = client.get("/visits")
        assert response.status_code == 200
        assert response.json() == {"visits": 42}

        # Verify cache was checked
        mock_redis.get.assert_called_once()

    def test_visits_falls_back_to_db(self, client: TestClient, test_db: Session, mock_redis: MagicMock) -> None:
        """Test that /visits queries DB when cache miss."""
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True

        # Create some visits in the test DB
        test_db.add(Visit(client_ip="192.168.1.1"))
        test_db.add(Visit(client_ip="192.168.1.2"))
        test_db.commit()

        response = client.get("/visits")
        assert response.status_code == 200
        assert response.json() == {"visits": 2}

        # Verify cache was updated
        mock_redis.set.assert_called_once_with("visits:count", 2)

    def test_visits_empty_database(self, client: TestClient, test_db: Session, mock_redis: MagicMock) -> None:
        """Test that /visits returns 0 for empty database."""
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True

        response = client.get("/visits")
        assert response.status_code == 200
        assert response.json() == {"visits": 0}

    def test_visits_handles_redis_failure(self, client: TestClient, test_db: Session, mock_redis: MagicMock) -> None:
        """Test that /visits works even if Redis completely fails."""
        mock_redis.get.side_effect = Exception("Redis error")
        mock_redis.set.side_effect = Exception("Redis error")

        # Create visit in DB
        test_db.add(Visit(client_ip="192.168.1.1"))
        test_db.commit()

        response = client.get("/visits")
        assert response.status_code == 200
        assert response.json() == {"visits": 1}


class TestCacheFunctions:
    """Tests for cache helper functions."""

    def test_get_cached_count_success(self, mock_redis: MagicMock) -> None:
        """Test getting cached count successfully."""
        mock_redis.get.return_value = "10"
        count: int | None = get_cached_count()
        assert count == 10

    def test_get_cached_count_none(self, mock_redis: MagicMock) -> None:
        """Test getting cached count when key doesn't exist."""
        mock_redis.get.return_value = None
        count: int | None = get_cached_count()
        assert count is None

    def test_get_cached_count_error(self, mock_redis: MagicMock) -> None:
        """Test getting cached count handles errors gracefully."""
        mock_redis.get.side_effect = Exception("Redis error")
        count: int | None = get_cached_count()
        assert count is None

    def test_update_cache_success(self, test_db: Session, mock_redis: MagicMock) -> None:
        """Test updating cache from database."""
        test_db.add(Visit(client_ip="192.168.1.1"))
        test_db.add(Visit(client_ip="192.168.1.2"))
        test_db.commit()

        count: int = update_cache(test_db)
        assert count == 2
        mock_redis.set.assert_called_once_with("visits:count", 2)

    def test_update_cache_redis_failure(self, test_db: Session, mock_redis: MagicMock) -> None:
        """Test update_cache still returns count even if Redis fails."""
        mock_redis.set.side_effect = Exception("Redis error")
        test_db.add(Visit(client_ip="192.168.1.1"))
        test_db.commit()

        count: int = update_cache(test_db)
        assert count == 1  # Should still return the count

    def test_increment_cache_success(self, mock_redis: MagicMock) -> None:
        """Test incrementing cache."""
        mock_redis.incr.return_value = 5
        increment_cache()
        mock_redis.incr.assert_called_once_with("visits:count")

    def test_increment_cache_failure(self, mock_redis: MagicMock) -> None:
        """Test increment_cache handles errors gracefully."""
        mock_redis.incr.side_effect = Exception("Redis error")
        # Should not raise exception
        increment_cache()


class TestIntegration:
    """Integration tests combining multiple operations."""

    def test_ping_then_visits_consistency(self, client: TestClient, test_db: Session, mock_redis: MagicMock) -> None:
        """Test that ping followed by visits shows consistent count."""
        # Mock Redis to simulate cache behavior
        cache_value: Dict[str, int] = {"count": 0}

        def mock_incr(key: str) -> int:
            cache_value["count"] += 1
            return cache_value["count"]

        def mock_get(key: str) -> str | None:
            return str(cache_value["count"]) if cache_value["count"] > 0 else None

        mock_redis.incr.side_effect = mock_incr
        mock_redis.get.side_effect = mock_get
        mock_redis.set.return_value = True

        # Call ping 5 times
        for _ in range(5):
            response = client.get("/ping")
            assert response.status_code == 200

        # Check visits count
        response = client.get("/visits")
        assert response.status_code == 200
        assert response.json() == {"visits": 5}

        # Verify DB has same count
        db_count: int = test_db.query(Visit).count()
        assert db_count == 5
