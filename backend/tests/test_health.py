"""
Smoke test — /health endpoint returns 200 with expected payload.

Uses httpx.AsyncClient as the ASGI transport so no running server
is needed.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_returns_200() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "healthy"
    assert "version" in body
    assert "service" in body
