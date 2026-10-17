import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from utils.code_resolver import clean_and_extract_code, resolve_and_send_content


def test_clean_and_extract_code_numeric_only():
    """Faqat raqamlardan iborat bo'lgan matnlar prefikssiz (type_hint=None) ajratiladi."""
    assert clean_and_extract_code("30") == ("30", None)
    assert clean_and_extract_code("#30") == ("30", None)
    assert clean_and_extract_code("№123") == ("123", None)
    assert clean_and_extract_code("kod: 30") == ("30", None)


def test_clean_and_extract_code_prefixed_series():
    """Serial prefikslari (s_, series_, serial_) to'g'ri 'series' turi bilan ajratiladi."""
    assert clean_and_extract_code("s_30") == ("30", "series")
    assert clean_and_extract_code("s30") == ("s30", "series")
    assert clean_and_extract_code("series_42") == ("42", "series")
    assert clean_and_extract_code("serial_15") == ("15", "series")
    assert clean_and_extract_code("serial: 99") == ("99", "series")
    assert clean_and_extract_code("kod: s_30") == ("30", "series")


def test_clean_and_extract_code_prefixed_movie():
    """Kino prefikslari (m_, movie_, kino_, film) to'g'ri 'movie' turi bilan ajratiladi."""
    assert clean_and_extract_code("m_PT3BQB") == ("PT3BQB", "movie")
    assert clean_and_extract_code("movie_ABC123") == ("ABC123", "movie")
    assert clean_and_extract_code("kino_TEST") == ("TEST", "movie")
    assert clean_and_extract_code("kino: PT3BQB") == ("PT3BQB", "movie")
    assert clean_and_extract_code("film: MATRIX") == ("MATRIX", "movie")


def test_clean_and_extract_code_prefixed_episode():
    """Qism prefikslari (ep_, episode_, S1-CH1, S01E08) to'g'ri 'episode' turi bilan ajratiladi."""
    assert clean_and_extract_code("ep_55") == ("55", "episode")
    assert clean_and_extract_code("episode_12") == ("12", "episode")
    assert clean_and_extract_code("S1-CH1") == ("S1-CH1", "episode")
    assert clean_and_extract_code("s1ch1") == ("s1ch1", "episode")
    assert clean_and_extract_code("S01E08") == ("S01E08", "episode")


@pytest.mark.asyncio
async def test_numeric_only_query_is_not_resolved():
    """Faqat raqamdan iborat so'rov (30, 17, 123) rad etiladi va ID qidiruvi amalga oshirilmaydi."""
    bot = AsyncMock()
    chat_id = 123456789

    with patch("services.api_client.api_client.get_movie_by_id", new_callable=AsyncMock) as mock_movie_id, \
         patch("services.api_client.api_client.get_series_by_id", new_callable=AsyncMock) as mock_series_id, \
         patch("services.api_client.api_client.get_movie_by_code", new_callable=AsyncMock) as mock_movie_code:

        # 1. Sof raqam
        result = await resolve_and_send_content(bot, chat_id, "30")
        assert result is False

        # 2. Reshëtka bilan raqam
        result_hash = await resolve_and_send_content(bot, chat_id, "#30")
        assert result_hash is False

        # 3. 'kod: 30' ko'rinishidagi raqam
        result_kod = await resolve_and_send_content(bot, chat_id, "kod: 30")
        assert result_kod is False

        # Hech qanday ID yoki kod chaqirilmagan bo'lishi shart
        mock_movie_id.assert_not_called()
        mock_series_id.assert_not_called()
        mock_movie_code.assert_not_called()


@pytest.mark.asyncio
async def test_prefixed_series_id_is_resolved():
    """s_<id> prefiksi bilan berilgan serial ID si muvaffaqiyatli topiladi va yuboriladi."""
    bot = AsyncMock()
    chat_id = 123456789
    fake_series = {"id": 30, "title": "Test Serial"}

    with patch("services.api_client.api_client.get_series_by_id", new_callable=AsyncMock, return_value=fake_series) as mock_series_id, \
         patch("utils.code_resolver.send_series_info", new_callable=AsyncMock) as mock_send_series:

        # s_30 prefiksi
        result = await resolve_and_send_content(bot, chat_id, "s_30")
        assert result is True
        mock_series_id.assert_called_with(30)
        mock_send_series.assert_called_once_with(bot, chat_id, fake_series)


@pytest.mark.asyncio
async def test_movie_code_is_resolved():
    """Kino kodi (PT3BQB yoki m_PT3BQB) faqat get_movie_by_code orqali qidiriladi (get_movie_by_id chaqirilmaydi)."""
    bot = AsyncMock()
    chat_id = 123456789
    fake_movie = {"id": 1, "code": "PT3BQB", "title": "Test Kino"}

    with patch("services.api_client.api_client.get_movie_by_code", new_callable=AsyncMock, return_value=fake_movie) as mock_movie_code, \
         patch("services.api_client.api_client.get_movie_by_id", new_callable=AsyncMock) as mock_movie_id, \
         patch("utils.code_resolver.send_movie_info", new_callable=AsyncMock) as mock_send_movie:

        # Harfli kino kodi
        result = await resolve_and_send_content(bot, chat_id, "PT3BQB")
        assert result is True
        mock_movie_code.assert_called_with("PT3BQB")
        mock_send_movie.assert_called_once_with(bot, chat_id, fake_movie)
        mock_movie_id.assert_not_called()

        # Prefiksli kino kodi (m_PT3BQB)
        mock_movie_code.reset_mock()
        mock_send_movie.reset_mock()
        result_prefix = await resolve_and_send_content(bot, chat_id, "m_PT3BQB")
        assert result_prefix is True
        mock_movie_code.assert_called_with("PT3BQB")
        mock_send_movie.assert_called_once_with(bot, chat_id, fake_movie)
        mock_movie_id.assert_not_called()


@pytest.mark.asyncio
async def test_episode_code_is_resolved():
    """Qism kodi (S1-CH1 yoki ep_10) get_episode_by_code orqali qidiriladi."""
    bot = AsyncMock()
    chat_id = 123456789
    fake_ep = {"id": 10, "code": "EP10", "display_code": "S1-CH1"}

    with patch("services.api_client.api_client.get_episode_by_code", new_callable=AsyncMock, return_value=fake_ep) as mock_ep_code, \
         patch("utils.code_resolver.send_episode_to_user", new_callable=AsyncMock, return_value=True) as mock_send_ep:

        result = await resolve_and_send_content(bot, chat_id, "S1-CH1")
        assert result is True
        mock_ep_code.assert_called_with("S1-CH1")
        mock_send_ep.assert_called_once_with(bot, chat_id, fake_ep)
