from fastapi import FastAPI, Request
from sqlalchemy import create_engine, NullPool
from sqlalchemy.orm import sessionmaker, Session

from model import Visit

engine = create_engine(
    "0.0.0.0",
    poolclass=NullPool,
    echo=True
)
session = sessionmaker(engine)
app = FastAPI()


@app.get("/")
def root():
    return {"message": "root"}


@app.get("/ping")
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


@app.get("/visits")
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
