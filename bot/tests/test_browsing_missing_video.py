import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import CallbackQuery, User, Message, Chat
from handlers.browsing import handle_watch_movie, handle_watch_episode

@pytest.mark.asyncio
async def test_watch_movie_missing_video_shows_truthful_message():
    """GUEST-ISSUE-004: When a movie has no video translations, the bot must NOT say
    'Video yuklanmoqda...', but truthfully state that the video file is not yet uploaded.
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
    callback.data = "watch_m_AVTR01"
    callback.answer = AsyncMock()

    # Movie exists in catalog, but translations list is empty (no video uploaded)
    mock_movie = {
        "id": 1,
        "title": "Avatar 3",
        "code": "AVTR01",
        "translations": []
    }

    with patch("handlers.browsing.api_client.get_movie_by_code", AsyncMock(return_value=mock_movie)):
        await handle_watch_movie(callback)

    # Must NOT display fake loading promise
    for call_args in mock_message.answer.call_args_list:
        assert "Video yuklanmoqda" not in call_args[0][0], "Fake video loading message was sent!"

    # Must display honest missing video message
    mock_message.answer.assert_called_with("⚠️ Ushbu film uchun video fayl hali yuklanmagan.")


@pytest.mark.asyncio
async def test_watch_episode_missing_video_shows_truthful_message():
    """GUEST-ISSUE-004: When an episode has no video translations, the bot must NOT say
    'Video yuklanmoqda...', but truthfully state that the video file is not yet uploaded.
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
    callback.data = "watch_e_EP001"
    callback.answer = AsyncMock()

    # Episode exists, but translations list is empty
    mock_episode = {
        "id": 10,
        "series_id": 2,
        "code": "EP001",
        "translations": []
    }

    with patch("handlers.browsing.api_client.get_episode_by_code", AsyncMock(return_value=mock_episode)):
        await handle_watch_episode(callback)

    # Must NOT display fake loading promise
    for call_args in mock_message.answer.call_args_list:
        assert "Video yuklanmoqda" not in call_args[0][0], "Fake video loading message was sent!"

    # Must display honest missing video message
    mock_message.answer.assert_called_with("⚠️ Ushbu qism uchun video fayl hali yuklanmagan.")
