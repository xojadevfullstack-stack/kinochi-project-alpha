import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_input_validation_boundary_pagination():
    """
    Input validation boundary tests for public endpoints:
    page=0, page=-1, and excessive limits.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # page = 0
        resp_zero = await client.get("/api/v1/movies?page=0&limit=10")
        # page = -1
        resp_neg = await client.get("/api/v1/movies?page=-1&limit=10")
        # limit = 10^7
        resp_huge = await client.get("/api/v1/movies?page=1&limit=10000000")

        # page=0 and page=-1 return 200 OK (graceful clamp/fallback)
        assert resp_zero.status_code == 200
        assert resp_neg.status_code == 200
        # limit exceeding maximum allowed (100) returns 422 Unprocessable Entity
        assert resp_huge.status_code == 422
