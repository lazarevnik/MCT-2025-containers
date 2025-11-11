import os
from typing import Annotated

from fastapi import FastAPI, Request, Depends
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker, Session
from fastapi.responses import PlainTextResponse

IS_DEV = os.getenv("DEV", "False").lower() == "true"
if not IS_DEV:
    from .database import DATABASE_URL, Visits

app = FastAPI()

def get_session():
    if IS_DEV:
        yield 1
    else:
        engine = create_engine(DATABASE_URL)
        session_maker = sessionmaker(bind=engine)
        with session_maker() as session:
            yield session


@app.get("/")
def root():
    return "Hello, World!"

@app.get("/ping")
def ping(request: Request, session: Annotated[Session, Depends(get_session)]) -> PlainTextResponse:
    if not IS_DEV:
        visit = Visits(ip=request.client.host)
        session.add(visit)
        session.commit()
    return PlainTextResponse("pong")


@app.get("/visits")
def visits(session: Annotated[Session, Depends(get_session)]) -> int:
    if IS_DEV:
        result = -1
    else:
        stmt = select(func.count()).select_from(Visits)
        result = session.execute(stmt).scalar_one()
    return result
