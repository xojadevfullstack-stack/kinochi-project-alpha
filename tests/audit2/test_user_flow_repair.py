import pytest
from httpx import AsyncClient, ASGITransport
import app.main as main_module

@pytest.mark.asyncio
async def test_user_issue_001_logout_clears_user_access_token_cookie():
    """USER-ISSUE-001: POST /api/v1/auth/logout must clear user_access_token cookie
    so that browser session does not persist after logout.
    """
    app = main_module.app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # User has an active user_access_token cookie, logging out from trusted website origin
        ac.cookies.set("user_access_token", "fake_user_jwt_token")
        resp = await ac.post("/api/v1/auth/logout", headers={"Origin": "https://kinochi.uz"})
        assert resp.status_code == 200

        # Assert user_access_token cookie was instructed to be deleted (Max-Age=0 or absent)
        cookie_header = resp.headers.get_list("set-cookie")
        user_cookie_deleted = any("user_access_token" in c and ('Max-Age=0' in c or 'expires=' in c.lower()) for c in cookie_header)
        assert user_cookie_deleted, (
            f"user_access_token cookie was NOT cleared on logout! Set-Cookie headers: {cookie_header}"
        )


@pytest.mark.asyncio
async def test_user_issue_002_history_total_count_accuracy():
    """USER-ISSUE-002: GET /api/v1/users/me/history must return accurate total count
    independent of pagination limit (not hardcoded len(items)).
    """
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.infrastructure.db.session import Base
    from app.infrastructure.db.models.user import UserModel
    from app.infrastructure.db.models.movie import MovieModel
    from app.infrastructure.db.models.watch_history import WatchHistoryModel
    from app.api.deps import get_db_session, get_current_user

    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        user = UserModel(telegram_id=987654321, first_name="HistoryUser")
        session.add(user)
        await session.flush()

        # Seed 3 movies and 3 watch history records
        for i in range(1, 4):
            movie = MovieModel(title=f"Movie {i}", code=f"M{i}", publish_status="published")
            session.add(movie)
            await session.flush()
            session.add(WatchHistoryModel(user_id=user.id, movie_id=movie.id, status="completed"))
        await session.commit()
        user_id = user.id

    async def override_db():
        async with session_factory() as session:
            yield session

    async def override_user():
        return {"user_id": user_id, "telegram_id": 987654321, "role": "user"}

    app = main_module.app
    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_current_user] = override_user

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # Request only 1 item per page
            resp = await ac.get("/api/v1/users/me/history?skip=0&limit=1")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["items"]) == 1
            # Before fix: returns total=1 (len(items)).
            # After fix: returns total=3 (actual count of history records for this user).
            assert data["total"] == 3, f"Expected total=3, but got {data['total']}"
    finally:
        app.dependency_overrides.clear()
        await test_engine.dispose()

