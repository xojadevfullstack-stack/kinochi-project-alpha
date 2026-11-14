import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import CallbackQuery, User, Message, Chat
from handlers.browsing import handle_watch_episode

@pytest.mark.asyncio
async def test_watch_episode_not_found_shows_uploading_or_helpful_message():
    """When an episode returns 404/None because it was just posted or is uploading,
    the bot should give a helpful retry/uploading notice instead of a dry 'Bu qism topilmadi'.
    """
    mock_bot = AsyncMock()
    mock_user = User(id=12345, is_bot=False, first_name="TestUser")
    mock_chat = Chat(id=12345, type="private")
    mock_message = MagicMock(spec=Message)
    mock_message.chat = mock_chat
    mock_message.answer = AsyncMock()

    callback = MagicMock(spec=CallbackQuery)
    callback.bot = mock_bot
    callback.from_user = mock_user
    callback.message = mock_message
    callback.data = "watch_e_NEW_EP_99"
    callback.answer = AsyncMock()

    # Episode API returns None (404 on Render because newly created or series pending)
    with patch("handlers.browsing.api_client.get_episode_by_code", AsyncMock(return_value=None)):
        await handle_watch_episode(callback)

    # Must provide informative message
    assert mock_message.answer.called
    sent_text = mock_message.answer.call_args[0][0]
    assert "yuklanmoqda" in sent_text or "mavjud emas" in sent_text
