"""Tests for search_count, POST /search/track-click, and GET /search/popular."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel
from app.main import app


@pytest.mark.asyncio
async def test_search_track_click_and_popular_ranking(db_session):
    """track-click increments search_count with dedup, popular orders by search_count > view_count > rating."""
    m_low = MovieModel(
        title="Low Search Movie",
        code="LOW01",
        short_code="7001",
        imdb_rating=9.2,
        view_count=1,
        search_count=0,
        publish_status="published",
    )
    m_top = MovieModel(
        title="Most Searched Movie",
        code="TOP01",
        short_code="7002",
        imdb_rating=7.5,
        view_count=10,
        search_count=4,
        publish_status="published",
    )
    m_adult = MovieModel(
        title="Adult Movie",
        code="ADL01",
        short_code="7003",
        imdb_rating=8.9,
        search_count=99,
        is_18_plus=True,
        publish_status="published",
    )
    m_pending = MovieModel(
        title="Pending Movie",
        code="PND01",
        search_count=50,
        publish_status="pending",
    )
    s_pop = SeriesModel(
        title="Popular Searched Series",
        status="ongoing",
        imdb_rating=8.6,
        view_count=20,
        search_count=6,
        publish_status="published",
    )
    db_session.add_all([m_low, m_top, m_adult, m_pending, s_pop])
    await db_session.commit()
    await db_session.refresh(m_top)
    await db_session.refresh(s_pop)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Track a click on m_top (cache miss -> recorded=True)
        with patch("app.api.v1.search.get_cache", new=AsyncMock(return_value=None)), patch(
            "app.api.v1.search.set_cache", new=AsyncMock(return_value=True)
        ), patch("app.api.v1.search.delete_cache_pattern", new=AsyncMock(return_value=None)):
            res_click = await client.post(
                "/api/v1/search/track-click",
                json={"media_type": "movie", "item_id": m_top.id},
            )
            assert res_click.status_code == 200
            assert res_click.json()["recorded"] is True

        # 2. Duplicate click inside 1h window (cache hit -> recorded=False)
        with patch("app.api.v1.search.get_cache", new=AsyncMock(return_value="1")):
            res_dup = await client.post(
                "/api/v1/search/track-click",
                json={"media_type": "movie", "item_id": m_top.id},
            )
            assert res_dup.status_code == 200
            assert res_dup.json()["recorded"] is False

        # 3. GET /search/popular with include_adult=false excludes adult & pending
        with patch("app.api.v1.search.get_cache", new=AsyncMock(return_value=None)), patch(
            "app.api.v1.search.set_cache", new=AsyncMock(return_value=True)
        ):
            res_pop = await client.get("/api/v1/search/popular?limit=8&include_adult=false")
            assert res_pop.status_code == 200
            data = res_pop.json()
            titles = [item["title"] for item in data["results"]]
            assert "Adult Movie" not in titles
            assert "Pending Movie" not in titles
            assert titles[0] == "Popular Searched Series"
            assert titles[1] == "Most Searched Movie"
            assert data["results"][1]["search_count"] == 5

        # 4. GET /search/popular with include_adult=true includes adult movie first (search_count=99)
        with patch("app.api.v1.search.get_cache", new=AsyncMock(return_value=None)), patch(
            "app.api.v1.search.set_cache", new=AsyncMock(return_value=True)
        ):
            res_adult = await client.get("/api/v1/search/popular?limit=8&include_adult=true")
            assert res_adult.status_code == 200
            assert res_adult.json()["results"][0]["title"] == "Adult Movie"
