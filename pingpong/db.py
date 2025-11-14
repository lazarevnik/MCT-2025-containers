from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""


class Visit(Base):
    """Model for tracking visits by IP address."""

    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ip_address: Mapped[str] = mapped_column(unique=True, index=True)
    visit_count: Mapped[int] = mapped_column(default=0)
