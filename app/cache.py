import redis.asyncio as redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_redis = None

async def get_redis():
    global _redis

    if _redis is None:
        _redis = await redis.from_url(REDIS_URL, decode_responses=True)
        
    return _redis
