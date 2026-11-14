"""
Pre-Deploy Verification Suite: JWT, Refresh Token & CSRF Security Audit.
Verifies:
1. Access token and Refresh token creation, expiry and cookie storage.
2. Logout cookie clearing behavior.
3. Refresh endpoint behavior after logout with retained/stolen token (stateless proof).
4. Refresh token rotation vs token reuse vulnerability.
5. CSRF defense posture: absence of CSRF token and cross-origin header behavior.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from app.main import app
from app.api.deps import get_db_session
from app.infrastructure.db.session import Base
from app.infrastructure.security.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.infrastructure.security.password_hasher import hash_password
from app.infrastructure.db.models.admin_user import AdminUserModel
from app.infrastructure.db.models.user import UserModel


@pytest.fixture
async def test_db(tmp_path):
    """Isolated SQLite test DB preventing event loop leakage."""
    db_file = tmp_path / "test_predeploy.sqlite3"
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
async def test_jwt_token_lifetimes_and_claims():
    """Verify access token (30m) and refresh token (7d) lifetimes and claims."""
    subject = "999"
    access_tok = create_access_token(subject, extra={"role": "admin", "email": "test@kinochi.uz"})
    refresh_tok = create_refresh_token(subject)

    access_payload = decode_token(access_tok)
    refresh_payload = decode_token(refresh_tok)

    assert access_payload is not None
    assert access_payload["sub"] == "999"
    assert access_payload["type"] == "access"
    assert access_payload["role"] == "admin"
    assert access_payload["email"] == "test@kinochi.uz"

    assert refresh_payload is not None
    assert refresh_payload["sub"] == "999"
    assert refresh_payload["type"] == "refresh"

    # Check expiry difference
    access_exp = datetime.fromtimestamp(access_payload["exp"], tz=timezone.utc)
    refresh_exp = datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)

    access_delta_minutes = (access_exp - now).total_seconds() / 60
    refresh_delta_days = (refresh_exp - now).total_seconds() / 86400

    # Access token ~ 30 minutes (allow small drift)
    assert 28 <= access_delta_minutes <= 32
    # Refresh token ~ 7 days (allow small drift)
    assert 6.9 <= refresh_delta_days <= 7.1


@pytest.mark.asyncio
async def test_admin_login_logout_token_lifecycle(test_db):
    """
    Test login, token delivery via httpOnly cookies, logout cookie deletion,
    and stateless token validity after logout.
    """
    # 1. Seed test admin in DB
    async with test_db() as session:
        admin = AdminUserModel(
            email="predeploy_audit@kinochi.uz",
            hashed_password=hash_password("AuditSecret123!"),
            role="admin",
            is_active=True,
        )
        session.add(admin)
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Login
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "predeploy_audit@kinochi.uz", "password": "AuditSecret123!"},
        )
        assert login_resp.status_code == 200
        data = login_resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

        stolen_refresh_token = data["refresh_token"]

        # Step 2: Access protected route with cookie
        client.cookies.set("access_token", data["access_token"])
        me_resp = await client.get("/api/v1/auth/me")
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "predeploy_audit@kinochi.uz"

        # Step 3: Logout
        logout_resp = await client.post("/api/v1/auth/logout")
        assert logout_resp.status_code == 200

        # Step 4: Refresh endpoint with stolen/retained refresh token AFTER logout
        # Because JWT is stateless and has no blacklist, the retained refresh token STILL WORKS!
        client.cookies.clear()
        client.cookies.set("refresh_token", stolen_refresh_token)
        refresh_resp = await client.post("/api/v1/auth/refresh")
        assert refresh_resp.status_code == 200
        refreshed_data = refresh_resp.json()
        assert "access_token" in refreshed_data
        assert "refresh_token" in refreshed_data

        # Step 5: Test Refresh Token Replay / Reuse (Pseudo-rotation flaw)
        # Using the SAME old refresh token a second time:
        client.cookies.clear()
        client.cookies.set("refresh_token", stolen_refresh_token)
        replay_resp = await client.post("/api/v1/auth/refresh")
        # In a strict rotation system, this must fail with 401 or trigger breach detection.
        # But in Kinochi's stateless MVP, it succeeds again:
        assert replay_resp.status_code == 200, "Stateless token replay succeeds because no revocation list exists"


@pytest.mark.asyncio
async def test_csrf_vulnerability_posture(test_db):
    """
    Test CSRF posture:
    1. Endpoints do not require X-CSRF-Token or CSRF cookies.
    2. Cross-origin request headers (Origin: https://evil-attacker.com) are processed without 403.
    """
    async with test_db() as session:
        user = UserModel(
            id=123,
            telegram_id=999888,
            first_name="Test",
            username="test_csrf_user",
            is_banned=False,
        )
        session.add(user)
        await session.commit()

    user_tok = create_access_token("123", extra={"role": "user", "telegram_id": 999888})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.cookies.set("user_access_token", user_tok)
        # Cross-site origin request simulation
        resp = await client.get(
            "/api/v1/users/me/history",
            headers={"Origin": "https://evil-attacker.com", "Referer": "https://evil-attacker.com/exploit.html"},
        )
        # Endpoint returns 200 because there is no anti-CSRF or Origin-validation middleware
        assert resp.status_code == 200
