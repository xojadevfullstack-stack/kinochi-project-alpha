import pytest
import asyncio
from unittest.mock import patch, MagicMock
from app.infrastructure.external.tmdb_client import TMDbClient, TMDbRateLimiter


@pytest.mark.asyncio
async def test_tmdb_rate_limiter_basic():
    limiter = TMDbRateLimiter(requests_per_second=50.0, burst=5)
    # 5 tokens available immediately
    for _ in range(5):
        await limiter.acquire()
    assert limiter.tokens <= 1.0


@pytest.mark.asyncio
async def test_list_top_rated_movies():
    client = TMDbClient(api_key="mock_key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "page": 1,
        "results": [
            {
                "id": 278,
                "title": "Побег из Шоушенка",
                "original_title": "The Shawshank Redemption",
                "vote_average": 8.7,
                "vote_count": 26000,
                "release_date": "1994-09-23",
            }
        ],
        "total_pages": 500,
        "total_results": 10000,
    }

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        with patch("app.infrastructure.external.tmdb_client.get_cache", return_value=None):
            with patch("app.infrastructure.external.tmdb_client.set_cache", return_value=True):
                data = await client.list_top_rated("movie", page=1)
                assert data["page"] == 1
                assert len(data["results"]) == 1
                assert data["results"][0]["id"] == 278


@pytest.mark.asyncio
async def test_list_popular_tv():
    client = TMDbClient(api_key="mock_key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "page": 2,
        "results": [
            {
                "id": 1399,
                "name": "Игра престолов",
                "original_name": "Game of Thrones",
                "vote_average": 8.4,
                "vote_count": 22000,
                "first_air_date": "2011-04-17",
            }
        ],
        "total_pages": 100,
        "total_results": 2000,
    }

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        with patch("app.infrastructure.external.tmdb_client.get_cache", return_value=None):
            with patch("app.infrastructure.external.tmdb_client.set_cache", return_value=True):
                data = await client.list_popular("tv", page=2)
                assert data["page"] == 2
                assert len(data["results"]) == 1
                assert data["results"][0]["name"] == "Игра престолов"


@pytest.mark.asyncio
async def test_get_details_with_translations_and_external_ids():
    client = TMDbClient(api_key="mock_key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": 157336,
        "title": "Интерстеллар",
        "original_title": "Interstellar",
        "overview": "Olam bo'ylab sayohat",
        "release_date": "2014-11-05",
        "runtime": 169,
        "vote_average": 8.4,
        "vote_count": 34000,
        "popularity": 145.2,
        "poster_path": "/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
        "genres": [{"id": 12, "name": "Приключения"}, {"id": 18, "name": "Драма"}],
        "credits": {
            "cast": [{"name": "Metyu Makkonahi"}, {"name": "Enn Heteuey"}],
            "crew": [{"job": "Director", "name": "Kristofer Nolan"}],
        },
        "videos": {
            "results": [{"site": "YouTube", "type": "Trailer", "key": "zSWdZVtXT7E", "official": True}]
        },
        "translations": {
            "translations": [
                {"iso_639_1": "en", "data": {"title": "Interstellar"}},
                {"iso_639_1": "ru", "data": {"title": "Интерстеллар"}},
                {"iso_639_1": "uz", "data": {"title": "Yulduzlararo"}},
            ]
        },
        "external_ids": {
            "imdb_id": "tt0816692",
            "wikidata_id": "Q1344188",
        },
    }

    with patch("httpx.AsyncClient.get", return_value=mock_resp):
        with patch("app.infrastructure.external.tmdb_client.get_cache", return_value=None):
            with patch("app.infrastructure.external.tmdb_client.set_cache", return_value=True):
                details = await client.get_details(157336, kind="movie")
                assert details is not None
                assert details["tmdb_id"] == 157336
                assert details["title_ru"] == "Интерстелlar" or "Интерстеллар" in details["title_ru"]
                assert details["title_en"] == "Interstellar"
                assert details["title_uz"] == "Yulduzlararo"
                assert details["imdb_id"] == "tt0816692"
                assert details["director"] == "Kristofer Nolan"
                assert details["vote_count"] == 34000


@pytest.mark.asyncio
async def test_retry_on_429():
    client = TMDbClient(api_key="mock_key")

    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.headers = {"Retry-After": "0.1"}

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.json.return_value = {"page": 1, "results": [{"id": 1, "title": "Test"}]}

    with patch("httpx.AsyncClient.get", side_effect=[resp_429, resp_200]):
        with patch("app.infrastructure.external.tmdb_client.get_cache", return_value=None):
            with patch("app.infrastructure.external.tmdb_client.set_cache", return_value=True):
                data = await client.list_popular("movie", page=1)
                assert len(data["results"]) == 1
                assert data["results"][0]["title"] == "Test"
