import pytest
from sqlalchemy import text
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel


def test_f008_models_have_unique_tmdb_id_index():
    """F-008 regression: MovieModel and SeriesModel must have unique partial index on tmdb_id."""
    # Check MovieModel
    movie_indexes = {idx.name: idx for idx in MovieModel.__table__.indexes}
    assert "uq_movies_tmdb_id" in movie_indexes, "uq_movies_tmdb_id index missing on MovieModel"
    assert movie_indexes["uq_movies_tmdb_id"].unique is True

    # Check SeriesModel
    series_indexes = {idx.name: idx for idx in SeriesModel.__table__.indexes}
    assert "uq_series_tmdb_id" in series_indexes, "uq_series_tmdb_id index missing on SeriesModel"
    assert series_indexes["uq_series_tmdb_id"].unique is True


@pytest.mark.asyncio
async def test_f008_admission_gate_advisory_lock():
    """F-008 regression: admission_gate pre_check must invoke pg_advisory_xact_lock when tmdb_id is present."""
    from unittest.mock import AsyncMock, MagicMock
    from app.core.admission_gate import pre_check

    mock_session = AsyncMock()
    # Mock DB query results so nothing is found
    scalar_mock = MagicMock()
    scalar_mock.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = scalar_mock

    payload = {
        "title": "Inception",
        "year": 2010,
        "genres": "Sci-Fi",
        "description": "A thief who steals corporate secrets through the use of dream-sharing technology.",
        "poster_url": "https://example.com/poster.jpg",
        "tmdb_id": 27205,
        "source": "scraper",
        "source_key": "test_inception",
        "manual_verified": True
    }

    is_valid, defects = await pre_check("movie", payload, session=mock_session, check_reachability=False)

    # Check that pg_advisory_xact_lock was called with tmdb lock key
    executed_statements = [str(call.args[0]) for call in mock_session.execute.call_args_list if call.args]
    advisory_lock_called = any("pg_advisory_xact_lock" in stmt for stmt in executed_statements)
    assert advisory_lock_called, "pg_advisory_xact_lock must be acquired in pre_check for tmdb_id concurrency protection"
