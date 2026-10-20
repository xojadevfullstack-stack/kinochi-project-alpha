"""
Unit tests for Admission Gate (B2).
Tests pre_check, final_check, reachability, and state machine promotion.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.admission_gate import (
    pre_check,
    final_check,
    normalize_title,
    check_url_reachable,
    record_rejection,
    resolve_rejection,
    promote_to_published,
)
from app.infrastructure.db.models.rejected_item import RejectedItemModel


def test_normalize_title():
    assert normalize_title("  Qasoskorlar: Intiho (2019)  ") == "qasoskorlar intiho 2019"
    assert normalize_title("Spider-Man: No Way Home") == "spiderman no way home"


@pytest.mark.asyncio
async def test_pre_check_valid_movie():
    payload = {
        "title": "Inception",
        "year": 2010,
        "poster_url": "https://image.tmdb.org/t/p/w500/test.jpg",
        "genres": ["Sci-Fi", "Action"],
        "description": "A thief who steals corporate secrets through the use of dream-sharing technology.",
        "source": "uzmovi",
        "source_key": "uzmovi_1234",
        "tmdb_id": 27205,
    }
    is_valid, defects = await pre_check("movie", payload, check_reachability=False)
    assert is_valid is True
    assert defects == []


@pytest.mark.asyncio
async def test_pre_check_defective_movie():
    # 1. Missing title, invalid year, short description, missing tmdb_id
    payload = {
        "title": "A",
        "year": 1800,
        "poster_url": "invalid_url",
        "genres": [],
        "description": "Short",
        "source": "",
    }
    is_valid, defects = await pre_check("movie", payload, check_reachability=False)
    assert is_valid is False
    codes = [d["code"] for d in defects]
    assert "missing_source" in codes
    assert "missing_or_short_title" in codes
    assert "invalid_year" in codes
    assert "missing_genres" in codes
    assert "insufficient_description" in codes
    assert "missing_or_invalid_poster_url" in codes
    assert "missing_tmdb_id" in codes


@pytest.mark.asyncio
async def test_pre_check_national_and_manual_override():
    # Uzbek national movie without TMDb ID should pass
    payload = {
        "title": "Mahallada duv-duv gap",
        "year": 1960,
        "poster_url": "https://example.com/poster.jpg",
        "genres": ["Comedy"],
        "description": "O'zbek kinosining eng sara durdonalaridan biri bo'lgan ajoyib komediya.",
        "source": "uzmovi",
        "is_national": True,
    }
    is_valid, defects = await pre_check("movie", payload, check_reachability=False)
    assert is_valid is True

    # Manual verified override
    payload2 = {
        "title": "Custom Indie Film",
        "year": 2024,
        "poster_url": "https://example.com/poster.jpg",
        "genres": ["Drama"],
        "description": "Mustaqil ijodkorlar tomonidan yaratilgan yangi qisqa metrajli film.",
        "source": "custom",
        "manual_verified": True,
    }
    is_valid2, defects2 = await pre_check("movie", payload2, check_reachability=False)
    assert is_valid2 is True


@pytest.mark.asyncio
async def test_pre_check_anime_rules():
    # Anime without Shikimori and TMDb ID must fail
    anime_payload = {
        "title": "Naruto Shippuden",
        "year": 2007,
        "poster_url": "https://example.com/naruto.jpg",
        "genres": ["Anime", "Action"],
        "description": "Naruto Uzumaki kishloqni himoya qilish uchun yangi kuchlarni o'rganadi.",
        "source": "anitoob",
    }
    is_valid, defects = await pre_check("series", anime_payload, check_reachability=False)
    assert is_valid is False
    assert any(d["code"] == "missing_anime_external_id" for d in defects)

    # With shikimori_id, passes
    anime_payload["shikimori_id"] = 1735
    is_valid2, defects2 = await pre_check("series", anime_payload, check_reachability=False)
    assert is_valid2 is True


@pytest.mark.asyncio
async def test_pre_check_episode():
    # Invalid episode
    is_valid, defects = await pre_check("episode", {"source": "uzmovi", "season_number": 0, "episode_number": -1})
    assert is_valid is False
    assert any(d["code"] == "invalid_season_number" for d in defects)
    assert any(d["code"] == "invalid_episode_number" for d in defects)

    # Valid episode
    is_valid2, defects2 = await pre_check("episode", {"source": "uzmovi", "season_number": 1, "episode_number": 5})
    assert is_valid2 is True


def test_final_check_valid_and_invalid():
    # Valid media
    valid_media = {
        "telegram_file_id": "BAACAgIAAxkBAAI123...",
        "storage_channel_message_id": 456,
        "duration": 7200,
        "language": "O'zbekcha",
        "file_size": 1000 * 1024 * 1024,
    }
    is_valid, defects = final_check("movie", valid_media)
    assert is_valid is True
    assert defects == []

    # Invalid: missing file_id, invalid message_id, language='Asosiy', size > 2GB
    invalid_media = {
        "telegram_file_id": "",
        "storage_channel_message_id": 0,
        "duration": -10,
        "language": "Asosiy",
        "file_size": 2500 * 1024 * 1024,
    }
    is_valid2, defects2 = final_check("movie", invalid_media)
    assert is_valid2 is False
    codes = [d["code"] for d in defects2]
    assert "missing_telegram_file_id" in codes
    assert "missing_storage_channel_message_id" in codes
    assert "invalid_duration" in codes
    assert "invalid_language" in codes
    assert "file_exceeds_telegram_limit" in codes


@pytest.mark.asyncio
async def test_state_machine_record_rejection_and_promote():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    # 1. Record rejection
    rej_item = await record_rejection(
        session=mock_session,
        media_type="movie",
        source="uzmovi",
        source_key="uz_999",
        title="Test Movie",
        payload={"raw": "data"},
        defects=[{"field": "poster_url", "code": "unreachable", "message": "Failed"}],
    )
    assert rej_item.source == "uzmovi"
    assert rej_item.attempts == 1
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called()

    # 2. Promote to published
    mock_media = MagicMock()
    mock_media.publish_status = "pending"
    await promote_to_published(mock_session, mock_media, source="uzmovi", source_key="uz_999")
    assert mock_media.publish_status == "published"


@pytest.mark.asyncio
async def test_pre_check_series_with_release_year_and_category_ids():
    payload = {
        "title": "The Mentalist",
        "release_year": 2008,
        "poster_url": "https://image.tmdb.org/t/p/w500/test.jpg",
        "category_ids": [1, 2],
        "description": "Patrick Jane is an independent consultant for the California Bureau of Investigation.",
        "source": "uzmovi",
        "source_key": "uzmovi_series_123",
        "tmdb_id": 5920,
    }
    is_valid, defects = await pre_check("series", payload, check_reachability=False)
    assert is_valid is True
    assert defects == []

