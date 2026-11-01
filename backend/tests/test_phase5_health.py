import pytest
from unittest.mock import patch, AsyncMock
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.core.bot_status import set_bot_status, set_bot_alive


@pytest.mark.asyncio
async def test_health_check_all_healthy():
    transport = ASGITransport(app=app)
    set_bot_status("alive")
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["bot"] == "alive"
        assert data["bot_alive"] is True
        assert data["redis"] in ["connected", "unavailable"]
    finally:
        set_bot_status("stopped")


@pytest.mark.asyncio
async def test_health_check_degraded_bot_returns_200():
    transport = ASGITransport(app=app)
    set_bot_status("degraded")
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["bot"] == "degraded"
        assert data["bot_alive"] is False
    finally:
        set_bot_status("stopped")


@pytest.mark.asyncio
async def test_health_check_redis_unavailable_returns_200():
    transport = ASGITransport(app=app)
    with patch("app.core.cache.is_redis_available", return_value=False):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["redis"] == "unavailable"


@pytest.mark.asyncio
async def test_health_check_database_failure_returns_503():
    transport = ASGITransport(app=app)
    # Mock database session execute to simulate connection failure / timeout
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None
    mock_session.execute.side_effect = TimeoutError("Database connection timed out")

    with patch("app.infrastructure.db.session.async_session_factory", return_value=mock_session):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get("/health")
        assert res.status_code == 503
        data = res.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "unavailable"
