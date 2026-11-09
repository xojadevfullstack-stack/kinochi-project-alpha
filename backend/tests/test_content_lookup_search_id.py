import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_admin
from app.infrastructure.external.tmdb_client import tmdb_client


@pytest.fixture
def admin_client():
    app.dependency_overrides[get_current_admin] = lambda: {"username": "admin", "role": "admin"}
    original_key = tmdb_client._api_key
    tmdb_client._api_key = "valid_test_key"
    client = TestClient(app)
    yield client
    tmdb_client._api_key = original_key
    app.dependency_overrides.pop(get_current_admin, None)


def test_search_content_by_numeric_id_for_anime(admin_client):
    """Assertion: Searching by numeric TMDb ID for anime (260463) finds Daemons of the Shadow Realm (TV/series)."""
    mock_tv_details = {
        "tmdb_id": 260463,
        "content_type": "series",
        "title": "Tsugai zagrobnogo mira",
        "original_title": "Yomi no Tsugai",
        "release_year": 2026,
        "poster_url": "https://image.tmdb.org/t/p/w500/vIE1llfr1lcmzlsV4xn8vhgtlQN.jpg",
        "overview": "Daemons of the Shadow Realm anime series",
        "tmdb_rating": 8.5,
        "adult": False,
    }
    mock_movie_details = {
        "tmdb_id": 260463,
        "content_type": "movie",
        "title": "Vénus aveugle",
        "original_title": "Vénus aveugle",
        "release_year": 1941,
        "poster_url": "https://image.tmdb.org/t/p/w500/venus.jpg",
        "overview": "Clarisse learns that she will go blind...",
        "tmdb_rating": 6.2,
        "adult": False,
    }

    async def fake_get_details(tmdb_id: int, kind: str = "movie", **kwargs):
        if tmdb_id == 260463:
            return mock_tv_details if kind in ("tv", "series") else mock_movie_details
        return None

    with patch("app.infrastructure.external.tmdb_client.tmdb_client.get_details", side_effect=fake_get_details):
        resp = admin_client.get(
            "/api/v1/content-lookup/search",
            params={"q": "260463", "type": "anime"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert len(data) >= 1
        # Because type is anime, the TV series must be first
        first_item = data[0]
        assert first_item["tmdb_id"] == 260463
        assert first_item["content_type"] in ("series", "tv")
        assert first_item["title"] == "Tsugai zagrobnogo mira"
        assert first_item["poster_url"] == "https://image.tmdb.org/t/p/w500/vIE1llfr1lcmzlsV4xn8vhgtlQN.jpg"

        # The secondary movie result must also be included so user has full visibility
        if len(data) > 1:
            second_item = data[1]
            assert second_item["tmdb_id"] == 260463
            assert second_item["content_type"] == "movie"
            assert second_item["title"] == "Vénus aveugle"


def test_search_content_fallback_between_movie_and_tv(admin_client):
    """Assertion: When search in preferred endpoint returns empty, it falls back to the other endpoint."""
    async def fake_request(endpoint: str, params=None, **kwargs):
        if "search/tv" in endpoint and "Daemons" in (params or {}).get("query", ""):
            return {
                "results": [
                    {
                        "id": 260463,
                        "name": "Daemons of the Shadow Realm",
                        "original_name": "Yomi no Tsugai",
                        "first_air_date": "2026-01-01",
                        "poster_path": "/vIE1llfr1lcmzlsV4xn8vhgtlQN.jpg",
                        "overview": "Anime series",
                        "vote_average": 8.5,
                    }
                ]
            }
        return {"results": []}

    with patch("app.infrastructure.external.tmdb_client.tmdb_client._request_with_retry", side_effect=fake_request):
        # Querying with type="movie" should fallback to "tv" and still find Daemons of the Shadow Realm
        resp = admin_client.get(
            "/api/v1/content-lookup/search",
            params={"q": "Daemons of the Shadow Realm", "type": "movie"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == 260463
        assert data[0]["title"] == "Daemons of the Shadow Realm"
        assert data[0]["content_type"] == "series"
