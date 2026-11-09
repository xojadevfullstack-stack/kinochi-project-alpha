import os
import sys

sys.path.insert(0, os.path.abspath("bot"))

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.api_client import api_client, APIConnectionError
from handlers.browsing import handle_watch_movie, handle_watch_episode, handle_show_season, SERVER_RETRY_MSG
import httpx

@pytest.mark.asyncio
async def test_k5_api_client_500_swallowed_as_none():
    """
    K5 tekshiruvi: api_client 500 yoki 502 xatolik yuz berganda None qaytaradimi?
    Isbot: response.raise_for_status() HTTPStatusError tashlaydi,
    u esa generic httpx.HTTPError tomonidan tutilib None qaytariladi.
    Natijada bot 500 xatosini ham 'kino topilmadi' (404) deb ko'rsatadi!
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError("500 Server Error", request=MagicMock(), response=mock_resp)

    with patch.object(api_client.client, "get", AsyncMock(return_value=mock_resp)):
        res = await api_client.get_movie_by_code("TESTCODE")
        assert res is None, "500 xatosi None ga aylanib ketmoqda (404 bilan qorishmoqda)"


@pytest.mark.asyncio
async def test_k5_callback_answer_delayed_after_api_call():
    """
    K5 tekshiruvi: handle_watch_movie da callback.answer() API chaqiruvidan KEYIN
    finally blokida chaqiriladi. Agar API so'rovi 25s davom etsa,
    Telegram 'query is too old' xatosini beradi va tugma 25 soniya davomida aylanib qoladi.
    """
    call_order = []

    mock_callback = MagicMock()
    mock_callback.data = "watch_m_TESTCODE"
    mock_callback.from_user.id = 12345
    mock_callback.message.answer = AsyncMock()
    
    async def fake_get_movie(*args, **kwargs):
        call_order.append("api_client_called")
        return {"id": 1, "code": "TESTCODE", "title": "Test Kino", "translations": []}

    async def fake_answer(*args, **kwargs):
        call_order.append("callback_answer_called")

    mock_callback.answer = AsyncMock(side_effect=fake_answer)

    with patch.object(api_client, "get_movie_by_code", side_effect=fake_get_movie), \
         patch("handlers.browsing.send_movie_to_user", AsyncMock(return_value=True)):
        await handle_watch_movie(mock_callback)

    # Chaqiruvlar tartibi: avval API, keyin callback.answer()
    assert call_order == ["api_client_called", "callback_answer_called"], (
        f"Kutilgan tartib API -> answer, ammo olingan: {call_order}"
    )
