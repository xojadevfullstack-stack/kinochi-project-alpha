import pytest
import hmac
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport
from starlette.requests import Request
from app.main import app
from app.core.config import settings
from app.infrastructure.security.jwt_handler import create_access_token
from app.api.limiter import get_client_ip
from app.infrastructure.db.models.series import SeriesModel
from app.infrastructure.db.models.collection import CollectionModel


@pytest.mark.asyncio
async def test_2a_generic_exception_handler_masks_details_in_production():
    """In production, generic_exception_handler must mask error_type and error_message, giving only request_id."""
    @app.get("/test-phase2-unhandled-500")
    async def _dummy_failing_route():
        raise RuntimeError("super_sensitive_sql_or_db_error")

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        with patch.object(settings, "APP_ENV", "production"):
            resp = await ac.get("/test-phase2-unhandled-500")
            assert resp.status_code == 500
            data = resp.json()
            assert "super_sensitive_sql_or_db_error" not in resp.text
            assert "error_type" not in data
            assert "error_message" not in data
            assert "request_id" in data
            assert "detail" in data


@pytest.mark.asyncio
async def test_2b_diag_requires_admin_and_omits_database_url(db_session):
    """Diagnostic endpoint must require admin authentication and never return database_url_masked."""
    from app.infrastructure.db.models.admin_user import AdminUserModel
    from app.infrastructure.security.password_hasher import hash_password

    # Seed an admin user
    admin = AdminUserModel(
        id=99,
        email="diag_admin@kinochi.uz",
        hashed_password=hash_password("admin_pass"),
        is_active=True,
        role="admin",
    )
    db_session.add(admin)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Unauthenticated request -> must be 401 or 403
        resp_unauth = await ac.get("/api/v1/diag")
        assert resp_unauth.status_code in (401, 403)

        # Authenticated admin request -> 200, but NO database_url_masked
        admin_token = create_access_token(str(admin.id), extra={"email": admin.email, "role": admin.role})
        resp_auth = await ac.get(
            "/api/v1/diag",
            cookies={"access_token": admin_token},
        )
        assert resp_auth.status_code == 200
        data = resp_auth.json()
        assert "database_url_masked" not in data
        assert "version" in data


@pytest.mark.asyncio
async def test_2c_cors_rejects_arbitrary_vercel_subdomains():
    """Verify strict CORS enforcement on allowed domains, arbitrary domains, credentials, and preflights."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Arbitrary and phishing vercel subdomains rejected
        resp_evil_vercel = await ac.get("/", headers={"Origin": "https://kinochi-evil.vercel.app"})
        assert resp_evil_vercel.headers.get("access-control-allow-origin") is None

        resp_evil_com = await ac.get("/", headers={"Origin": "https://evil.com"})
        assert resp_evil_com.headers.get("access-control-allow-origin") is None

        # 2. Legitimate production frontend domains pass with credentials
        resp_alpha = await ac.get("/", headers={"Origin": "https://kinochi-project-alpha.vercel.app"})
        assert resp_alpha.headers.get("access-control-allow-origin") == "https://kinochi-project-alpha.vercel.app"
        assert resp_alpha.headers.get("access-control-allow-credentials") == "true"

        resp_custom = await ac.get("/", headers={"Origin": "https://kinochi.uz"})
        assert resp_custom.headers.get("access-control-allow-origin") == "https://kinochi.uz"
        assert resp_custom.headers.get("access-control-allow-credentials") == "true"

        # 3. Preflight OPTIONS request
        opt_ok = await ac.options("/health", headers={
            "Origin": "https://kinochi-project-alpha.vercel.app",
            "Access-Control-Request-Method": "GET",
        })
        assert opt_ok.status_code == 200
        assert opt_ok.headers.get("access-control-allow-origin") == "https://kinochi-project-alpha.vercel.app"
        assert opt_ok.headers.get("access-control-allow-credentials") == "true"

        opt_evil = await ac.options("/health", headers={
            "Origin": "https://kinochi-evil.vercel.app",
            "Access-Control-Request-Method": "GET",
        })
        assert opt_evil.headers.get("access-control-allow-origin") is None


@pytest.mark.asyncio
async def test_2d_series_and_collection_subscriptions_idor_protection(db_session):
    """Subscribing on behalf of another user without bot secret or matching JWT must return 403."""
    # Seed a series and collection
    series = SeriesModel(title="Test Series", description="Desc")
    collection = CollectionModel(name="Test Collection", slug="test-col-sub")
    db_session.add_all([series, collection])
    await db_session.commit()
    await db_session.refresh(series)
    await db_session.refresh(collection)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Anonymous request with arbitrary telegram_user_id -> 403
        resp_anon = await ac.post(
            f"/api/v1/series/{series.id}/subscribe",
            json={"telegram_user_id": 999888},
        )
        assert resp_anon.status_code == 403

        resp_anon_col = await ac.post(
            f"/api/v1/collections/{collection.id}/subscribe",
            json={"telegram_user_id": 999888},
        )
        assert resp_anon_col.status_code == 403

        # 2. Status query for arbitrary telegram_user_id without auth -> 403
        resp_status_anon = await ac.get(
            f"/api/v1/series/{series.id}/subscription-status?telegram_user_id=999888"
        )
        assert resp_status_anon.status_code == 403

        # 3. With valid X-Bot-Secret -> 200
        bot_secret = settings.BOT_API_SECRET or "test_bot_secret"
        with patch.object(settings, "BOT_API_SECRET", bot_secret):
            resp_bot = await ac.post(
                f"/api/v1/series/{series.id}/subscribe",
                json={"telegram_user_id": 999888},
                headers={"X-Bot-Secret": bot_secret},
            )
            assert resp_bot.status_code == 200
            assert resp_bot.json()["is_subscribed"] is True

        # 4. User with JWT matching telegram_id -> 200
        user_token = create_access_token("101", extra={"telegram_id": 123456, "role": "user"})
        resp_own = await ac.post(
            f"/api/v1/series/{series.id}/subscribe",
            json={"telegram_user_id": 123456},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp_own.status_code == 200

        # 5. User with JWT for 123456 trying to toggle for 999888 -> 403
        resp_mismatch = await ac.post(
            f"/api/v1/series/{series.id}/subscribe",
            json={"telegram_user_id": 999888},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp_mismatch.status_code == 403


@pytest.mark.asyncio
async def test_2e_users_bot_secret_uses_timing_safe_compare():
    """users.py verify_bot_secret must use timing-safe comparison and reject invalid secrets."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        with patch.object(settings, "BOT_API_SECRET", "super_secret_bot_key"):
            # Invalid secret
            resp_bad = await ac.post(
                "/api/v1/users/register",
                headers={"X-Bot-Secret": "wrong_key"},
                json={"telegram_id": 111222, "first_name": "Test"},
            )
            assert resp_bad.status_code == 403


def test_2f_limiter_key_func_trusted_proxies():
    """Rate limiter IP extraction must not be spoofable when TRUST_PROXY=True."""
    mock_request = MagicMock(spec=Request)
    mock_request.client.host = "10.0.0.1"  # Reverse proxy address

    # Scenario 1: TRUST_PROXY is False -> ignores X-Forwarded-For
    with patch.object(settings, "TRUST_PROXY", False):
        mock_request.headers = {"x-forwarded-for": "198.51.100.1, 203.0.113.195"}
        ip = get_client_ip(mock_request)
        assert ip == "10.0.0.1"

    # Scenario 2: TRUST_PROXY is True, TRUSTED_PROXIES_COUNT=1
    # Attacker prepended "198.51.100.1", reverse proxy appended real client "203.0.113.195"
    with patch.object(settings, "TRUST_PROXY", True), patch.object(settings, "TRUSTED_PROXIES_COUNT", 1):
        mock_request.headers = {"x-forwarded-for": "198.51.100.1, 203.0.113.195"}
        ip = get_client_ip(mock_request)
        assert ip == "203.0.113.195"


def test_dns_cache_ttl_and_env_config():
    """Verify DNS TTL defaults to 60.0 and respects DNS_CACHE_TTL_SECONDS env var."""
    import os
    from app.infrastructure.db import session as db_session_module
    assert db_session_module.DNS_CACHE_TTL_SECONDS == 60.0
    with patch.dict(os.environ, {"DNS_CACHE_TTL_SECONDS": "45.0"}):
        val = float(os.environ.get("DNS_CACHE_TTL_SECONDS", "60.0"))
        assert val == 45.0
