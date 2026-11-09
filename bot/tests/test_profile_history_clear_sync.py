import pytest
from unittest.mock import AsyncMock, MagicMock
from handlers.profile import render_user_profile, handle_confirm_clear_history
from aiogram.types import CallbackQuery, User, Message


@pytest.mark.asyncio
async def test_render_profile_shows_clear_history_when_watched_positive(monkeypatch):
    """Profile includes 'Tarixni tozalash' button when total_watched > 0."""
    mock_summary = {
        "user": {"id": 1, "telegram_id": 12345, "first_name": "Test", "username": "tester"},
        "total_watched": 5,
        "recent_history": [{"title": "Inception"}],
        "achievements": [],
        "subscriptions": [],
        "collection_subscriptions": []
    }
    mock_api = AsyncMock()
    mock_api.get_user_summary.return_value = mock_summary
    mock_api.register_user.return_value = {}
    mock_api.generate_login_token.return_value = None
    monkeypatch.setattr("handlers.profile.api_client", mock_api)

    text, markup = await render_user_profile(user_id=12345, first_name="Test", username="tester")

    assert "Tomosha faolligi:" in text
    buttons = [btn.callback_data for row in markup.inline_keyboard for btn in row]
    assert "ask_clear_history" in buttons


@pytest.mark.asyncio
async def test_confirm_clear_history_invokes_api_client(monkeypatch):
    """Confirm clear history callback calls api_client.clear_user_history."""
    mock_api = AsyncMock()
    mock_api.clear_user_history.return_value = True
    mock_api.get_user_summary.return_value = {
        "user": {"id": 1, "telegram_id": 12345, "first_name": "Test", "username": "tester"},
        "total_watched": 0,
        "recent_history": [],
        "achievements": [],
        "subscriptions": [],
        "collection_subscriptions": []
    }
    mock_api.register_user.return_value = {}
    mock_api.generate_login_token.return_value = None
    monkeypatch.setattr("handlers.profile.api_client", mock_api)

    user = MagicMock(spec=User)
    user.id = 12345
    user.first_name = "Test"
    user.username = "tester"

    msg = MagicMock(spec=Message)
    msg.edit_text = AsyncMock()

    callback = MagicMock(spec=CallbackQuery)
    callback.from_user = user
    callback.data = "confirm_clear_history"
    callback.message = msg
    callback.answer = AsyncMock()

    await handle_confirm_clear_history(callback)

    mock_api.clear_user_history.assert_called_once_with(12345)
    callback.answer.assert_called_once()
    assert "tozalandi" in callback.answer.call_args[0][0]
    msg.edit_text.assert_called_once()
