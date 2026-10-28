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
async def test_numeric_only_query_is_not_resolved_when_code_not_found():
    """Faqat raqamdan iborat so'rov (30, 17, 123) avval movie code sifatida qidiriladi, topilmasa ID qidiruvi rad etiladi."""
    bot = AsyncMock()
    chat_id = 123456789

    with patch("services.api_client.api_client.get_movie_by_id", new_callable=AsyncMock) as mock_movie_id, \
         patch("services.api_client.api_client.get_series_by_id", new_callable=AsyncMock) as mock_series_id, \
         patch("services.api_client.api_client.get_movie_by_code", new_callable=AsyncMock, return_value=None) as mock_movie_code:

        # 1. Sof raqam
        result = await resolve_and_send_content(bot, chat_id, "30")
        assert result is False

        # 2. Reshëtka bilan raqam
        result_hash = await resolve_and_send_content(bot, chat_id, "#30")
        assert result_hash is False

        # 3. 'kod: 30' ko'rinishidagi raqam
        result_kod = await resolve_and_send_content(bot, chat_id, "kod: 30")
        assert result_kod is False

        # Film kodi sifatida qidirilgan bo'lishi kerak
        assert mock_movie_code.call_count == 3
        # Lekin noaniq ID qidiruvlari chaqirilmagan bo'lishi shart
        mock_movie_id.assert_not_called()
        mock_series_id.assert_not_called()


@pytest.mark.asyncio
async def test_numeric_movie_code_is_resolved():
    """Film kodi sof raqam bo'lgan holatda (masalan: '123456'), u get_movie_by_code orqali muvaffaqiyatli topiladi."""
    bot = AsyncMock()
    chat_id = 123456789
    fake_movie = {"id": 10, "code": "123456", "title": "Raqamli Kodli Film"}

    with patch("services.api_client.api_client.get_movie_by_code", new_callable=AsyncMock, return_value=fake_movie) as mock_movie_code, \
         patch("services.api_client.api_client.get_movie_by_id", new_callable=AsyncMock) as mock_movie_id, \
         patch("services.api_client.api_client.get_series_by_id", new_callable=AsyncMock) as mock_series_id, \
         patch("utils.code_resolver.send_movie_info", new_callable=AsyncMock) as mock_send_movie:

        result = await resolve_and_send_content(bot, chat_id, "123456")
        assert result is True
        mock_movie_code.assert_called_once_with("123456")
        mock_send_movie.assert_called_once_with(bot, chat_id, fake_movie)
        # ID qidiruvi chaqirilmagan bo'lishi shart
        mock_movie_id.assert_not_called()
        mock_series_id.assert_not_called()


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


@pytest.mark.asyncio
async def test_random_alphanumeric_episode_code_is_resolved():
    """8-belgili tasodifiy qism kodi (gb3SGSCj, ASVdEqPi) get_episode_by_code orqali muvaffaqiyatli topiladi."""
    bot = AsyncMock()
    chat_id = 123456789
    fake_ep = {"id": 14946, "code": "gb3SGSCj", "display_code": "S1-CH1"}

    with patch("services.api_client.api_client.get_movie_by_code", new_callable=AsyncMock, return_value=None), \
         patch("services.api_client.api_client.get_episode_by_code", new_callable=AsyncMock, return_value=fake_ep) as mock_ep_code, \
         patch("utils.code_resolver.send_episode_to_user", new_callable=AsyncMock, return_value=True) as mock_send_ep:

        result = await resolve_and_send_content(bot, chat_id, "gb3SGSCj")
        assert result is True
        mock_ep_code.assert_called_with("gb3SGSCj")
        mock_send_ep.assert_called_once_with(bot, chat_id, fake_ep)


@pytest.mark.asyncio
async def test_compound_episode_code_is_resolved():
    """Compound formatdagi qism kodi (s_1007_s1_ep1) to'g'ri ajratiladi va qidiriladi."""
    bot = AsyncMock()
    chat_id = 123456789
    fake_ep = {"id": 14930, "code": "ASVdEqPi"}

    with patch("services.api_client.api_client.get_episode_by_code", new_callable=AsyncMock, return_value=fake_ep) as mock_ep, \
         patch("utils.code_resolver.send_episode_to_user", new_callable=AsyncMock, return_value=True):

        result = await resolve_and_send_content(bot, chat_id, "s_1007_s1_ep1")
        assert result is True
        mock_ep.assert_called_with("s_1007_s1_ep1")


@pytest.mark.asyncio
async def test_collection_slug_is_resolved():
    """10 belgidan uzun to'plam slugi (masalan harry-potter) rad etilmasdan get_collection orqali topiladi."""
    bot = AsyncMock()
    chat_id = 123456789
    fake_col = {"id": 1, "slug": "harry-potter", "name": "Garri Potter"}

    with patch("services.api_client.api_client.get_movie_by_code", new_callable=AsyncMock, return_value=None), \
         patch("services.api_client.api_client.get_episode_by_code", new_callable=AsyncMock, return_value=None), \
         patch("services.api_client.api_client.get_series_by_code", new_callable=AsyncMock, return_value=None), \
         patch("services.api_client.api_client.get_collection", new_callable=AsyncMock, return_value=fake_col) as mock_col, \
         patch("utils.code_resolver.send_collection_info", new_callable=AsyncMock, return_value=True):

        result = await resolve_and_send_content(bot, chat_id, "harry-potter")
        assert result is True
        mock_col.assert_called_with("harry-potter")


@pytest.mark.asyncio
async def test_numeric_episode_code_is_resolved():
    """8-raqamli sof sonli qism kodi (masalan: Taxtlar o'yini 1-qismi '28831337') get_episode_by_code orqali muvaffaqiyatli topiladi."""
    bot = AsyncMock()
    chat_id = 123456789
    fake_ep = {"id": 14052, "code": "28831337", "display_code": "S1-CH1", "series_id": 998}

    with patch("services.api_client.api_client.get_movie_by_code", new_callable=AsyncMock, return_value=None), \
         patch("services.api_client.api_client.get_episode_by_code", new_callable=AsyncMock, return_value=fake_ep) as mock_ep_code, \
         patch("utils.code_resolver.send_episode_to_user", new_callable=AsyncMock, return_value=True) as mock_send_ep:

        # 1. Sof raqamli qism kodi: 28831337 (saytdan kelgan link)
        result = await resolve_and_send_content(bot, chat_id, "28831337")
        assert result is True
        mock_ep_code.assert_called_with("28831337")
        mock_send_ep.assert_called_once_with(bot, chat_id, fake_ep)

        # 2. Prefiksli qism kodi: ep_28831337
        mock_ep_code.reset_mock()
        mock_send_ep.reset_mock()
        result_prefixed = await resolve_and_send_content(bot, chat_id, "ep_28831337")
        assert result_prefixed is True
        mock_ep_code.assert_called_with("28831337")
        mock_send_ep.assert_called_once_with(bot, chat_id, fake_ep)
