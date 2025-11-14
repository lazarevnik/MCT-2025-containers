import os
from contextlib import asynccontextmanager

import asyncpg  # type: ignore[import]
import redis.asyncio as redis  # type: ignore[import]
from fastapi import FastAPI, HTTPException


DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://cache:6379/0")
CACHE_KEY = "visits_count"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    if not REDIS_URL:
        raise RuntimeError("REDIS_URL environment variable is not set")

    try:
        app.state.db_pool = await asyncpg.create_pool(DATABASE_URL)
    except Exception as exc:
        raise RuntimeError("Failed to connect to Postgres") from exc

    try:
        app.state.redis = redis.from_url(
            REDIS_URL, encoding="utf-8", decode_responses=True
        )
    except Exception as exc:
        await app.state.db_pool.close()
        raise RuntimeError("Failed to connect to Redis") from exc

    try:
        yield
    finally:
        await app.state.db_pool.close()
        await app.state.redis.aclose()


app = FastAPI(title="Ping Pong API", lifespan=lifespan)


@app.get("/ping")
async def ping():
    try:
        async with app.state.db_pool.acquire() as conn:
            await conn.execute("INSERT INTO visits DEFAULT VALUES;")
            count = await conn.fetchval("SELECT COUNT(*) FROM visits;")
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to record visit") from exc

    await app.state.redis.set(CACHE_KEY, str(count))

    return "pong"


@app.get("/visits")
async def get_visits():
    cached_value = await app.state.redis.get(CACHE_KEY)
    if cached_value is not None:
        return int(cached_value)

    try:
        async with app.state.db_pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM visits;")
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch visits") from exc

    await app.state.redis.set(CACHE_KEY, str(count))

    return count

