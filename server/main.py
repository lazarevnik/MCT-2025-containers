from typing import Annotated

from fastapi import FastAPI, Request, Depends
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker, Session

from .database import DATABASE_URL, Visits

app = FastAPI()

def get_session():
    engine = create_engine(DATABASE_URL)
    session_maker = sessionmaker(bind=engine)
    with session_maker() as session:
        yield session


@app.get("/ping")
def ping(request: Request, session: Annotated[Session, Depends(get_session)]) -> str:
    visit = Visits(ip=request.client.host)
    session.add(visit)
    session.commit()
    return "pong"


@app.get("/visits")
def visits(session: Annotated[Session, Depends(get_session)]) -> int:
    stmt = select(func.count()).select_from(Visits)
    result = session.execute(stmt).scalar_one()
    return str(result)
