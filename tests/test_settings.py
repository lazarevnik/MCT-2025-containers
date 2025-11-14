"""Tests for settings module."""

import os
from unittest.mock import patch

from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.pool import NullPool

from pingpong.settings import DatabaseSettings


class TestDatabaseSettings:
    """Tests for DatabaseSettings class."""

    def test_default_values(self):
        """Test default settings values (may be overridden by environment)."""
        settings = DatabaseSettings(password="test_password")

        # These values might come from environment or use defaults
        assert settings.host in ["localhost", "db"]  # Allow both default and env value
        assert settings.port == 5432
        assert settings.user == "postgres"
        assert settings.database in [
            "pingpong",
            "pingpong_test",
        ]  # Allow both default and test db
        assert isinstance(settings.echo, bool)
        assert settings.pool_size == 5
        assert settings.max_overflow == 15
        assert settings.disable_pooling is False

    def test_custom_values(self):
        """Test custom settings values."""
        settings = DatabaseSettings(
            host="custom-host",
            port=5433,
            user="custom-user",
            password="custom-password",
            database="custom-db",
            echo=True,
            pool_size=10,
            max_overflow=20,
            disable_pooling=True,
        )

        assert settings.host == "custom-host"
        assert settings.port == 5433
        assert settings.user == "custom-user"
        assert settings.database == "custom-db"
        assert settings.echo is True
        assert settings.pool_size == 10
        assert settings.max_overflow == 20
        assert settings.disable_pooling is True

    def test_password_is_secret(self):
        """Test password is stored as SecretStr."""
        settings = DatabaseSettings(password="secret_password")

        assert isinstance(settings.password, SecretStr)
        assert settings.password.get_secret_value() == "secret_password"
        assert str(settings.password) == "**********"

    def test_url_property(self):
        """Test database URL generation."""
        settings = DatabaseSettings(
            host="testhost",
            port=5432,
            user="testuser",
            password="testpass",
            database="testdb",
        )

        expected_url = "postgresql+asyncpg://testuser:testpass@testhost:5432/testdb"
        assert settings.url == expected_url

    def test_url_with_special_characters(self):
        """Test database URL with special characters in password."""
        settings = DatabaseSettings(
            host="testhost",
            port=5432,
            user="testuser",
            password="p@ss:w0rd!",
            database="testdb",
        )

        assert "p@ss:w0rd!" in settings.url
        assert settings.url.startswith("postgresql+asyncpg://testuser:")

    def test_engine_property(self):
        """Test engine property creates an AsyncEngine."""
        settings = DatabaseSettings(password="testpass")

        engine = settings.engine
        assert isinstance(engine, AsyncEngine)
        assert engine is settings.engine  # Should return same instance

    def test_engine_with_pooling(self):
        """Test engine creation with connection pooling."""
        settings = DatabaseSettings(
            password="testpass",
            disable_pooling=False,
            pool_size=10,
            max_overflow=20,
        )

        engine = settings.engine
        assert isinstance(engine, AsyncEngine)
        assert engine.pool.size() == 10

    def test_engine_without_pooling(self):
        """Test engine creation without connection pooling."""
        settings = DatabaseSettings(
            password="testpass",
            disable_pooling=True,
        )

        engine = settings.engine
        assert isinstance(engine, AsyncEngine)
        assert isinstance(engine.pool, NullPool)

    def test_async_session_maker(self):
        """Test async_session_maker property."""
        settings = DatabaseSettings(password="testpass")

        session_maker = settings.async_session_maker
        assert callable(session_maker)

    def test_env_prefix(self):
        """Test environment variable prefix."""
        with patch.dict(
            os.environ,
            {
                "DB_HOST": "env-host",
                "DB_PORT": "5433",
                "DB_USER": "env-user",
                "DB_PASSWORD": "env-password",
                "DB_DATABASE": "env-database",
            },
        ):
            settings = DatabaseSettings()

            assert settings.host == "env-host"
            assert settings.port == 5433
            assert settings.user == "env-user"
            assert settings.password.get_secret_value() == "env-password"
            assert settings.database == "env-database"

    def test_case_insensitive_env_vars(self):
        """Test that environment variables are case insensitive."""
        with patch.dict(
            os.environ,
            {
                "db_host": "lowercase-host",
                "DB_PASSWORD": "test-password",
            },
        ):
            settings = DatabaseSettings()

            assert settings.host == "lowercase-host"
            assert settings.password.get_secret_value() == "test-password"
