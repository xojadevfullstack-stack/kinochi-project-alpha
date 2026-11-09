import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app, is_origin_allowed
from app.core.config import settings

@pytest.mark.asyncio
async def test_cors_attacker_subdomain_rejected():
    """
    BUG-002 Regression Test:
    Arbitrary attacker subdomains such as 'kinochi-project-alpha-attacker.vercel.app'
    or 'kinochi-admin-phishing.vercel.app' MUST NOT match CORS_ORIGIN_REGEX and
    MUST NOT receive Access-Control-Allow-Origin headers.
    """
    attacker_origins = [
        "https://kinochi-project-alpha-attacker.vercel.app",
        "https://kinochi-admin-phishing.vercel.app",
        "https://kinochi-project-alpha-evil.vercel.app",
        "https://kinochi-admin-fake.vercel.app",
        "https://attacker.vercel.app",
        "http://kinochi-project-alpha.vercel.app",
    ]

    for attacker_origin in attacker_origins:
        assert not is_origin_allowed(attacker_origin), (
            f"Security flaw: Attacker origin {attacker_origin} was allowed by CORS configuration!"
        )

    # Preflight request simulation
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.options(
            "/api/v1/movies",
            headers={
                "Origin": "https://kinochi-project-alpha-attacker.vercel.app",
                "Access-Control-Request-Method": "GET",
            }
        )
        assert "access-control-allow-origin" not in res.headers, (
            f"Vulnerability: Attacker received Access-Control-Allow-Origin header: {res.headers}"
        )

@pytest.mark.asyncio
async def test_cors_legitimate_origins_allowed():
    """Legitimate origins must be allowed."""
    valid_origins = [
        "https://kinochi-project-alpha.vercel.app",
        "https://kinochi-admin.vercel.app",
        "https://kinochi.uz",
        "https://admin.kinochi.uz",
        "https://kinochi-project-alpha-git-main-xojadev.vercel.app",
        "https://kinochi-project-alpha-a1b2c3d4e.vercel.app",
    ]
    for origin in valid_origins:
        assert is_origin_allowed(origin), f"Legitimate origin {origin} was blocked!"
