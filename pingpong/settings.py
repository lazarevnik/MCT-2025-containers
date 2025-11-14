from collections.abc import Callable

from openai import AsyncClient
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool


class DatabaseSettings(BaseSettings):
    """Settings for database connection."""

    model_config = SettingsConfigDict(case_sensitive=False, env_prefix="DB_")

    host: str = Field("localhost", description="Database host")
    port: int = Field(5432, description="Database port")
    user: str = Field("postgres", description="Database user")
    password: SecretStr = Field(description="Database password")
    database: str = Field("pingpong", description="Database name")
    echo: bool = Field(False, description="Enable SQL query logging")
    pool_size: int = Field(5, description="Connection pool size")
    max_overflow: int = Field(15, description="Maximum overflow connections")
    disable_pooling: bool = False

    @property
    def url(self) -> str:
        """Get the database URL."""
        return f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.database}"

    @property
    def engine(self) -> AsyncEngine:
        """Initialize and get async database engine."""
        if not hasattr(self, "_engine"):
            if self.disable_pooling:
                self._engine = create_async_engine(
                    self.url,
                    echo=self.echo,
                    poolclass=NullPool,
                )
            else:
                self._engine = create_async_engine(
                    self.url,
                    echo=self.echo,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                )
        return self._engine

    @property
    def async_session_maker(self) -> Callable[[], AsyncSession]:
        """Get async session maker."""
        return async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )


class LLMSettings(BaseSettings):
    """Settings for LLM service connection."""

    model_config = SettingsConfigDict(case_sensitive=False, env_prefix="LLM_")

    base_url: str = Field("http://vllm:8000/v1", description="LLM API base URL")
    api_key: str = Field("EMPTY", description="LLM API key (not required for local)")
    model_name: str = "Qwen/Qwen2.5-0.5B-Instruct"

    def get_client(self) -> AsyncClient:
        return AsyncClient(
            base_url=self.base_url,
            api_key=self.api_key,
        )


class Settings(BaseModel):
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if not _settings:
        _settings = Settings()
    return _settings
