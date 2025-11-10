from fastapi import FastAPI, Request
from sqlalchemy import create_engine, NullPool
from sqlalchemy.orm import sessionmaker

from app.model import Visit
from app.config import settings

engine = create_engine(
    settings.database_url,
    poolclass=NullPool,
    echo=True
)
session = sessionmaker(engine)
api = FastAPI()


@api.get("/")
def root():
    return {"message": "root"}


@api.get("/ping")
def ping(req: Request) -> str:
    with session() as db:
        address = req.client.host
        port = req.client.port
        record: Visit | None = (
            db.query(Visit)
            .filter(Visit.address == address)
            .filter(Visit.port == port)
            .first()
        )

        if record is None:
            db.add(Visit(address=req.client.host, port=req.client.port, count=1))
            db.commit()
        else:
            record.count += 1
            db.commit()
    return "pong"


@api.get("/visits")
def visits(req: Request) -> int:
    with session() as db:
        address = req.client.host
        port = req.client.port
        record: Visit | None = (
            db.query(Visit)
            .filter(Visit.address == address)
            .filter(Visit.port == port)
            .first()
        )

        if record is None:
            return 0
        return record.count
