import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.deps import get_current_admin, get_db_session
from app.infrastructure.db.models.movie import MovieModel


@pytest.mark.asyncio
async def test_check_duplicates_endpoint_none_found():
    app.dependency_overrides[get_current_admin] = lambda: {"username": "admin", "role": "admin"}

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db_session] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(
            "/api/v1/content-lookup/duplicates",
            params={"title": "NonExistentFilm123", "tmdb_id": 99999999}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["exact"] == []
        assert data["similar"] == []

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_check_duplicates_endpoint_exact_found():
    app.dependency_overrides[get_current_admin] = lambda: {"username": "admin", "role": "admin"}

    mock_movie = MovieModel(
        id=42,
        title="Avatar",
        code="4821",
        release_year=2009,
        tmdb_id=19995
    )

    mock_session = AsyncMock()
    # First query is for exact movies by tmdb_id
    mock_result_exact = MagicMock()
    mock_result_exact.scalars.return_value.all.return_value = [mock_movie]

    # Remaining queries (series, similar) return empty
    mock_result_empty = MagicMock()
    mock_result_empty.scalars.return_value.all.return_value = []

    mock_session.execute.side_effect = [
        mock_result_exact, # movie tmdb_id query
        mock_result_empty, # series tmdb_id query
        mock_result_empty, # movie similar query
        mock_result_empty, # series similar query
    ]

    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db_session] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(
            "/api/v1/content-lookup/duplicates",
            params={"title": "Avatar", "tmdb_id": 19995}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["exact"]) == 1
        assert data["exact"][0]["id"] == 42
        assert data["exact"][0]["title"] == "Avatar"
        assert data["exact"][0]["code"] == "4821"

    app.dependency_overrides.clear()
