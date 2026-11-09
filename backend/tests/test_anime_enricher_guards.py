import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from scraper.queue_manager import QueueItem
from scraper.telethon_moderator_pipeline import resolve_page_ids

def test_anime_smart_enricher_and_pipeline_page_isolation():
    """Assertion: Anime items MUST NEVER get Page 8 (Multfilm) or Category 22 (Animatsiya) even if TMDb returns 'Animatsiya' genre."""
    item = QueueItem(
        id="anime_99",
        source="anitoob",
        title="Jujutsu Kaisen",
        media_type="anime",
        url="http://anitoob.uz/anime/jujutsu"
    )
    meta = {
        "title": "Sehrli jang",
        "genres": ["Animatsiya", "Jangari", "Fantastika"],
        "category_ids": [2],
    }

    # Resolve pages for the anime
    pages = resolve_page_ids(item, meta)
    assert 1 in pages, "Anime must be linked to Page 1 (Anime)"
    assert 8 not in pages, "Anime must NEVER be linked to Page 8 (Multfilm)"
    assert 9 not in pages, "Anime must not be linked to Page 9 (Tarjima kinolar)"

def test_cartoon_smart_enricher_and_pipeline_page_isolation():
    """Assertion: True cartoons (Shrek, Moana) MUST get Page 8 (Multfilm) and NOT Page 1 (Anime)."""
    item = QueueItem(
        id="mult_1",
        source="uzmovi",
        title="Muzlik davri",
        media_type="multfilm",
        url="http://uzmovi.tv/multfilm/ice-age"
    )
    meta = {
        "title": "Muzlik davri",
        "genres": ["Animatsiya", "Komediya", "Oilaviy"],
        "category_ids": [22],
    }

    pages = resolve_page_ids(item, meta)
    assert 8 in pages, "Cartoons must be linked to Page 8 (Multfilm)"
    assert 1 not in pages, "Cartoons must NEVER be linked to Page 1 (Anime)"
