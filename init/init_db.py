import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

import sys
sys.path.append("/app")

from db import Base


DB_URL = "postgresql+asyncpg://postgres:postgres@db:5432/postgres"


async def init_db():
    print("Init DB...")

    engine = create_async_engine(DB_URL, echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    await engine.dispose()

    print("DB initialized successfully")


if __name__ == "__main__":
    asyncio.run(init_db())
