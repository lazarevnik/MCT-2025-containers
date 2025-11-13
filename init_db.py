"""Database initialization script."""

import asyncio
import logging

from pingpong.db import Base
from pingpong.settings import DatabaseSettings

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Initialize the database by creating all tables."""
    settings = DatabaseSettings()

    async with settings.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.debug("Database initialized successfully!")

    await settings.engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())
