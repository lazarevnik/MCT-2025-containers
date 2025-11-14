"""Tests for FastAPI application endpoints."""

from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pingpong.db import Visit


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_sync(self, sync_client: TestClient):
        """Test root endpoint returns ok status."""
        response = sync_client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    async def test_root_async(self, client: AsyncClient):
        """Test root endpoint with async client."""
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestPingEndpoint:
    """Tests for the /ping endpoint."""

    async def test_ping_first_visit(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test ping endpoint creates a new visit record."""
        response = await client.get("/ping")

        assert response.status_code == 200
        assert response.text == "pong"
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

        # Verify database record
        result = await db_session.execute(select(Visit))
        visits = result.scalars().all()
        assert len(visits) == 1
        assert visits[0].visit_count == 1

    async def test_ping_multiple_visits(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test ping endpoint increments visit count."""
        # First visit
        response1 = await client.get("/ping")
        assert response1.status_code == 200
        assert response1.text == "pong"

        # Second visit
        response2 = await client.get("/ping")
        assert response2.status_code == 200
        assert response2.text == "pong"

        # Third visit
        response3 = await client.get("/ping")
        assert response3.status_code == 200
        assert response3.text == "pong"

        # Verify database record
        result = await db_session.execute(select(Visit))
        visits = result.scalars().all()
        assert len(visits) == 1
        assert visits[0].visit_count == 3

    async def test_ping_different_ips(self, db_session: AsyncSession):
        """Test ping endpoint tracks different IPs separately."""
        from unittest.mock import Mock

        from pingpong.app import ping

        # Mock request with first IP
        request1 = Mock()
        request1.client = Mock()
        request1.client.host = "192.168.1.1"

        result1 = await ping(request1, db_session)
        assert result1 == "pong"

        # Mock request with second IP
        request2 = Mock()
        request2.client = Mock()
        request2.client.host = "192.168.1.2"

        result2 = await ping(request2, db_session)
        assert result2 == "pong"

        # Verify both IPs are tracked
        result = await db_session.execute(select(Visit))
        visits = result.scalars().all()
        assert len(visits) == 2

        ip_counts = {v.ip_address: v.visit_count for v in visits}
        assert ip_counts["192.168.1.1"] == 1
        assert ip_counts["192.168.1.2"] == 1

    async def test_ping_no_client(self, db_session: AsyncSession):
        """Test ping endpoint handles missing client info."""
        from unittest.mock import Mock

        from pingpong.app import ping

        # Mock request without client
        request = Mock()
        request.client = None

        result = await ping(request, db_session)
        assert result == "pong"

        # Verify "unknown" IP is used
        result = await db_session.execute(
            select(Visit).where(Visit.ip_address == "unknown")
        )
        visit = result.scalar_one_or_none()
        assert visit is not None
        assert visit.visit_count == 1


class TestVisitsEndpoint:
    """Tests for the /visits endpoint."""

    async def test_visits_no_history(self, client: AsyncClient):
        """Test visits endpoint returns 0 for new IP."""
        response = await client.get("/visits")

        assert response.status_code == 200
        assert response.json() == 0

    async def test_visits_with_history(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test visits endpoint returns correct count after visits."""
        # Make some ping requests first
        await client.get("/ping")
        await client.get("/ping")
        await client.get("/ping")

        # Check visit count
        response = await client.get("/visits")

        assert response.status_code == 200
        assert response.json() == 3

    async def test_visits_different_ips(self, db_session: AsyncSession):
        """Test visits endpoint tracks different IPs separately."""
        from unittest.mock import Mock

        from pingpong.app import ping, visits

        # First IP makes 3 visits
        request1 = Mock()
        request1.client = Mock()
        request1.client.host = "192.168.1.1"

        await ping(request1, db_session)
        await ping(request1, db_session)
        await ping(request1, db_session)

        # Second IP makes 2 visits
        request2 = Mock()
        request2.client = Mock()
        request2.client.host = "192.168.1.2"

        await ping(request2, db_session)
        await ping(request2, db_session)

        # Check visit counts
        count1 = await visits(request1, db_session)
        assert count1 == 3

        count2 = await visits(request2, db_session)
        assert count2 == 2

    async def test_visits_no_client(self, db_session: AsyncSession):
        """Test visits endpoint handles missing client info."""
        from unittest.mock import Mock

        from pingpong.app import visits

        # Mock request without client
        request = Mock()
        request.client = None

        count = await visits(request, db_session)
        assert count == 0


class TestSillyVisitsEndpoint:
    """Tests for the /silly-visits endpoint."""

    async def test_silly_visits_no_history(self, client: AsyncClient, monkeypatch):
        """Test silly-visits endpoint returns 0 count with rhymes."""

        # Mock the LLM call
        async def mock_get_rhyming_words(number: int) -> list[str]:
            return ["fun", "run", "sun"]

        monkeypatch.setattr("pingpong.app.get_rhyming_words", mock_get_rhyming_words)

        response = await client.get("/silly-visits")

        assert response.status_code == 200
        assert "0" in response.text
        assert "fun" in response.text or "run" in response.text
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

    async def test_silly_visits_with_history(self, client: AsyncClient, monkeypatch):
        """Test silly-visits endpoint returns correct count with rhymes."""

        # Mock the LLM call
        async def mock_get_rhyming_words(number: int) -> list[str]:
            return ["free", "tree", "sea"]

        monkeypatch.setattr("pingpong.app.get_rhyming_words", mock_get_rhyming_words)

        # Make some ping requests first
        await client.get("/ping")
        await client.get("/ping")
        await client.get("/ping")

        response = await client.get("/silly-visits")

        assert response.status_code == 200
        assert "3" in response.text
        # Check for at least one of the rhyming words
        assert (
            "free" in response.text or "tree" in response.text or "sea" in response.text
        )

    async def test_get_rhyming_words_fallback(self, monkeypatch):
        """Test that get_rhyming_words has proper fallback on error."""
        # Mock vllm_client to raise an exception
        from unittest.mock import AsyncMock

        from pingpong.app import get_rhyming_words

        mock_client = AsyncMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        monkeypatch.setattr("pingpong.app.vllm_client", mock_client)

        # Should return fallback rhymes
        rhymes = await get_rhyming_words(5)
        assert rhymes == ["fun", "run", "sun"]
