import time
import pytest
from scraper.smart_enricher import ANIME_TITLE_MAP
from scraper.duplicate_checker import DuplicateChecker

@pytest.mark.asyncio
async def test_bleach_title_preserved():
    # 1. "bleach" must map to "Bleach" in ANIME_TITLE_MAP
    assert "bleach" in ANIME_TITLE_MAP
    assert ANIME_TITLE_MAP["bleach"].get("uz") == "Bleach"
    assert ANIME_TITLE_MAP["bleach"].get("tmdb_id") == 30984

    # 2. "tabiat farzandi" must map to "Ob-havo farzandi" with tmdb_id 568160
    assert "tabiat farzandi" in ANIME_TITLE_MAP
    assert ANIME_TITLE_MAP["tabiat farzandi"].get("tmdb_id") == 568160
    assert ANIME_TITLE_MAP["tabiat farzandi"].get("uz") == "Ob-havo farzandi"

@pytest.mark.asyncio
async def test_duplicate_checker_matches_by_tmdb_id_regardless_of_different_title():
    checker = DuplicateChecker()
    # Mock db cache with existing movie "Ob-havo farzandi" (TMDb 568160)
    checker._movies = [
        {
            "id": 839,
            "title": "Ob-havo farzandi",
            "original_title": "Tenki no Ko",
            "release_year": 2019,
            "code": "839",
            "tmdb_id": 568160,
            "type": "movie",
            "slug": "ob-havo-farzandi-2019",
            "stem_slug": "obhavofarzandi2019"
        }
    ]
    checker._series = []
    checker._last_cache_time = time.time()  # Prevent cache refresh overwriting mock

    # Query with a completely different donor raw title "Tabiat farzandi", but with the same TMDb ID
    result = await checker.check(
        title="Tabiat farzandi",
        year=2019,
        original_title=None,
        media_type="movie",
        tmdb_id=568160
    )

    assert result.is_duplicate is True
    assert result.match_type == "tmdb_id"
    assert result.matched_id == 839
    assert result.matched_title == "Ob-havo farzandi"
