from sqlalchemy import Column, Integer, String, DateTime, func

from db import Base

class Table(Base):
    __tablename__ = "visits"

    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
