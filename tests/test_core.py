from app.core import ping, visits, session
from app.model import Visit
import pytest


@pytest.fixture(autouse=True, scope="session")
def clean_db() -> None:
    with session() as db:
        records = db.query(Visit).all()
        for rec in records:
            db.delete(rec)
        db.commit()


def test_ping() -> None:
    address = "127.0.0.1"
    port = 80
    ping(address, port)
    assert visits(address, port) == 1
