import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram.types import CallbackQuery, Message, User, Chat
import httpx

from services.api_client import api_client, APIConnectionError
from handlers.browsing import handle_show_season, handle_watch_episode

@pytest.mark.asyncio
async def test_get_series_by_id_timeout_raises_api_connection_error():
    """httpx.TimeoutException yuz berganda get_series_by_id None emas, APIConnectionError chiqarishi shart."""
    with patch.object(api_client.client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Read timed out")
        
        with pytest.raises(APIConnectionError):
            await api_client.get_series_by_id(1024)

@pytest.mark.asyncio
async def test_get_episode_by_code_timeout_raises_api_connection_error():
    """httpx.TimeoutException yuz berganda get_episode_by_code None emas, APIConnectionError chiqarishi shart."""
    with patch.object(api_client.client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Read timed out")
        
        with pytest.raises(APIConnectionError):
            await api_client.get_episode_by_code("VncEACEz")

@pytest.mark.asyncio
async def test_handle_show_season_connection_error_shows_retry_message():
    """APIConnectionError yuz berganda 'Bu serial topilmadi' emas, vaqtinchalik kechikish xabari berilishi kerak."""
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "show_season_1024_1305"
    callback.from_user = MagicMock(spec=User, id=12345)
    callback.message = MagicMock(spec=Message)
    callback.message.message_id = 999
    callback.message.answer = AsyncMock()
    callback.answer = AsyncMock()

    with patch.object(api_client, "get_series_by_id", new_callable=AsyncMock) as mock_get_series:
        mock_get_series.side_effect = APIConnectionError("Timeout")
        
        await handle_show_season(callback)
        
        # 'Bu serial topilmadi' deyilmasligi kerak!
        for call_args in callback.message.answer.call_args_list:
            text = call_args[0][0]
            assert "Bu serial topilmadi" not in text
            assert "kechikish" in text.lower() or "kuting" in text.lower() or "server" in text.lower()

@pytest.mark.asyncio
async def test_handle_watch_episode_connection_error_shows_retry_message():
    """APIConnectionError yuz berganda 'Bu qism topilmadi' emas, vaqtinchalik kechikish xabari berilishi kerak."""
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "watch_e_VncEACEz"
    callback.from_user = MagicMock(spec=User, id=12345)
    callback.message = MagicMock(spec=Message)
    callback.message.message_id = 999
    callback.message.answer = AsyncMock()
    callback.answer = AsyncMock()

    with patch.object(api_client, "get_episode_by_code", new_callable=AsyncMock) as mock_get_ep:
        mock_get_ep.side_effect = APIConnectionError("Timeout")
        
        await handle_watch_episode(callback)
        
        # 'Bu qism topilmadi' deyilmasligi kerak!
        for call_args in callback.message.answer.call_args_list:
            text = call_args[0][0]
            assert "Bu qism topilmadi" not in text
            assert "kechikish" in text.lower() or "kuting" in text.lower() or "server" in text.lower()
