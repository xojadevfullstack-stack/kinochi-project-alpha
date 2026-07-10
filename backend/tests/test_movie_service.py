import pytest
from unittest.mock import AsyncMock

from app.domain.movies.entities import Movie
from app.application.movies.service import MovieService


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_repo):
    return MovieService(mock_repo)


@pytest.mark.asyncio
async def test_create_movie(service, mock_repo):
    expected_movie = Movie(id=1, title="Test Movie", code="test1234")
    mock_repo.create.return_value = expected_movie
    mock_repo.get_by_code.return_value = None  # No collision

    result = await service.create_movie(title="Test Movie")
    
    assert result == expected_movie
    mock_repo.create.assert_called_once()
    args, kwargs = mock_repo.create.call_args
    assert args[0].title == "Test Movie"
    assert args[0].code is not None # Generated code
    assert len(args[0].code) == 6 # Length is 6
    assert kwargs.get("category_ids") is None
    mock_repo.get_by_code.assert_called_once()


@pytest.mark.asyncio
async def test_create_movie_with_collision(service, mock_repo):
    expected_movie = Movie(id=1, title="Test Movie", code="test1234")
    mock_repo.create.return_value = expected_movie
    # First call returns a movie (collision), second call returns None (success)
    mock_repo.get_by_code.side_effect = [Movie(id=2, title="Other", code="collid"), None]

    result = await service.create_movie(title="Test Movie")
    
    assert result == expected_movie
    assert mock_repo.get_by_code.call_count == 2
    mock_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_get_movie(service, mock_repo):
    expected_movie = Movie(id=1, title="Test Movie", code="test1234")
    mock_repo.get_by_id.return_value = expected_movie

    result = await service.get_movie(1)
    
    assert result == expected_movie
    mock_repo.get_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_search_movies(service, mock_repo):
    expected_movies = [Movie(id=1, title="Test Movie", code="test1234")]
    mock_repo.search_by_title.return_value = (expected_movies, 1)

    result_movies, result_total = await service.search_movies("Test")
    
    assert result_movies == expected_movies
    assert result_total == 1
    mock_repo.search_by_title.assert_called_once_with("Test", skip=0, limit=20)
