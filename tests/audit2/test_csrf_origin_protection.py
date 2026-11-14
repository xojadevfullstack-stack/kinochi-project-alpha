"""
CSRF Security Suite: Origin & Referer Verification Testing.
Tests:
1. Safe HTTP Methods (GET, OPTIONS) -> Allowed regardless of Origin
2. Untrusted Origin on state-changing request -> Rejected (403 Forbidden)
3. Trusted Origin -> Allowed
4. Missing Origin:
   - With auth cookie and no Referer -> Rejected (403 Forbidden)
   - With auth cookie and untrusted Referer -> Rejected (403 Forbidden)
   - With auth cookie and trusted Referer -> Allowed (not 403)
5. Server-to-server / Bot (X-Bot-Secret, no cookies, no Origin) -> Allowed
6. Admin cookie authentication with Origin check
7. User cookie authentication with Origin check
8. Auth endpoints (Login, Refresh, Logout) Origin enforcement
"""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.main import app
from app.api.deps import get_db_session
from app.infrastructure.db.session import Base
from app.infrastructure.security.jwt_handler import create_access_token, create_refresh_token
from app.infrastructure.security.password_hasher import hash_password
from app.infrastructure.db.models.admin_user import AdminUserModel
from app.infrastructure.db.models.user import UserModel
from app.core.config import settings


@pytest.fixture
async def test_db(tmp_path):
    """Isolated SQLite test DB preventing event loop leakage."""
    db_file = tmp_path / "test_csrf.sqlite3"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_file}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db_session():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db_session] = override_get_db_session

    yield session_factory

    app.dependency_overrides.pop(get_db_session, None)
    await engine.dispose()


@pytest.mark.asyncio
async def test_csrf_safe_methods_unrestricted():
    """1. GET and OPTIONS safe methods must never be blocked by CSRF origin checks."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # GET with evil origin
        resp_get = await client.get("/api/v1/movies", headers={"Origin": "https://evil-attacker.com"})
        assert resp_get.status_code == 200

        # CORS preflight OPTIONS with evil origin
        resp_options = await client.options(
            "/api/v1/movies",
            headers={"Origin": "https://evil-attacker.com", "Access-Control-Request-Method": "GET"},
        )
        assert resp_options.status_code in (200, 204, 400)


@pytest.mark.asyncio
async def test_csrf_untrusted_origin_rejected_on_post():
    """2. Untrusted Origin on state-changing POST must receive 403 Forbidden."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/logout",
            headers={"Origin": "https://evil-attacker.com"},
        )
        assert resp.status_code == 403
        assert "CSRF" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_csrf_trusted_origin_allowed(test_db):
    """3. Trusted Origin from CORS configuration must be allowed."""
    async with test_db() as session:
        admin = AdminUserModel(
            email="csrf_admin@kinochi.uz",
            hashed_password=hash_password("Pass123!"),
            role="admin",
            is_active=True,
        )
        session.add(admin)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Trusted frontend origin: https://kinochi-project-alpha.vercel.app
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "csrf_admin@kinochi.uz", "password": "Pass123!"},
            headers={"Origin": "https://kinochi-project-alpha.vercel.app"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

        # Vercel deployment preview origin: https://kinochi-project-alpha-qoqf.vercel.app
        resp_preview = await client.post(
            "/api/v1/auth/login",
            json={"email": "csrf_admin@kinochi.uz", "password": "Pass123!"},
            headers={"Origin": "https://kinochi-project-alpha-qoqf.vercel.app"},
        )
        assert resp_preview.status_code == 200
        assert "access_token" in resp_preview.json()


@pytest.mark.asyncio
async def test_csrf_missing_origin_cookie_auth_handling(test_db):
    """
    4. Missing Origin handling:
    - If auth cookies exist and NO Referer -> 403 Forbidden
    - If auth cookies exist and untrusted Referer -> 403 Forbidden
    - If auth cookies exist and trusted Referer -> Allowed (not 403)
    """
    async with test_db() as session:
        user = UserModel(
            id=456,
            telegram_id=456789,
            first_name="CsrfUser",
            username="csrf_user",
            is_banned=False,
        )
        session.add(user)
        await session.commit()

    user_token = create_access_token("456", extra={"role": "user", "telegram_id": 456789})
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.cookies.set("user_access_token", user_token)

        # 4a. Cookie present, NO Origin, NO Referer -> 403 Forbidden
        resp_no_origin = await client.delete("/api/v1/users/me/history")
        assert resp_no_origin.status_code == 403
        assert "CSRF" in resp_no_origin.json()["detail"]

        # 4b. Cookie present, NO Origin, UNTRUSTED Referer -> 403 Forbidden
        resp_bad_ref = await client.delete(
            "/api/v1/users/me/history",
            headers={"Referer": "https://evil-attacker.com/exploit.html"},
        )
        assert resp_bad_ref.status_code == 403
        assert "CSRF" in resp_bad_ref.json()["detail"]

        # 4c. Cookie present, NO Origin, TRUSTED Referer -> Allowed (204 No Content)
        resp_good_ref = await client.delete(
            "/api/v1/users/me/history",
            headers={"Referer": "https://kinochi-project-alpha.vercel.app/history"},
        )
        assert resp_good_ref.status_code == 204


@pytest.mark.asyncio
async def test_csrf_server_to_server_bot_unrestricted(test_db):
    """5. Telegram Bot requests without cookies (using X-Bot-Secret) must NOT be blocked by CSRF."""
    settings.BOT_API_SECRET = "super-test-bot-secret"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Bot request: no Origin, no cookies, sends X-Bot-Secret
        resp = await client.post(
            "/api/v1/auth/bot-login",
            json={"telegram_id": 998877, "first_name": "BotUser"},
            headers={"X-Bot-Secret": "super-test-bot-secret"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_csrf_admin_cookie_auth_protection(test_db):
    """6. Admin cookie authenticated POST is blocked under untrusted origin."""
    async with test_db() as session:
        admin = AdminUserModel(
            id=10,
            email="admin_csrf_test@kinochi.uz",
            hashed_password=hash_password("AdminPass123!"),
            role="admin",
            is_active=True,
        )
        session.add(admin)
        await session.commit()

    admin_token = create_access_token("10", extra={"role": "admin", "email": "admin_csrf_test@kinochi.uz"})
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.cookies.set("access_token", admin_token)

        # Attacker triggers admin action
        resp = await client.post(
            "/api/v1/admin/cache/flush",
            headers={"Origin": "https://attacker-domain.xyz"},
        )
        assert resp.status_code == 403
        assert "CSRF" in resp.json()["detail"]

        # Legitimate Admin Panel action
        resp_legit = await client.post(
            "/api/v1/admin/cache/flush",
            headers={"Origin": "https://kinochi-admin.vercel.app"},
        )
        assert resp_legit.status_code == 200


@pytest.mark.asyncio
async def test_csrf_refresh_and_logout_endpoints(test_db):
    """7. Refresh and Logout endpoints enforce Origin validation."""
    async with test_db() as session:
        admin = AdminUserModel(
            id=11,
            email="admin_refresh_csrf@kinochi.uz",
            hashed_password=hash_password("Pass123!"),
            role="admin",
            is_active=True,
        )
        session.add(admin)
        await session.commit()

    admin_refresh = create_refresh_token("11")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.cookies.set("refresh_token", admin_refresh)

        # Attacker tries to refresh tokens
        resp_bad_refresh = await client.post(
            "/api/v1/auth/refresh",
            headers={"Origin": "https://evil.com"},
        )
        assert resp_bad_refresh.status_code == 403
        assert "CSRF" in resp_bad_refresh.json()["detail"]

        # Trusted origin refreshes tokens
        resp_good_refresh = await client.post(
            "/api/v1/auth/refresh",
            headers={"Origin": "https://kinochi-admin.vercel.app"},
        )
        assert resp_good_refresh.status_code == 200
        assert "access_token" in resp_good_refresh.json()

        # Attacker tries to force logout (Logout CSRF)
        resp_bad_logout = await client.post(
            "/api/v1/auth/logout",
            headers={"Origin": "https://evil.com"},
        )
        assert resp_bad_logout.status_code == 403

        # Legitimate logout from trusted website
        resp_good_logout = await client.post(
            "/api/v1/auth/logout",
            headers={"Origin": "https://kinochi.uz"},
        )
        assert resp_good_logout.status_code == 200
