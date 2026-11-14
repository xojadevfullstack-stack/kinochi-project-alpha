import pytest
from httpx import AsyncClient, ASGITransport
import app.main as main_module
from app.api.deps import get_current_admin, get_db_session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.infrastructure.db.session import Base

@pytest.mark.asyncio
async def test_admin_issue_002_sources_no_307_redirect_on_get_and_post():
    """ADMIN-ISSUE-002: GET and POST /api/v1/sources must NOT return HTTP 307 redirect.
    It should directly match without trailing slash inconsistency.
    """
    app = main_module.app
    
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    test_sessionmaker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with test_sessionmaker() as session:
            yield session

    async def override_get_current_admin():
        return {"id": 1, "email": "admin@kinochi.uz", "role": "superadmin"}

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_current_admin] = override_get_current_admin

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # Test GET /api/v1/sources (without trailing slash) with follow_redirects=False
            resp_get = await ac.get("/api/v1/sources", follow_redirects=False)
            assert resp_get.status_code != 307, (
                f"GET /api/v1/sources returned HTTP 307 Redirect to {resp_get.headers.get('location')}! "
                "Must return 200 directly without trailing slash."
            )
            assert resp_get.status_code == 200

            # Test POST /api/v1/sources (without trailing slash) with follow_redirects=False
            payload = {
                "name": "Test Source",
                "chat_id": -100123456789,
                "topic_id": 1,
                "type": "superguruh"
            }
            resp_post = await ac.post("/api/v1/sources", json=payload, follow_redirects=False)
            assert resp_post.status_code != 307, (
                f"POST /api/v1/sources returned HTTP 307 Redirect to {resp_post.headers.get('location')}! "
                "Must handle POST directly without 307 redirect."
            )
            assert resp_post.status_code == 200 or resp_post.status_code == 201
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        app.dependency_overrides.pop(get_current_admin, None)
        await test_engine.dispose()
