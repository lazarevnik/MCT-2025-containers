"""FastAPI application for ping-pong with visit tracking."""

from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.responses import PlainTextResponse
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pingpong.db import Visit
from pingpong.settings import get_settings

app = FastAPI(title="Ping-Pong API")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint for health checks."""
    return {"status": "ok"}


async def get_db() -> AsyncSession:
    """Get database session."""
    async with get_settings().db.async_session_maker() as session:
        yield session


@app.get("/ping", response_class=PlainTextResponse)
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


async def get_poem(number: int) -> str | None:
    """Use vLLM to generate three words that rhyme with a number."""
    try:
        prompt = f"""Generate a silly 4-line poem with phrase `and the visits number is {number}` or something like this"""

        response = (
            await get_settings()
            .llm.get_client()
            .chat.completions.create(
                model=get_settings().llm.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=50,
            )
        )

        return response.choices[0].message.content.strip()
    except Exception:
        logger.exception("Error during llm call")
        return None


@app.get("/silly-visits", response_class=PlainTextResponse)
async def silly_visits(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> str:
    """Get visit count in a silly way with rhyming words."""
    client_ip = request.client.host if request.client else "unknown"

    result = await db.execute(select(Visit).where(Visit.ip_address == client_ip))
    visit = result.scalar_one_or_none()

    count = visit.visit_count if visit else 0

    return await get_poem(count)
