import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, CallbackQuery, User
from middlewares.ban_check import BanCheckMiddleware


@pytest.mark.asyncio
async def test_ban_middleware_blocks_banned_user_message(monkeypatch):
    """When user is banned, BanCheckMiddleware prevents handler execution on Message."""
    mock_api = AsyncMock()
    mock_api.check_user_banned.return_value = True
    monkeypatch.setattr("middlewares.ban_check.api_client", mock_api)

    middleware = BanCheckMiddleware()
    mock_handler = AsyncMock()

    user = MagicMock(spec=User)
    user.id = 999
    message = MagicMock(spec=Message)
    message.from_user = user
    message.text = "Salom"
    message.answer = AsyncMock()

    result = await middleware(mock_handler, message, {})

    assert result is None
    mock_handler.assert_not_called()
    message.answer.assert_called_once()
    assert "bloklangan" in message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_ban_middleware_blocks_banned_user_callback(monkeypatch):
    """When user is banned, BanCheckMiddleware prevents handler execution on CallbackQuery."""
    mock_api = AsyncMock()
    mock_api.check_user_banned.return_value = True
    monkeypatch.setattr("middlewares.ban_check.api_client", mock_api)

    middleware = BanCheckMiddleware()
    mock_handler = AsyncMock()

    user = MagicMock(spec=User)
    user.id = 999
    callback = MagicMock(spec=CallbackQuery)
    callback.from_user = user
    callback.data = "menu_catalog"
    callback.answer = AsyncMock()

    result = await middleware(mock_handler, callback, {})

    assert result is None
    mock_handler.assert_not_called()
    callback.answer.assert_called_once()
    assert "bloklangan" in callback.answer.call_args[0][0]
    assert callback.answer.call_args[1].get("show_alert") is True


@pytest.mark.asyncio
async def test_ban_middleware_allows_active_user(monkeypatch):
    """When user is not banned, BanCheckMiddleware passes through to handler."""
    mock_api = AsyncMock()
    mock_api.check_user_banned.return_value = False
    monkeypatch.setattr("middlewares.ban_check.api_client", mock_api)

    middleware = BanCheckMiddleware()
    mock_handler = AsyncMock(return_value="OK")

    user = MagicMock(spec=User)
    user.id = 111
    message = MagicMock(spec=Message)
    message.from_user = user
    message.text = "Katalog"

    result = await middleware(mock_handler, message, {})

    assert result == "OK"
    mock_handler.assert_called_once_with(message, {})
