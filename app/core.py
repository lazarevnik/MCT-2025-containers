from sqlalchemy import create_engine, NullPool
from sqlalchemy.orm import sessionmaker

from app.config import settings, Modes
from app.model import Visit

engine = create_engine(
    settings.database_url,
    poolclass=NullPool,
    echo=True
)
session = sessionmaker(engine)


def ping(address: str, port: int) -> str:
    if settings.APP_MODE == Modes.PROD:
        with session() as db:
            record: Visit | None = (
                db.query(Visit)
                .filter(Visit.address == address)
                .filter(Visit.port == port)
                .first()
            )

            if record is None:
                db.add(Visit(address=address, port=port, count=1))
                db.commit()
            else:
                record.count += 1
                db.commit()
    return "pong"


def visits(address: str, port: int) -> int:
    if settings.APP_MODE == Modes.PROD:
        with session() as db:
            record: Visit | None = (
                db.query(Visit)
                .filter(Visit.address == address)
                .filter(Visit.port == port)
                .first()
            )
        if record is None:
            return 0
        return record.count
    return -1
