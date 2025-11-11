import os
from datetime import datetime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import func, URL

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    host=os.getenv("POSTGRES_HOST"),
    port=int(os.getenv("POSTGRES_PORT")),
    database=os.getenv("POSTGRES_DB"),
)

class Base(DeclarativeBase):
    pass

class Visits(Base):
    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(primary_key=True)
    ip: Mapped[str]
    visited_at: Mapped[datetime] = mapped_column(default=func.current_timestamp())
