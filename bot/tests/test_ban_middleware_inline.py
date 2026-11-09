import sys
from unittest.mock import AsyncMock, patch, MagicMock
import pytest

# Ensure mocks for backend modules not available in bot venv
sys.modules.setdefault("app", MagicMock())
sys.modules.setdefault("app.core", MagicMock())
sys.modules.setdefault("app.core.reviews", MagicMock())
sys.modules.setdefault("app.core.watch_history", MagicMock())

from aiogram.types import InlineQuery, User
from middlewares.ban_check import BanCheckMiddleware
from services.api_client import api_client

@pytest.mark.asyncio
async def test_ban_middleware_blocks_inline_query():
    """
    BUG-007 Regression Test:
    Banned user performing an inline query MUST be intercepted by BanCheckMiddleware
    and the downstream handler MUST NOT be executed.
    """
    middleware = BanCheckMiddleware()
    event = MagicMock(spec=InlineQuery)
    event.from_user = MagicMock(spec=User)
    event.from_user.id = 777666
    event.answer = AsyncMock()

    handler = AsyncMock()

    with patch.object(api_client, "check_user_banned", new_callable=AsyncMock) as mock_check:
        mock_check.return_value = True

        result = await middleware(handler, event, {})

        assert result is None
        handler.assert_not_called()
        event.answer.assert_awaited_once()
        kwargs = event.answer.call_args[1]
        assert kwargs.get("results") == []
        assert "bloklangan" in kwargs.get("switch_pm_text", "").lower()

@pytest.mark.asyncio
async def test_ban_check_stale_while_error_policy():
    """
    BUG-007 Decision Test:
    When a user was previously known to be banned, even if TTL expired,
    if backend fails (returns None or raises error), user MUST remain banned.
    """
    tg_id = 999111
    # Seed cache as banned but with an expired timestamp in the past
    api_client._ban_cache[tg_id] = (True, 0.0)

    with patch.object(api_client, "get_user_summary", new_callable=AsyncMock) as mock_summary:
        mock_summary.return_value = None  # Backend is down

        is_banned = await api_client.check_user_banned(tg_id)
        assert is_banned is True, "Stale banned user was incorrectly unbanned during backend outage!"

    # Clean up
    api_client.invalidate_ban_cache(tg_id)
