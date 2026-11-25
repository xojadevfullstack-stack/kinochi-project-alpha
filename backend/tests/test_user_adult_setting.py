import pytest
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.infrastructure.security.jwt_handler import create_access_token
from app.api.limiter import limiter
from app.api.deps import get_db_session, get_user_service
from app.domain.users.entities import User


@pytest.fixture(autouse=True)
def disable_limiter():
    limiter.enabled = False
    yield
    limiter.enabled = True


@pytest.mark.asyncio
async def test_user_me_returns_and_updates_show_adult_content():
    now = datetime.now(timezone.utc)
    stored_user = User(
        id=42,
        telegram_id=999888777,
        username="xoja",
        first_name="Xoja",
        is_admin=False,
        is_banned=False,
        show_adult_content=False,
        joined_at=now,
        last_active_at=now,
    )

    class FakeUserService:
        async def get_by_telegram_id(self, telegram_id: int):
            if telegram_id == stored_user.telegram_id:
                return stored_user
            return None

        async def update_settings(self, telegram_id: int, show_adult_content: bool):
            if telegram_id != stored_user.telegram_id:
                return None
            stored_user.show_adult_content = show_adult_content
            return stored_user

    class FakeExecResult:
        def scalar_one_or_none(self):
            return stored_user

    class FakeSession:
        async def execute(self, *args, **kwargs):
            return FakeExecResult()

    app.dependency_overrides[get_db_session] = lambda: FakeSession()
    app.dependency_overrides[get_user_service] = lambda: FakeUserService()
    token = create_access_token(
        subject=str(stored_user.id),
        extra={"telegram_id": stored_user.telegram_id, "role": "user"},
    )

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. GET /me default false
            res_get = await client.get(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert res_get.status_code == 200
            assert res_get.json()["show_adult_content"] is False

            # 2. PATCH /me/settings -> true
            res_patch = await client.patch(
                "/api/v1/users/me/settings",
                headers={"Authorization": f"Bearer {token}"},
                json={"show_adult_content": True},
            )
            assert res_patch.status_code == 200
            assert res_patch.json()["show_adult_content"] is True

            # 3. Unauthenticated rejected
            res_unauth = await client.patch(
                "/api/v1/users/me/settings",
                json={"show_adult_content": False},
            )
            assert res_unauth.status_code == 401
    finally:
        app.dependency_overrides.clear()
