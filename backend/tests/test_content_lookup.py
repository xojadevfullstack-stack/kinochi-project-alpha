import pytest
from unittest.mock import patch, MagicMock
from app.infrastructure.external.tmdb_client import TMDbClient, tmdb_client


@pytest.mark.asyncio
async def test_tmdb_client_search_mock():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {
                "id": 19995,
                "title": "Avatar",
                "original_title": "Avatar",
                "release_date": "2009-12-16",
                "poster_path": "/kyeqWdyUXW608qlYkRqosgbbJyK.jpg",
                "overview": "Sinov tavsifi",
                "vote_average": 7.6,
            }
        ]
    }

    client = TMDbClient(api_key="mock_key")
    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        with patch("app.infrastructure.external.tmdb_client.get_cache", return_value=None):
            with patch("app.infrastructure.external.tmdb_client.set_cache", return_value=True):
                res = await client.search("Avatar", content_type="movie")
                assert len(res) == 1
                assert res[0]["tmdb_id"] == 19995
                assert res[0]["title"] == "Avatar"
                assert res[0]["release_year"] == 2009
                assert "https://image.tmdb.org/t/p/w500" in res[0]["poster_url"]


@pytest.mark.asyncio
async def test_tmdb_client_details_mock():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": 19995,
        "title": "Avatar",
        "original_title": "Avatar",
        "overview": "Avatar haqida tavsif",
        "release_date": "2009-12-16",
        "runtime": 162,
        "vote_average": 7.6,
        "poster_path": "/poster.jpg",
        "genres": [{"id": 28, "name": "Боевик"}],
        "credits": {
            "cast": [{"name": "Sem Uortington"}, {"name": "Zoi Saldana"}],
            "crew": [{"job": "Director", "name": "Jeyms Kemeron"}],
        },
        "videos": {
            "results": [
                {"site": "YouTube", "type": "Trailer", "key": "abc123xyz", "official": True}
            ]
        },
    }

    client = TMDbClient(api_key="mock_key")
    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        with patch("app.infrastructure.external.tmdb_client.get_cache", return_value=None):
            with patch("app.infrastructure.external.tmdb_client.set_cache", return_value=True):
                details = await client.get_details(19995, content_type="movie")
                assert details is not None
                assert details["tmdb_id"] == 19995
                assert details["director"] == "Jeyms Kemeron"
                assert "Sem Uortington" in details["cast"]
                assert details["trailer_url"] == "https://www.youtube.com/watch?v=abc123xyz"
                assert details["runtime"] == 162


@pytest.mark.asyncio
async def test_tmdb_client_search_numeric_id():
    client = TMDbClient(api_key="mock_key")
    mock_detail = {
        "tmdb_id": 550,
        "content_type": "movie",
        "title": "Fight Club",
        "original_title": "Fight Club",
        "release_year": 1999,
        "poster_url": "https://image.tmdb.org/t/p/w500/test.jpg",
        "overview": "Fight club overview",
        "tmdb_rating": 8.4,
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": []}

    with patch.object(client, "get_details", return_value=mock_detail):
        with patch("httpx.AsyncClient.get", return_value=mock_resp):
            with patch("app.infrastructure.external.tmdb_client.get_cache", return_value=None):
                with patch("app.infrastructure.external.tmdb_client.set_cache", return_value=True):
                    res = await client.search("550", content_type="movie")
                    assert len(res) == 1
                    assert res[0]["tmdb_id"] == 550
                    assert res[0]["title"] == "Fight Club"

