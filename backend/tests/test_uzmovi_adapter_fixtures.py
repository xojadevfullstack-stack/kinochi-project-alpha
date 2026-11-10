"""
TDD Tests for Uzmovi Adapter Fixtures:
1. Valid item extraction from HTML
2. Episode number shift (Kaiju case) rejection via admission gate
3. Invalid file / duration missing rejection
4. Duplicate item rejection
5. Pagination end (empty page / no cards)
6. Source down (network error / HTTP 500)
"""
import pytest
from unittest.mock import patch, MagicMock
from scraper.site_parser import _extract_uzmovi_items_from_html, parse_uzmovi_page
from app.core.admission_gate import final_check

UZMOVI_VALID_HTML = """
<div class="shortstory">
    <div class="shortstory-title">
        <a href="https://uzmovi.net/tarjima-kinolarri/9145-quruqlik-va-dengiz-urushi-2025.html" title="Quruqlik va dengiz urushi (2025)">
            Quruqlik va dengiz urushi (2025)
        </a>
    </div>
    <div class="shortstory-content">
        <img src="/uploads/posts/2025-01/9145.jpg" alt="Quruqlik va dengiz urushi" />
        <span class="imdb-rating">IMDb: 7.8</span>
        <a class="bot-link" href="https://t.me/UzmovieTV_Bot?start=9145">Telegramda ko'rish (Kod: 9145)</a>
    </div>
</div>
"""

UZMOVI_SERIES_HTML = """
<div class="shortstory">
    <div class="shortstory-title">
        <a href="https://uzmovi.net/serialar/8010-qashqirlar-makoni-serial-barcha-qismlar.html" title="Qashqirlar makoni (2024) Serial">
            Qashqirlar makoni (2024) Serial
        </a>
    </div>
    <div class="shortstory-content">
        <img src="/uploads/posts/8010.jpg" alt="Qashqirlar makoni" />
        <span class="imdb-rating">IMDb: 8.5</span>
    </div>
</div>
"""

UZMOVI_EMPTY_HTML = """
<!DOCTYPE html>
<html>
<body>
    <div class="navigation">Sahifalar tugadi</div>
</body>
</html>
"""

def test_uzmovi_valid_item_extraction():
    items = _extract_uzmovi_items_from_html(UZMOVI_VALID_HTML)
    assert len(items) == 1
    item = items[0]
    assert item.id == "uzmovi_9145"
    assert item.source == "uzmovi"
    assert item.source_id == "9145"
    assert "Quruqlik" in item.title
    assert item.year == 2025
    assert item.media_type == "movie"
    assert item.poster_url == "https://uzmovi.net/uploads/posts/2025-01/9145.jpg"

def test_uzmovi_series_type_detection():
    items = _extract_uzmovi_items_from_html(UZMOVI_SERIES_HTML)
    assert len(items) == 1
    item = items[0]
    assert item.media_type == "series"
    assert item.source_id == "8010"

def test_uzmovi_kaiju_episode_shift_rejection():
    # Uzmovi serial episode shift: requested Ep 5, but video file is S01E06 -> final_check fails
    media = {
        "telegram_file_id": "file_uz_ep5",
        "storage_channel_message_id": 205,
        "duration": 45 * 60,
        "language": "O'zbekcha",
        "season_number": 1,
        "episode_number": 5,
        "filename": "Kurtlar.Vadisi.S01E06.mp4",
        "caption": "Qashqirlar makoni 1-fasl 5-qism",
    }
    ok, defects = final_check("episode", media)
    assert not ok
    codes = [d["code"] for d in defects]
    assert "season_episode_conflict" in codes

def test_uzmovi_invalid_file_missing_duration_rejection():
    # Invalid media: duration is 0 or missing -> final_check fails
    media = {
        "telegram_file_id": "file_corrupt",
        "storage_channel_message_id": 206,
        "duration": 0,
        "language": "O'zbekcha",
    }
    ok, defects = final_check("movie", media)
    assert not ok
    codes = [d["code"] for d in defects]
    assert "duration_missing" in codes

def test_uzmovi_duplicate_rejection():
    # Duplicate file_unique_id
    media = {
        "telegram_file_id": "file_dup",
        "file_unique_id": "uzmovi_unique_9145",
        "duplicate_file_unique_id": True,
        "storage_channel_message_id": 207,
        "duration": 100 * 60,
        "language": "O'zbekcha",
    }
    ok, defects = final_check("movie", media)
    assert not ok
    codes = [d["code"] for d in defects]
    assert "duplicate_file_unique_id" in codes

def test_uzmovi_pagination_end():
    # Empty HTML page returns empty list without error
    items = _extract_uzmovi_items_from_html(UZMOVI_EMPTY_HTML)
    assert items == []

def test_uzmovi_source_down_graceful_handling():
    # When site throws URLError / ConnectionError, parse_uzmovi_page returns []
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused / 502 Bad Gateway")):
        items = parse_uzmovi_page("https://uzmovi.net/tarjima-kinolarri/page/9999/")
        assert items == []
