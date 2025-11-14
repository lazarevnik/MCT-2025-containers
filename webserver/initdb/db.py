from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class RequestDb(Base):
    __tablename__ = "requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    ip: Mapped[str] = mapped_column(String(len("256.256.256.256")))
    time: Mapped[datetime]
    request: Mapped[str]