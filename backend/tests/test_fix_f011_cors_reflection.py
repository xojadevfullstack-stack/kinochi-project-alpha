import pytest
from starlette.requests import Request
from app.main import generic_exception_handler
from app.core.config import settings


@pytest.mark.asyncio
async def test_f011_cors_reflection_blocks_attacker():
    """F-011 regression: generic_exception_handler must not reflect attacker origin."""
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/trigger-error",
        "headers": [(b"origin", b"https://attacker.com")],
        "client": ("127.0.0.1", 12345),
        "app": None,
    }
    req = Request(scope)

    resp = await generic_exception_handler(req, Exception("Boom"))
    assert resp.status_code == 500
    assert "Access-Control-Allow-Origin" not in resp.headers
    assert "Access-Control-Allow-Credentials" not in resp.headers


@pytest.mark.asyncio
async def test_f011_cors_reflection_allows_whitelisted_origin():
    """F-011 regression: generic_exception_handler allows configured CORS origin."""
    allowed_origin = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "http://localhost:3000"
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/trigger-error",
        "headers": [(b"origin", allowed_origin.encode("utf-8"))],
        "client": ("127.0.0.1", 12345),
        "app": None,
    }
    req = Request(scope)

    resp = await generic_exception_handler(req, Exception("Boom"))
    assert resp.status_code == 500
    assert resp.headers.get("Access-Control-Allow-Origin") == allowed_origin
    assert resp.headers.get("Access-Control-Allow-Credentials") == "true"
