"""Tests for Item 5: Admission gate final_check enhancements and routing for auto_index writes."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.admission_gate import final_check
from app.core.config import settings
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import EpisodeModel, SeasonModel
from app.api.deps import get_db_session, get_admin_or_bot


def test_final_check_type_consistency_movie_one_video_per_language():
    """Kino bitta tilda faqat bitta asosiy videoga ega bo'lishi mumkin."""
    # Mavjud O'zbekcha tarjimasi bo'lgan kino
    media_with_video = {
        "telegram_file_id": "file_new_123",
        "storage_channel_message_id": 200,
        "language": "O'zbekcha",
        "existing_translations": [
            {
                "language": "O'zbekcha",
                "telegram_file_id": "file_old_existing",
                "storage_channel_message_id": 100
            }
        ]
    }
    is_valid, defects = final_check("movie", media_with_video)
    assert is_valid is False
    codes = [d["code"] for d in defects]
    assert "movie_language_video_limit_exceeded" in codes

    # Tarjimasi bo'lmagan yangi til bo'lsa muvaffaqiyatli o'tishi kerak
    media_other_lang = {
        "telegram_file_id": "file_new_123",
        "storage_channel_message_id": 200,
        "language": "Ruscha",
        "existing_translations": [
            {
                "language": "O'zbekcha",
                "telegram_file_id": "file_old_existing",
                "storage_channel_message_id": 100
            }
        ]
    }
    is_valid2, defects2 = final_check("movie", media_other_lang)
    assert is_valid2 is True
    assert defects2 == []


def test_final_check_type_consistency_series_requires_season_and_episode():
    """Serial mavzusi uchun season_number va episode_number majburiy bo'lishi kerak."""
    # Mavsum va qism raqamlari yo'q
    media_missing = {
        "telegram_file_id": "file_ep_123",
        "storage_channel_message_id": 300,
        "language": "O'zbekcha"
    }
    is_valid, defects = final_check("episode", media_missing)
    assert is_valid is False
    codes = [d["code"] for d in defects]
    assert "missing_season_number" in codes
    assert "missing_episode_number" in codes

    # Mavsum va qism raqamlari mavjud
    media_valid = {
        "telegram_file_id": "file_ep_123",
        "storage_channel_message_id": 300,
        "language": "O'zbekcha",
        "season_number": 1,
        "episode_number": 4
    }
    is_valid2, defects2 = final_check("episode", media_valid)
    assert is_valid2 is True
    assert defects2 == []


def test_final_check_movie_duration_vs_tmdb_runtime_tolerance():
    """Kino video davomiyligi TMDb davomiyligi bilan taqqoslanadi va nisbiy tolerantlikdan (15%) oshsa rad etiladi."""
    settings.MOVIE_RUNTIME_TOLERANCE_PERCENT = 15

    # 1. Katta farq: TMDb 120 daqiqa, lekin video atigi 30 daqiqa (1800 soniya)
    # 120 daqiqaning 15% tolerantligi = 18 daqiqa. Farq 90 daqiqa > 18 daqiqa.
    media_extreme_mismatch = {
        "telegram_file_id": "file_movie_123",
        "storage_channel_message_id": 400,
        "language": "O'zbekcha",
        "duration": 1800,  # 30 daqiqa
        "runtime": 120
    }
    is_valid, defects = final_check("movie", media_extreme_mismatch)
    assert is_valid is False
    codes = [d["code"] for d in defects]
    assert "runtime_mismatch" in codes

    # 2. Tolerantlik doirasida: TMDb 120 daqiqa, video 110 daqiqa (6600 soniya) (farq: 10 daqiqa <= 18 daqiqa)
    media_tolerated = {
        "telegram_file_id": "file_movie_123",
        "storage_channel_message_id": 400,
        "language": "O'zbekcha",
        "duration": 6600,  # 110 daqiqa
        "runtime": 120
    }
    is_valid2, defects2 = final_check("movie", media_tolerated)
    assert is_valid2 is True
    assert defects2 == []


def test_final_check_relative_tolerance_minimum_5_minutes():
    """Qisqa film (20 daqiqa) uchun 15% = 3 daqiqa bo'lsa ham, minimal 5 daqiqa tolerantlik qo'llanilishi kerak."""
    settings.MOVIE_RUNTIME_TOLERANCE_PERCENT = 15

    # 20 daqiqali film, video 24 daqiqa (farq 4 daqiqa <= min 5 daqiqa) -> o'tishi kerak
    media_min_tolerated = {
        "telegram_file_id": "file_short_ok",
        "storage_channel_message_id": 401,
        "language": "O'zbekcha",
        "duration": 1440,  # 24 daqiqa
        "runtime": 20
    }
    is_valid, defects = final_check("movie", media_min_tolerated)
    assert is_valid is True
    assert defects == []

    # 20 daqiqali film, video 26 daqiqa (farq 6 daqiqa > min 5 daqiqa) -> rad etilishi kerak
    media_min_rejected = {
        "telegram_file_id": "file_short_bad",
        "storage_channel_message_id": 402,
        "language": "O'zbekcha",
        "duration": 1560,  # 26 daqiqa
        "runtime": 20
    }
    is_valid2, defects2 = final_check("movie", media_min_rejected)
    assert is_valid2 is False
    codes = [d["code"] for d in defects2]
    assert "runtime_mismatch" in codes


def test_final_check_unknown_duration_rejected():
    """Video davomiyligi noma'lum (None yoki 0) bo'lsa duration_unknown defekti bilan rad etiladi."""
    # 1. duration: None
    media_none = {
        "telegram_file_id": "file_no_dur",
        "storage_channel_message_id": 403,
        "language": "O'zbekcha",
        "duration": None
    }
    is_valid, defects = final_check("movie", media_none)
    assert is_valid is False
    codes = [d["code"] for d in defects]
    assert "duration_unknown" in codes

    # 2. duration: 0
    media_zero = {
        "telegram_file_id": "file_zero_dur",
        "storage_channel_message_id": 404,
        "language": "O'zbekcha",
        "duration": 0
    }
    is_valid2, defects2 = final_check("movie", media_zero)
    assert is_valid2 is False
    codes2 = [d["code"] for d in defects2]
    assert "duration_unknown" in codes2


def test_final_check_one_file_cannot_belong_to_two_titles():
    """Bitta fayl birdan ortiq nomga tegishli bo'lsa rad etilishi shart."""
    media_duplicate_title = {
        "telegram_file_id": "file_shared_123",
        "storage_channel_message_id": 500,
        "language": "O'zbekcha",
        "attached_to_other_title": True
    }
    is_valid, defects = final_check("movie", media_duplicate_title)
    assert is_valid is False
    codes = [d["code"] for d in defects]
    assert "file_belongs_to_multiple_titles" in codes


@pytest.mark.asyncio
async def test_link_movie_video_endpoint_gate_rejection_runtime_mismatch():
    """Kino video davomiyligi mos kelmasa /movies/{id}/link-video 400 Bad Request qaytarishi kerak."""
    mock_session = AsyncMock(spec=AsyncSession)
    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_admin_or_bot] = lambda: {"role": "admin"}

    try:
        mock_movie = MagicMock(spec=MovieModel)
        mock_movie.id = 1
        mock_movie.title = "Kino Runtime Test"
        mock_movie.runtime = 120
        mock_movie.translations = []
        mock_session.get.return_value = mock_movie

        # record_rejection mock
        res_rej = MagicMock()
        res_rej.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = res_rej

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/v1/movies/1/link-video", json={
                "message_id": 999,
                "language": "O'zbekcha",
                "telegram_file_id": "file_short_123",
                "duration": 600  # 10 daqiqa (120 daqiqadan 110 daqiqa farq)
            })
            assert resp.status_code == status.HTTP_400_BAD_REQUEST
            data = resp.json()
            codes = [d["code"] for d in data["detail"]["defects"]]
            assert "runtime_mismatch" in codes
            assert mock_session.commit.called
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        app.dependency_overrides.pop(get_admin_or_bot, None)


@pytest.mark.asyncio
async def test_link_episode_video_endpoint_gate_rejection_missing_numbers():
    """Serial mavzusi uchun season yoki episode raqamlari bo'lmasa 400 Bad Request qaytarishi kerak."""
    mock_session = AsyncMock(spec=AsyncSession)
    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_admin_or_bot] = lambda: {"role": "admin"}

    try:
        mock_ep = MagicMock(spec=EpisodeModel)
        mock_ep.id = 1
        mock_ep.title = "Ep 1"
        mock_ep.season_id = 1
        mock_ep.episode_number = None  # Missing!

        mock_session.get.side_effect = [mock_ep, None]

        res_rej = MagicMock()
        res_rej.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = res_rej

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/v1/series/episodes/1/link-video", json={
                "message_id": 999,
                "language": "O'zbekcha",
                "telegram_file_id": "file_ep_123"
            })
            assert resp.status_code == status.HTTP_400_BAD_REQUEST
            data = resp.json()
            codes = [d["code"] for d in data["detail"]["defects"]]
            assert "missing_episode_number" in codes
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        app.dependency_overrides.pop(get_admin_or_bot, None)
