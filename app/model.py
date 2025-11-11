from sqlalchemy import Column, Integer, String, BigInteger, SmallInteger, MetaData, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = MetaData(naming_convention=naming_convention)


class Base(DeclarativeBase):
    metadata = metadata


class Visit(Base):
    __tablename__ = "visits"
    __table_args__ = (
        UniqueConstraint("address", "port"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    address = Column(String(45), nullable=False)  # up to IPv6 length
    port = Column(Integer, nullable=False)
    count = Column(BigInteger, nullable=False, server_default="0")

    def __repr__(self):
        return f"<Visit(id={self.id}, address='{self.address}', port='{self.port}', count={self.count})>"
