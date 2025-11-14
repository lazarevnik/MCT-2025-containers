"""Tests for database models."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pingpong.db import Base, Visit


class TestBase:
    """Tests for the Base class."""

    def test_base_is_declarative(self):
        """Test Base is a proper SQLAlchemy declarative base."""
        from sqlalchemy.orm import DeclarativeBase

        assert issubclass(Base, DeclarativeBase)


class TestVisitModel:
    """Tests for the Visit model."""

    def test_visit_table_name(self):
        """Test Visit model has correct table name."""
        assert Visit.__tablename__ == "visits"

    def test_visit_fields(self):
        """Test Visit model has required fields."""
        assert hasattr(Visit, "id")
        assert hasattr(Visit, "ip_address")
        assert hasattr(Visit, "visit_count")

    async def test_create_visit(self, db_session: AsyncSession):
        """Test creating a Visit record."""
        visit = Visit(ip_address="192.168.1.1", visit_count=1)
        db_session.add(visit)
        await db_session.commit()

        # Retrieve and verify
        result = await db_session.execute(
            select(Visit).where(Visit.ip_address == "192.168.1.1")
        )
        retrieved = result.scalar_one()

        assert retrieved.ip_address == "192.168.1.1"
        assert retrieved.visit_count == 1
        assert retrieved.id is not None

    async def test_update_visit_count(self, db_session: AsyncSession):
        """Test updating visit count."""
        visit = Visit(ip_address="192.168.1.2", visit_count=1)
        db_session.add(visit)
        await db_session.commit()

        # Update count
        visit.visit_count += 1
        await db_session.commit()

        # Retrieve and verify
        result = await db_session.execute(
            select(Visit).where(Visit.ip_address == "192.168.1.2")
        )
        retrieved = result.scalar_one()

        assert retrieved.visit_count == 2

    async def test_unique_ip_address(self, db_session: AsyncSession):
        """Test ip_address is unique."""
        visit1 = Visit(ip_address="192.168.1.3", visit_count=1)
        db_session.add(visit1)
        await db_session.commit()

        visit2 = Visit(ip_address="192.168.1.3", visit_count=1)
        db_session.add(visit2)

        with pytest.raises(Exception):  # Should raise integrity error
            await db_session.commit()

    async def test_multiple_different_ips(self, db_session: AsyncSession):
        """Test storing multiple visits with different IPs."""
        visit1 = Visit(ip_address="192.168.1.10", visit_count=5)
        visit2 = Visit(ip_address="192.168.1.11", visit_count=3)
        visit3 = Visit(ip_address="192.168.1.12", visit_count=1)

        db_session.add_all([visit1, visit2, visit3])
        await db_session.commit()

        # Retrieve all visits
        result = await db_session.execute(select(Visit))
        visits = result.scalars().all()

        assert len(visits) == 3

        ip_counts = {v.ip_address: v.visit_count for v in visits}
        assert ip_counts["192.168.1.10"] == 5
        assert ip_counts["192.168.1.11"] == 3
        assert ip_counts["192.168.1.12"] == 1
