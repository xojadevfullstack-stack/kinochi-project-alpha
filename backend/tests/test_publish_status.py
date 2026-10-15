import pytest
from unittest.mock import AsyncMock, MagicMock
from app.domain.movies.entities import Movie
from app.domain.series.entities import Series
from app.application.movies.service import MovieService
from app.application.series.series_service import SeriesService


def test_movie_and_series_default_publish_status():
    """Yangi yaratilgan Movie va Series obyektlari default holatda pending bo'lishini tekshirish."""
    movie = Movie(id=1, title="Test Film", code="test1234")
    assert movie.publish_status == "pending"

    series = Series(
        id=1,
        title="Test Serial",
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-01T00:00:00"
    )
    assert series.publish_status == "pending"


@pytest.mark.asyncio
async def test_movie_service_publish_status_filter():
    """MovieService get_movie va search_movies da publish_status filtrini repo'ga to'g'ri uzatishini tekshirish."""
    mock_repo = AsyncMock()
    service = MovieService(mock_repo)

    # get_movie with publish_status="published"
    await service.get_movie(1, publish_status="published")
    mock_repo.get_by_id.assert_called_with(1, publish_status="published")

    # get_movie_by_code with publish_status="published"
    await service.get_movie_by_code("abc12345", publish_status="published")
    mock_repo.get_by_code.assert_called_with("abc12345", publish_status="published")

    # list_movies with publish_status="published"
    mock_repo.list_movies.return_value = ([], 0)
    await service.list_movies(publish_status="published")
    mock_repo.list_movies.assert_called_with(
        skip=0, limit=20, category_id=None, page_id=None, exclude_paged=False, publish_status="published"
    )

    # search_movies with publish_status="published"
    mock_repo.search_by_title.return_value = ([], 0)
    await service.search_movies("kino", publish_status="published")
    mock_repo.search_by_title.assert_called_with("kino", skip=0, limit=20, publish_status="published")


@pytest.mark.asyncio
async def test_series_service_publish_status_filter():
    """SeriesService get_series va search_series da publish_status filtrini repo'ga to'g'ri uzatishini tekshirish."""
    mock_repo = AsyncMock()
    mock_telegram = AsyncMock()
    service = SeriesService(repository=mock_repo, telegram_api=mock_telegram)

    mock_repo.get_series_by_id.return_value = None
    await service.get_series_by_id(10, publish_status="published")
    mock_repo.get_series_by_id.assert_called_with(10, publish_status="published")

    mock_repo.get_series_by_code.return_value = None
    await service.get_series_by_code("s_10", publish_status="published")
    mock_repo.get_series_by_code.assert_called_with("s_10", publish_status="published")

    mock_repo.get_all_series.return_value = ([], 0)
    await service.get_all_series(publish_status="published")
    mock_repo.get_all_series.assert_called_with(0, 100, None, None, False, publish_status="published")

    mock_repo.search_series.return_value = ([], 0)
    await service.search_series("serial", publish_status="published")
    mock_repo.search_series.assert_called_with("serial", 0, 100, publish_status="published")
