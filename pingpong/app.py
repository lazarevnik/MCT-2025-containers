"""FastAPI application for ping-pong with visit tracking."""

from typing import Annotated

from fastapi import Depends, FastAPI, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pingpong.db import Visit
from pingpong.settings import DatabaseSettings

settings = DatabaseSettings()
app = FastAPI(title="Ping-Pong API")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint for health checks."""
    return {"status": "ok"}


async def get_db() -> AsyncSession:
    """Get database session."""
    async with settings.async_session_maker() as session:
        yield session


@app.get("/ping")
async def ping(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> str:
    """Ping endpoint that tracks visits by IP address."""
    client_ip = request.client.host if request.client else "unknown"

    result = await db.execute(select(Visit).where(Visit.ip_address == client_ip))
    visit = result.scalar_one_or_none()

    if visit:
        visit.visit_count += 1
    else:
        visit = Visit(ip_address=client_ip, visit_count=1)
        db.add(visit)

    await db.commit()
    return "pong"


@app.get("/visits")
async def visits(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> int:
    """Get visit count for the requesting IP address."""
    client_ip = request.client.host if request.client else "unknown"

    result = await db.execute(select(Visit).where(Visit.ip_address == client_ip))
    visit = result.scalar_one_or_none()

    return visit.visit_count if visit else 0
