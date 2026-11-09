import pytest
import re
from scraper.smart_enricher import clean_movie_title, ANIME_TITLE_MAP
from scraper.telethon_moderator_pipeline import resolve_page_ids


def test_title_cleaner_does_not_split_intra_word_hyphens():
    """Ensure hyphenated words like 'Aka-uka' or 'Spider-Man' are not split into 'Aka' or 'Spider'."""
    raw = "Aka-uka Grimm ertaklari Multserial"
    clean = clean_movie_title(raw)
    
    # Subtitle splitting pattern must not match intra-word '-'
    sub_parts = re.split(r"\s+[:\-\–\—\/]\s+|:\s*", clean)
    assert len(sub_parts) == 1, f"Expected no split on 'Aka-uka', got {sub_parts}"
    assert "Aka" not in [p.strip() for p in sub_parts if len(p.strip()) <= 3]


def test_anime_title_map_contains_grimm_and_kiki():
    """Verify that canonical anime titles are pre-mapped with correct TMDb IDs and clean Uzbek titles."""
    assert "aka-uka grimm ertaklari" in ANIME_TITLE_MAP
    grimm_entry = ANIME_TITLE_MAP["aka-uka grimm ertaklari"]
    assert grimm_entry["tmdb_id"] == 9892
    assert grimm_entry["type"] == "tv"
    assert grimm_entry["uz"] == "Aka-uka Grimm ertaklari"

    assert "kiki va eltuv xizmati" in ANIME_TITLE_MAP
    kiki_entry = ANIME_TITLE_MAP["kiki va eltuv xizmati"]
    assert kiki_entry["tmdb_id"] == 16859
    assert kiki_entry["uz"] == "Kiki: Eltuv xizmati"


def test_live_action_not_assigned_to_anime():
    """If TMDb genres do not include Animation (ID 16), live action movie must not be assigned to Page 1 (Anime)."""
    class MockItem:
        media_type = "anime"
        title = "Zodiak ritsarlari"

    # Meta has Action, Fantasy genres (no Animation)
    meta = {
        "page_ids": [],
        "category_ids": [1, 6],
        "genres": "Jangari, Fantastika",
        "tmdb_genre_ids": [28, 14],  # Action, Fantasy (no 16)
        "is_animation": False
    }

    pages = resolve_page_ids(MockItem(), meta)
    assert 1 not in pages, f"Page 1 (Anime) must not be assigned to live-action movie! Got pages: {pages}"
