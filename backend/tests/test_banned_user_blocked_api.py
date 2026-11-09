import pytest
from httpx import AsyncClient, ASGITransport
import app.main as main_module
from app.infrastructure.security.jwt_handler import create_access_token
from app.api.deps import get_db_session
from app.infrastructure.db.session import Base
from app.infrastructure.db.models.user import UserModel
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_banned_user_is_strictly_blocked_with_403(engine, db_session: AsyncSession):
    """
    BUG-001 Regression Test:
    Banned user with a valid JWT token MUST receive 403 Forbidden on protected endpoints.
    Currently, get_current_user only decodes JWT without checking is_banned in DB.
    """
    fastapi_app = main_module.app
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 1. Create a banned user in the test database
    user = UserModel(
        telegram_id=888999777,
        first_name="Banned",
        last_name="User",
        username="banned_user_test",
        is_banned=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    banned_user_id = user.id

    # 2. Issue valid access token for this user
    token = create_access_token(subject=str(banned_user_id), extra={"telegram_id": 888999777, "role": "user"})

    # 3. Override DB session dependency
    async def override_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db_session] = override_db

    try:
        # 4. Call protected endpoint (e.g. /users/me/subscriptions)
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/users/me/subscriptions",
                headers={"Authorization": f"Bearer {token}"}
            )

            # Assertion: MUST be blocked with 403 Forbidden
            assert response.status_code == 403, (
                f"Expected 403 Forbidden for banned user, got {response.status_code}: {response.text}"
            )
            assert "bloklangan" in response.json().get("detail", "").lower()

            # 5. Create active non-banned user
            active_user = UserModel(
                telegram_id=111222333,
                first_name="Active",
                last_name="User",
                username="active_user_test",
                is_banned=False
            )
            db_session.add(active_user)
            await db_session.commit()
            await db_session.refresh(active_user)

            active_token = create_access_token(
                subject=str(active_user.id),
                extra={"telegram_id": 111222333, "role": "user"}
            )
            active_response = await client.get(
                "/api/v1/users/me/subscriptions",
                headers={"Authorization": f"Bearer {active_token}"}
            )
            assert active_response.status_code == 200, (
                f"Expected 200 OK for active user, got {active_response.status_code}: {active_response.text}"
            )
    finally:
        fastapi_app.dependency_overrides.pop(get_db_session, None)
