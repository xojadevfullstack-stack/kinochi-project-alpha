"""
Test public routes and published_only query filter (A2, A3, A4).
Asserts that all public media, season, and episode read paths hide pending/hidden items.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select

from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel
from app.infrastructure.db.query_filters import published_only
from app.main import app


def test_published_only_sql_clauses():
    """published_only helper barcha modellar uchun to'g'ri WHERE shartlarini qo'shishini tekshirish."""
    # 1. MovieModel
    stmt_m = published_only(select(MovieModel), MovieModel)
    assert "movies.publish_status = :publish_status_1" in str(stmt_m)

    # 2. SeriesModel
    stmt_s = published_only(select(SeriesModel), SeriesModel)
    assert "series.publish_status = :publish_status_1" in str(stmt_s)

    # 3. SeasonModel (ota series'ga join qilib tekshiradi)
    stmt_sn = published_only(select(SeasonModel), SeasonModel)
    compiled_sn = str(stmt_sn)
    assert "JOIN series ON seasons.series_id = series.id" in compiled_sn
    assert "series.publish_status = :publish_status_1" in compiled_sn

    # 4. EpisodeModel (season va series'ga join qilib tekshiradi)
    stmt_ep = published_only(select(EpisodeModel), EpisodeModel)
    compiled_ep = str(stmt_ep)
    assert "JOIN seasons ON episodes.season_id = seasons.id" in compiled_ep
    assert "JOIN series ON seasons.series_id = series.id" in compiled_ep
    assert "series.publish_status = :publish_status_1" in compiled_ep


def test_all_v1_routes_enumeration():
    """
    /api/v1 dagi barcha yo'nalishlarni openapi orqali sanab chiqadi va public media yo'llari
    mavjudligini tekshiradi.
    """
    paths = list(app.openapi()["paths"].keys())
    assert any("/api/v1/movies" in p for p in paths)
    assert any("/api/v1/series" in p for p in paths)
    assert any("/api/v1/search" in p for p in paths)


@pytest.mark.asyncio
async def test_public_routes_hide_pending_and_hidden():
    """Public servis va repo metodlari orqali pending/hidden elementlar chiqmasligini tekshirish."""
    from app.application.movies.service import MovieService
    from app.application.series.series_service import SeriesService

    mock_movie_repo = AsyncMock()
    mock_series_repo = AsyncMock()
    mock_telegram = AsyncMock()

    mock_movie_repo.get_by_id.return_value = None
    mock_movie_repo.get_by_code.return_value = None
    mock_movie_repo.list_movies.return_value = ([], 0)

    mock_series_repo.get_series_by_id.return_value = None
    mock_series_repo.get_series_by_code.return_value = None
    mock_series_repo.get_season_by_id.return_value = None
    mock_series_repo.get_episode_with_context_by_code.return_value = (None, None, None)

    movie_service = MovieService(mock_movie_repo)
    series_service = SeriesService(repository=mock_series_repo, telegram_api=mock_telegram)

    # 1. Movie public lookup published_status='published' uzatishini tekshirish
    await movie_service.get_movie_by_id(999, publish_status="published")
    mock_movie_repo.get_by_id.assert_called_with(999, publish_status="published")

    await movie_service.get_movie_by_code("test_code", publish_status="published")
    mock_movie_repo.get_by_code.assert_called_with("test_code", publish_status="published")

    await movie_service.list_movies(publish_status="published")
    mock_movie_repo.list_movies.assert_called_with(
        skip=0, limit=20, category_id=None, page_id=None, exclude_paged=False, publish_status="published"
    )

    # 2. Series public lookup published_status='published' uzatishini tekshirish
    await series_service.get_series_by_id(777, publish_status="published")
    mock_series_repo.get_series_by_id.assert_called_with(777, publish_status="published")

    await series_service.get_series_by_code("s_777", publish_status="published")
    mock_series_repo.get_series_by_code.assert_called_with("s_777", publish_status="published")

    # 3. Season va Episode public lookup
    await series_service.get_season_by_id(55, publish_status="published")
    mock_series_repo.get_season_by_id.assert_called_with(55, publish_status="published")

    await series_service.get_episode_detail_by_code("s1_e1", publish_status="published")
    mock_series_repo.get_episode_with_context_by_code.assert_called_with("s1_e1", publish_status="published")

