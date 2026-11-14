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
        # User has an active user_access_token cookie
        ac.cookies.set("user_access_token", "fake_user_jwt_token")
        resp = await ac.post("/api/v1/auth/logout")
        assert resp.status_code == 200

        # Assert user_access_token cookie was instructed to be deleted (Max-Age=0 or absent)
        cookie_header = resp.headers.get_list("set-cookie")
        user_cookie_deleted = any("user_access_token" in c and ('Max-Age=0' in c or 'expires=' in c.lower()) for c in cookie_header)
        assert user_cookie_deleted, (
            f"user_access_token cookie was NOT cleared on logout! Set-Cookie headers: {cookie_header}"
        )
