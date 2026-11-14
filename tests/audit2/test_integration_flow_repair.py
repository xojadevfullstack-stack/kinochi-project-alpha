import os
import sys
import pytest
from contextlib import asynccontextmanager
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("bot"))

from app.main import app
from app.core.config import settings
from app.infrastructure.db.session import Base
from app.infrastructure.db.models.user import UserModel
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel
from app.api.deps import get_db_session
from utils.code_resolver import clean_and_extract_code


@asynccontextmanager
async def create_integration_client():
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db

    # Pre-populate sample movie and series
    async with session_factory() as session:
        movie = MovieModel(id=1, code="PT3BQB", title="Test Movie", publish_status="published")
        series = SeriesModel(id=30, title="Test Series", publish_status="published")
        session.add_all([movie, series])
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, session_factory

    app.dependency_overrides.pop(get_db_session, None)
    await test_engine.dispose()


@pytest.mark.asyncio
async def test_integration_bot_backend_secret_gate():
    """Verify that bot-only endpoints enforce X-Bot-Secret and reject unauthenticated requests."""
    async with create_integration_client() as (client, session_factory):
        # 1. Missing header -> 403 or 422
        resp = await client.post("/api/v1/users/register", json={"telegram_id": 12345})
        assert resp.status_code in (401, 403, 422)

        # 2. Invalid header -> 403
        resp = await client.post(
            "/api/v1/users/register",
            json={"telegram_id": 12345},
            headers={"X-Bot-Secret": "invalid_secret_token"}
        )
        assert resp.status_code == 403

        # 3. Valid header -> succeeds
        resp = await client.post(
            "/api/v1/users/register",
            json={"telegram_id": 9999991, "first_name": "IntegrationTestUser"},
            headers={"X-Bot-Secret": settings.BOT_API_SECRET}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["telegram_id"] == 9999991


@pytest.mark.asyncio
async def test_integration_magic_login_handshake():
    """Verify full magic login lifecycle: Bot requests token -> User visits web with ?auth_token= -> Backend authenticates."""
    async with create_integration_client() as (client, session_factory):
        # Step 1: Register user first via bot client
        await client.post(
            "/api/v1/users/register",
            json={"telegram_id": 8888881, "first_name": "MagicLoginUser"},
            headers={"X-Bot-Secret": settings.BOT_API_SECRET}
        )

        # Step 2: Bot calls /auth/bot-login
        resp = await client.post(
            "/api/v1/auth/bot-login",
            json={"telegram_id": 8888881, "first_name": "MagicLoginUser"},
            headers={"X-Bot-Secret": settings.BOT_API_SECRET}
        )
        assert resp.status_code == 200
        auth_data = resp.json()
        access_token = auth_data.get("access_token")
        assert access_token is not None
        assert len(access_token) > 20

        # Step 3: Web client receives ?auth_token= and calls /users/me
        me_resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert me_resp.status_code == 200
        user_info = me_resp.json()
        assert user_info["telegram_id"] == 8888881
        assert user_info["first_name"] == "MagicLoginUser"


def test_integration_web_to_bot_deeplinks():
    """Verify that all deep-link formats emitted by website components are correctly parsed by bot code resolver."""
    # 1. Movie deep link: m_PT3BQB or PT3BQB
    code, c_type = clean_and_extract_code("m_PT3BQB")
    assert code == "PT3BQB"
    assert c_type == "movie"

    code, c_type = clean_and_extract_code("movie_FEPB6U")
    assert code == "FEPB6U"
    assert c_type == "movie"

    # 2. Series deep link: s_30 or series_30
    code, c_type = clean_and_extract_code("s_30")
    assert code == "30"
    assert c_type == "series"

    code, c_type = clean_and_extract_code("series_105")
    assert code == "105"
    assert c_type == "series"

    # 3. Episode deep link: ep_28831337 or episode_123
    code, c_type = clean_and_extract_code("ep_28831337")
    assert code == "28831337"
    assert c_type == "episode"

    # 4. Collection deep link: col_5 or franchise_5
    code, c_type = clean_and_extract_code("col_5")
    assert code == "5"
    assert c_type == "collection"

    code, c_type = clean_and_extract_code("franchise_12")
    assert code == "12"
    assert c_type == "collection"

    # 5. Compound episode code: s_1007_s1_ep1
    code, c_type = clean_and_extract_code("s_1007_s1_ep1")
    assert c_type == "episode"


@pytest.mark.asyncio
async def test_integration_report_submission_contract():
    """Verify that issue reports from bot and web (FormData/urlencoded) are properly received and created."""
    async with create_integration_client() as (client, session_factory):
        payload = {
            "media_type": "movie",
            "issue_type": "boshqa",
            "movie_id": "1",
            "description": "Integration test report: audio issue",
            "telegram_user_id": "8888881",
        }
        resp = await client.post("/api/v1/reports", data=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "success"
        assert "report_id" in data


@pytest.mark.asyncio
async def test_integration_content_request_submission():
    """Verify that content requests from web or bot API are accepted by backend."""
    async with create_integration_client() as (client, session_factory):
        payload = {
            "title": "Inception 2",
            "media_type": "movie",
            "release_year": 2026,
            "preferred_language": "uz",
            "telegram_user_id": 8888881,
            "user_contact": "@kinochi_user"
        }
        resp = await client.post("/api/v1/content-requests", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert data["is_new"] is True
        assert "request_id" in data
