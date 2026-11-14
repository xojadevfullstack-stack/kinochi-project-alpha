import pytest
from scraper.smart_enricher import score_tmdb_candidate, ANIME_TITLE_MAP

def test_obs_86_show_without_animation_genre_is_disqualified():
    """Obs 86 Show (empty genre_ids or non-16) must be rejected with -200.0 for anime sources."""
    cand_obs = {
        "id": 292821,
        "title": "Obs 86 - Show",
        "genre_ids": [],
        "vote_average": 0.0,
    }
    score = score_tmdb_candidate(
        candidate=cand_obs,
        query="86",
        source="anitoob",
        media_type="anime"
    )
    assert score <= -100.0, f"Expected disqualification for non-animation candidate, got score={score}"

def test_naruto_ocean_cut_fan_edit_is_disqualified():
    """Fan edits like 'Naruto The Ocean Cut' must be rejected with -200.0."""
    cand_ocean_cut = {
        "id": 328746,
        "title": "Naruto The Ocean Cut",
        "genre_ids": [16, 28],
        "vote_average": 8.0,
    }
    score = score_tmdb_candidate(
        candidate=cand_ocean_cut,
        query="Naruto",
        source="anitoob",
        media_type="anime"
    )
    assert score <= -100.0, f"Expected fan-edit 'Ocean Cut' to be disqualified, got score={score}"

def test_anime_title_map_mappings():
    """Verify canonical mappings exist for 86, Naruto Shippuden, Attack on Titan, and World's End Harem."""
    # 86 mapping
    assert "86" in ANIME_TITLE_MAP
    assert ANIME_TITLE_MAP["86"]["tmdb_id"] == 100565
    assert ANIME_TITLE_MAP["86"]["type"] == "tv"

    # Naruto Shippuden mapping
    assert "naruto shippuden" in ANIME_TITLE_MAP
    assert ANIME_TITLE_MAP["naruto shippuden"]["tmdb_id"] == 31910
    assert ANIME_TITLE_MAP["naruto shippuden"]["type"] == "tv"

    # Attack on Titan mapping (must be TV 1429, not movie 1333100)
    assert "titanlar hujumi" in ANIME_TITLE_MAP
    assert ANIME_TITLE_MAP["titanlar hujumi"]["tmdb_id"] == 1429
    assert ANIME_TITLE_MAP["titanlar hujumi"]["type"] == "tv"

    # World's End Harem mapping
    assert "world's end harem" in ANIME_TITLE_MAP
    assert ANIME_TITLE_MAP["world's end harem"]["tmdb_id"] == 103409
    assert ANIME_TITLE_MAP["world's end harem"]["type"] == "tv"

def test_anime_season_extraction():
    """Verify season number is accurately parsed from anime titles."""
    from scraper.telethon_moderator_pipeline import extract_season_number_from_text
    assert extract_season_number_from_text("Naruto 2-fasl") == 2
    assert extract_season_number_from_text("Naruto 2 Fasl") == 2
    assert extract_season_number_from_text("Shilliq sifatida qayta tug'ilganim haqida 4-fasl") == 4
    assert extract_season_number_from_text("Zanjirlangan qul 2-mavsum") == 2
    assert extract_season_number_from_text("Hujumkor titanlar") is None
