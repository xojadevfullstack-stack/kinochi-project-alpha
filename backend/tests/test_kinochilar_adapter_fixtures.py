import pytest
"""
TDD Tests for Kinochilar Adapter Fixtures:
1. Valid item extraction from HTML
2. Missing start hash (modern CDN embed page) handling -> needs_review
3. Episode number shift (Kaiju case) rejection via admission gate
4. Invalid file / duration missing rejection
5. Duplicate item rejection
6. Pagination end (empty page / no cards)
7. Source down (network error / HTTP 500)
"""
from unittest.mock import patch, MagicMock
from scraper.kinochilar_parser import (
    _extract_kinochilar_items_from_html,
    fetch_kinochilar_start_hash,
    parse_kinochilar_page,
)
from app.core.admission_gate import final_check

KINOCHILAR_VALID_HTML = """
<article class="movie-card">
    <a href="https://kinochilar.com/tarjima-kinolar/16662-yovuzlik-maskani-uzbek-tilida.html" title="Yovuzlik maskani (2024)">
        <img src="https://kinochilar.com/uploads/16662.jpg" alt="Yovuzlik maskani" />
        Yovuzlik maskani (2024) 1080p FHD
    </a>
    <div class="rating">IMDb: 6.9</div>
</article>
"""

KINOCHILAR_DETAIL_WITH_HASH = """
<!DOCTYPE html>
<html>
<body>
    <div class="full-media">
        <h1>Yovuzlik maskani (2024)</h1>
        <a href="https://t.me/kinochilar_fast_bot?start=abc123hashxyz" class="btn-bot">
            Telegramda tomosha qilish
        </a>
    </div>
</body>
</html>
"""

KINOCHILAR_DETAIL_WITHOUT_HASH = """
<!DOCTYPE html>
<html>
<body>
    <div class="full-media">
        <h1>Yovuzlik maskani (2024)</h1>
        <iframe src="//wreath-as.stravers.live/?token_movie=123" width="640" height="360"></iframe>
        <a href="https://t.me/+05xbaqax-zRiNWVi">Bizning Telegram kanal</a>
    </div>
</body>
</html>
"""

KINOCHILAR_EMPTY_HTML = """
<!DOCTYPE html>
<html>
<body>
    <div class="empty-catalog">Hech narsa topilmadi</div>
</body>
</html>
"""

def test_kinochilar_valid_item_extraction():
    items = _extract_kinochilar_items_from_html(KINOCHILAR_VALID_HTML)
    assert len(items) == 1
    item = items[0]
    assert item.id == "kinochilar_16662"
    assert item.source == "kinochilar"
    assert item.source_id == "16662"
    assert "Yovuzlik" in item.title
    assert item.year == 2024
    assert item.media_type == "movie"
    assert item.poster_url == "https://kinochilar.com/uploads/16662.jpg"
    assert item.payload == {"quality_tag": "1080p"}

def test_kinochilar_start_hash_extraction():
    with patch("urllib.request.urlopen") as mock_open:
        mock_resp = MagicMock()
        mock_resp.read.return_value = KINOCHILAR_DETAIL_WITH_HASH.encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_resp

        h = fetch_kinochilar_start_hash("https://kinochilar.com/tarjima-kinolar/16662-yovuzlik-maskani-uzbek-tilida.html")
        assert h == "abc123hashxyz"

def test_kinochilar_modern_page_without_hash_returns_none():
    # Modern CDN page without bot link must safely return None
    with patch("urllib.request.urlopen") as mock_open:
        mock_resp = MagicMock()
        mock_resp.read.return_value = KINOCHILAR_DETAIL_WITHOUT_HASH.encode("utf-8")
        mock_open.return_value.__enter__.return_value = mock_resp

        h = fetch_kinochilar_start_hash("https://kinochilar.com/tarjima-kinolar/16662-yovuzlik-maskani-uzbek-tilida.html")
        assert h is None

def test_kinochilar_kaiju_episode_shift_rejection():
    # Episode shift: requested Ep 1, but video file is S01E02 -> final_check fails
    media = {
        "telegram_file_id": "file_kc_ep1",
        "storage_channel_message_id": 301,
        "duration": 50 * 60,
        "language": "O'zbekcha",
        "season_number": 1,
        "episode_number": 1,
        "filename": "Kinochilar.Series.S01E02.1080p.mkv",
        "caption": "Kinochilar serial 1-mavsum 1-qism",
    }
    ok, defects = final_check("episode", media)
    assert not ok
    codes = [d["code"] for d in defects]
    assert "season_episode_conflict" in codes

def test_kinochilar_invalid_file_missing_duration_rejection():
    # Missing duration
    media = {
        "telegram_file_id": "file_kc_corrupt",
        "storage_channel_message_id": 302,
        "duration": None,
        "language": "O'zbekcha",
    }
    ok, defects = final_check("movie", media)
    assert not ok
    codes = [d["code"] for d in defects]
    assert "duration_missing" in codes

def test_kinochilar_duplicate_rejection():
    # Duplicate file_unique_id
    media = {
        "telegram_file_id": "file_kc_dup",
        "file_unique_id": "kinochilar_unique_16662",
        "duplicate_file_unique_id": True,
        "storage_channel_message_id": 303,
        "duration": 110 * 60,
        "language": "O'zbekcha",
    }
    ok, defects = final_check("movie", media)
    assert not ok
    codes = [d["code"] for d in defects]
    assert "duplicate_file_unique_id" in codes

def test_kinochilar_pagination_end():
    # Empty catalog HTML returns empty list
    items = _extract_kinochilar_items_from_html(KINOCHILAR_EMPTY_HTML)
    assert items == []

def test_kinochilar_source_down_graceful_handling():
    # When site is down, returns []
    with patch("urllib.request.urlopen", side_effect=Exception("503 Service Unavailable")):
        items = parse_kinochilar_page("https://kinochilar.com/page/9999/")
        assert items == []


@pytest.mark.asyncio
async def test_kinochilar_missing_hash_returns_none_not_tuple():
    from scraper.telethon_moderator_pipeline import TelethonModeratorPipeline
    from scraper.queue_manager import QueueItem
    pipeline = TelethonModeratorPipeline.__new__(TelethonModeratorPipeline)
    item = QueueItem(
        id="kinochilar_16577",
        source="kinochilar",
        source_id="16577",
        title="Sevgi uchburchagi",
        original_title=None,
        year=2024,
        media_type="movie",
        url="https://kinochilar.com/tarjima-kinolar/16577-sevgi-uchburchagi.html",
        payload=None
    )
    with patch("scraper.kinochilar_parser.fetch_kinochilar_start_hash", return_value=None):
        with patch("scraper.queue_manager.QueueManager.update_status") as mock_st:
            res = await pipeline._fetch_kinochilar_video(item=item, query="16577")
            assert res is None
            assert not isinstance(res, tuple)
            assert item.status == "needs_review"
            assert item.error_message == "missing_start_hash"
