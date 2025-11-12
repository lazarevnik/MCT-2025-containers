from fastapi import FastAPI, Request, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy import select, func
import os


ENV_TYPE = os.getenv("ENV", "prod")

if ENV_TYPE == "prod":
    from db import Base, engine, get_db
    from models import Table
    from cache import get_redis
else:
    async def get_db():
        yield None


app = FastAPI(title="Ping Pong")


@app.on_event("startup")
async def startup():
    if ENV_TYPE == "prod":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


@app.get("/ping", response_class=PlainTextResponse)
async def ping(request: Request, db=Depends(get_db)):
    if ENV_TYPE == "dev":
        return "pong"
    
    ip = request.client.host
    visits = Table(ip=ip)
    db.add(visits)
    await db.commit()

    # обновляем кэш
    redis = await get_redis()
    count = await redis.get("visit_count")
    if count is not None:
        await redis.incr("visit_count")

    return "pong"


@app.get("/visits")
async def visits(db=Depends(get_db)):
    if ENV_TYPE == "dev":
        return -1

    redis = await get_redis()
    cached = await redis.get("visit_count")

    if cached is not None: # кэш есть
        return int(cached)

    result = await db.execute(select(func.count(Table.id)))
    count = result.scalar()

    await redis.set("visit_count", count)

    return count