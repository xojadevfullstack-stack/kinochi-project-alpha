import pytest
from unittest.mock import AsyncMock, patch
from scraper.telethon_moderator_pipeline import resolve_page_ids

class DummyItem:
    def __init__(self, media_type, title=""):
        self.media_type = media_type
        self.title = title

def test_resolve_page_ids_dorama():
    item = DummyItem("dorama", "Tasodifmi")
    meta = {"genres": "Drama, Melodrama"}
    page_ids = resolve_page_ids(item, meta)
    assert 5 in page_ids
    # Ensure invalid pages are not returned
    for invalid_page in [9, 10, 11, 12]:
        assert invalid_page not in page_ids

def test_resolve_page_ids_multfilm_no_anime():
    item = DummyItem("multfilm", "Ajoyib sirk")
    meta = {"category_ids": [22], "genres": "Animatsiya, Komediya"}
    page_ids = resolve_page_ids(item, meta)
    assert 8 in page_ids
    assert 1 not in page_ids

def test_resolve_page_ids_anime():
    item = DummyItem("anime", "Solo Leveling")
    meta = {"category_ids": [2], "genres": "Anime, Fantastika"}
    page_ids = resolve_page_ids(item, meta)
    assert 1 in page_ids
    assert 8 not in page_ids

@pytest.mark.asyncio
async def test_enrich_movie_smart_media_type_distribution(monkeypatch):
    from scraper import smart_enricher

    fake_cat_map = {
        "anime": 2,
        "drama": 3,
        "komediya": 5,
        "animatsiya": 22,
        "tarjima kinolar": 36,
        "hind kinolari": 37,
        "turk kinolari": 38,
        "turk seriallari": 39,
        "doramalar": 40,
    }

    monkeypatch.setattr(smart_enricher, "get_all_categories_map", AsyncMock(return_value=fake_cat_map))
    monkeypatch.setattr(smart_enricher, "gemini_identify_movie", AsyncMock(return_value=None))

    # 1. Dorama
    with patch.object(smart_enricher.tmdb_client, "search", AsyncMock(return_value=[])):
        res_dorama = await smart_enricher.enrich_movie_smart(
            raw_title="Tasodifmi dorama",
            media_type="dorama"
        )
        assert 40 in res_dorama["category_ids"]

    # 2. Multfilm (must have 22, must NOT have 2)
    with patch.object(smart_enricher.tmdb_client, "search", AsyncMock(return_value=[])):
        res_mult = await smart_enricher.enrich_movie_smart(
            raw_title="Ajoyib multfilm",
            media_type="multfilm"
        )
        assert 22 in res_mult["category_ids"]
        assert 2 not in res_mult["category_ids"]

    # 3. Turk serial
    with patch.object(smart_enricher.tmdb_client, "search", AsyncMock(return_value=[])):
        res_turk = await smart_enricher.enrich_movie_smart(
            raw_title="Qashqirlar makoni serial turkiya",
            media_type="series"
        )
        assert 39 in res_turk["category_ids"]

    # 4. Hind kino
    with patch.object(smart_enricher.tmdb_client, "search", AsyncMock(return_value=[])):
        res_hind = await smart_enricher.enrich_movie_smart(
            raw_title="Qasoskor bollywood hind kinosi",
            media_type="movie"
        )
        assert 37 in res_hind["category_ids"]
