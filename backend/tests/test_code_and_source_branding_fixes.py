import pytest
from app.infrastructure.db.models.ingest_item import validate_status_transition, ALLOWED_STATUS_TRANSITIONS
from app.domain.series.entities import SeriesBase, SeriesCreate
from app.domain.movies.entities import Movie

def test_needs_review_to_failed_transition_allowed():
    """needs_review holatidan failed holatiga o'tish ruxsat etilgan bo'lishi kerak."""
    assert "failed" in ALLOWED_STATUS_TRANSITIONS["needs_review"]
    # Should not raise ValueError
    validate_status_transition("needs_review", "failed")

def test_series_and_movie_default_source_type_is_none():
    """Series va Movie modellarida source_type sukut bo'yicha 'uzmovi' ga qotib qolmasligi kerak."""
    sb = SeriesBase(title="Test Serial")
    assert sb.source_type is None

    mb = Movie(title="Test Film", code="TEST01")
    assert mb.source_type is None

def test_series_create_accepts_all_supported_source_types():
    """Barcha qo'llab-quvvatlanadigan manbalar (kinochilar, anitoob, animeelar, asilmedia, uzmovi, boshqa) to'g'ri saqlanishi kerak."""
    sources = ["kinochilar", "anitoob", "animeelar", "asilmedia", "uzmovi", "boshqa"]
    for src in sources:
        sc = SeriesCreate(title=f"Test {src}", source_type=src)
        assert sc.source_type == src
