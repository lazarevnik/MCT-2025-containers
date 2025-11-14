import asyncio
import os

import asyncpg


DATABASE_URL = os.getenv("DATABASE_URL")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS visits ( 
    id BIGSERIAL PRIMARY KEY
);
"""


async def init_db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=1)
    async with pool.acquire() as conn:
        await conn.execute(CREATE_TABLE_SQL)
    await pool.close()


if __name__ == "__main__":
    asyncio.run(init_db())

