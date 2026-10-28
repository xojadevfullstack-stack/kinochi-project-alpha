import pytest
from unittest.mock import AsyncMock, patch
from utils.code_resolver import clean_and_extract_code, resolve_and_send_content


def test_clean_and_extract_code_handles_all_media_variants():
    """Barcha media turlari uchun clean_and_extract_code to'g'ri ishlashini tekshirish."""
    # 1. Epizodlar (ep_ prefiksi bilan va prefikssiz)
    assert clean_and_extract_code("ep_28831337") == ("28831337", "episode")
    assert clean_and_extract_code("episode_d0782b22") == ("d0782b22", "episode")
    assert clean_and_extract_code("S1-CH1") == ("S1-CH1", "episode")
    assert clean_and_extract_code("s_1007_s1_ep1") == ("s_1007_s1_ep1", "episode")
    assert clean_and_extract_code("28831337") == ("28831337", None)

    # 2. Kinolar
    assert clean_and_extract_code("m_PT3BQB") == ("PT3BQB", "movie")
    assert clean_and_extract_code("kino_123456") == ("123456", "movie")
    assert clean_and_extract_code("PT3BQB") == ("PT3BQB", None)

    # 3. Seriallar
    assert clean_and_extract_code("s_998") == ("998", "series")
    assert clean_and_extract_code("series_998") == ("998", "series")
    assert clean_and_extract_code("s998") == ("s998", "series")

    # 4. To'plamlar
    assert clean_and_extract_code("col_12") == ("12", "collection")
    assert clean_and_extract_code("fr_marvel") == ("marvel", "collection")


@pytest.mark.asyncio
async def test_numeric_episode_code_resolves_and_sends():
    """Saytda berilgan Taxtlar o'yini 1-qismi '28831337' kodi botda muvaffaqiyatli topiladi."""
    bot = AsyncMock()
    chat_id = 123456789
    fake_ep = {
        "id": 14052,
        "code": "28831337",
        "display_code": "S1-CH1",
        "series_id": 998,
        "title": "1-qism",
        "translations": [{"id": 1, "telegram_file_id": "file_123"}]
    }

    with patch("services.api_client.api_client.get_movie_by_code", new_callable=AsyncMock, return_value=None), \
         patch("services.api_client.api_client.get_episode_by_code", new_callable=AsyncMock, return_value=fake_ep) as mock_ep, \
         patch("utils.code_resolver.send_episode_to_user", new_callable=AsyncMock, return_value=True) as mock_send:

        # a) Direct start with numeric episode code: /start 28831337
        res1 = await resolve_and_send_content(bot, chat_id, "28831337")
        assert res1 is True
        mock_ep.assert_called_with("28831337")
        mock_send.assert_called_once_with(bot, chat_id, fake_ep)

        # b) Prefixed episode code: /start ep_28831337
        mock_ep.reset_mock()
        mock_send.reset_mock()
        res2 = await resolve_and_send_content(bot, chat_id, "ep_28831337")
        assert res2 is True
        mock_ep.assert_called_with("28831337")
        mock_send.assert_called_once_with(bot, chat_id, fake_ep)


@pytest.mark.asyncio
async def test_numeric_only_short_string_does_not_call_ambiguous_ids():
    """Qisqa raqamlar (masalan '30') film yoki qism kodi bo'lmasa, noaniq ID sifatida chaqirilmasligi kerak."""
    bot = AsyncMock()
    chat_id = 123456789

    with patch("services.api_client.api_client.get_movie_by_code", new_callable=AsyncMock, return_value=None) as mock_movie_code, \
         patch("services.api_client.api_client.get_movie_by_id", new_callable=AsyncMock) as mock_movie_id, \
         patch("services.api_client.api_client.get_series_by_id", new_callable=AsyncMock) as mock_series_id:

        res = await resolve_and_send_content(bot, chat_id, "30")
        assert res is False
        mock_movie_code.assert_called_once_with("30")
        mock_movie_id.assert_not_called()
        mock_series_id.assert_not_called()
