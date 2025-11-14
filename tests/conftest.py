"""Pytest fixtures for testing."""

from typing import AsyncGenerator, Generator
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from testcontainers.postgres import PostgresContainer

from pingpong.settings import DatabaseSettings, get_settings


@pytest.fixture(scope="session")
def override_settings() -> Generator[None, None, None]:
    """Generate test database URL from postgres container."""
    with PostgresContainer("postgres:16.10-alpine") as container:
        settings = DatabaseSettings(
            host=container.get_container_host_ip(),
            port=container.get_exposed_port(5432),
            user=container.username,
            password=container.password,
            database=container.dbname,
            disable_pooling=True,
        )
        with patch("pingpong.settings._settings", new=settings):
            yield


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def init_engine() -> AsyncGenerator[None, None]:
    from pingpong.db import Base

    # engine is a singleton in our app
    engine = get_settings().db.engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(init_engine: None):
    # Ensure clean state before each test
    await _clean_tables()

    async with get_settings().db.async_session_maker() as s:
        yield s

    # Cleanup after each test
    await _clean_tables()


async def _clean_tables() -> None:
    from pingpong.db import Base

    tables = Base.metadata.tables.values()

    # Delete all rows from all tables
    async with get_settings().db.async_session_maker() as test_session:
        for table in reversed(list(tables)):
            await test_session.execute(table.delete())
        await test_session.commit()


@pytest.fixture
def sync_client(override_settings: None) -> Generator[TestClient, None, None]:
    """Create a synchronous test client for the FastAPI app.

    This fixture uses FastAPI's TestClient which is synchronous
    and suitable for testing synchronous endpoints.
    """
    from pingpong.app import app

    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def client(
    override_settings: None, init_engine: None
) -> AsyncGenerator[AsyncClient, None]:
    """Create an asynchronous test client for the FastAPI app.

    This fixture uses httpx.AsyncClient with ASGITransport,
    which allows for proper async/await testing of endpoints.
    """
    from pingpong.app import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
