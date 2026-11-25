"""Tests for Slice 1 & 2: View tracking, analytics aggregation, and TMDb insights."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.infrastructure.security.jwt_handler import create_access_token
from app.infrastructure.db.models.admin_user import AdminUserModel
from app.infrastructure.db.models.content_request import ContentRequestModel
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel
from app.infrastructure.db.models.user import UserModel
from app.main import app


@pytest.mark.asyncio
async def test_media_view_event_model_and_record_view(db_session):
    """Recording views increments view_count and persists MediaViewEventModel rows."""
    from app.core.analytics import get_analytics_overview, record_media_view
    from app.infrastructure.db.models.media_view_event import MediaViewEventModel

    now = datetime.now(timezone.utc)
    user = UserModel(
        telegram_id=900001,
        username="viewer_one",
        first_name="Viewer",
        joined_at=now - timedelta(days=2),
        last_active_at=now,
    )
    movie = MovieModel(
        title="Oppenheimer",
        code="OPP01",
        short_code="9101",
        tmdb_id=872585,
        imdb_rating=8.4,
        publish_status="published",
    )
    series = SeriesModel(
        title="Severance",
        status="ongoing",
        tmdb_id=95396,
        imdb_rating=8.7,
        publish_status="published",
    )
    req = ContentRequestModel(
        title="Dune Messiah",
        media_type="movie",
        tmdb_id=999888,
        vote_count=12,
        status="pending",
    )
    db_session.add_all([user, movie, series, req])
    await db_session.commit()
    await db_session.refresh(movie)
    await db_session.refresh(series)

    assert movie.view_count == 0
    assert series.view_count == 0
    baseline_overview = await get_analytics_overview(db_session, days=7)
    base_total_views = baseline_overview["summary"]["total_views"]
    base_period_views = baseline_overview["summary"]["period_views"]
    base_bot = baseline_overview["summary"]["bot_views"]
    base_web = baseline_overview["summary"]["web_views"]
    base_stream = baseline_overview["summary"]["stream_views"]

    with patch("app.core.analytics.get_cache", new=AsyncMock(return_value=None)), patch(
        "app.core.analytics.set_cache", new=AsyncMock(return_value=True)
    ):
        recorded_bot = await record_media_view(
            db_session,
            media_type="movie",
            movie_id=movie.id,
            source="bot",
            user_id=user.id,
        )
        recorded_web = await record_media_view(
            db_session,
            media_type="movie",
            movie_id=movie.id,
            source="web",
            dedup_key="web:ip1:movie:" + str(movie.id),
        )
        recorded_series = await record_media_view(
            db_session,
            media_type="series",
            series_id=series.id,
            source="stream",
            user_id=user.id,
        )

    assert recorded_bot is True
    assert recorded_web is True
    assert recorded_series is True

    await db_session.refresh(movie)
    await db_session.refresh(series)
    assert movie.view_count == 2
    assert series.view_count == 1

    events = (await db_session.execute(select(MediaViewEventModel))).scalars().all()
    assert len(events) == 3

    overview = await get_analytics_overview(db_session, days=7)
    assert overview["summary"]["total_views"] == base_total_views + 3
    assert overview["summary"]["period_views"] == base_period_views + 3
    assert overview["summary"]["bot_views"] == base_bot + 1
    assert overview["summary"]["web_views"] == base_web + 1
    assert overview["summary"]["stream_views"] == base_stream + 1
    assert overview["summary"]["active_users_today"] >= 1
    assert overview["summary"]["pending_requests"] == 1
    assert overview["top_movies"][0]["id"] == movie.id
    assert overview["top_movies"][0]["period_views"] == 2
    assert overview["top_series"][0]["id"] == series.id
    assert overview["top_series"][0]["period_views"] == 1
    assert len(overview["top_requests"]) == 1
    assert overview["top_requests"][0]["title"] == "Dune Messiah"


@pytest.mark.asyncio
async def test_web_view_dedup_prevents_f5_inflation(db_session):
    """Repeated web views with same dedup key in cache window do not double-count."""
    from app.core.analytics import record_media_view

    movie = MovieModel(
        title="Dedup Test Movie",
        code="DDP01",
        publish_status="published",
    )
    db_session.add(movie)
    await db_session.commit()
    await db_session.refresh(movie)

    with patch("app.core.analytics.get_cache", new=AsyncMock(return_value="1")), patch(
        "app.core.analytics.set_cache", new=AsyncMock(return_value=True)
    ):
        recorded = await record_media_view(
            db_session,
            media_type="movie",
            movie_id=movie.id,
            source="web",
            dedup_key="web:ip1:movie:" + str(movie.id),
        )

    assert recorded is False
    await db_session.refresh(movie)
    assert movie.view_count == 0


@pytest.mark.asyncio
async def test_analytics_and_tmdb_insights_endpoints(db_session):
    """Admin endpoints return analytics overview and cross-referenced TMDb insights."""
    movie = MovieModel(
        title="Existing TMDb Movie",
        code="EXT01",
        short_code="4455",
        tmdb_id=101010,
        view_count=5,
        publish_status="published",
    )
    req = ContentRequestModel(
        title="Requested Upcoming",
        media_type="movie",
        tmdb_id=202020,
        vote_count=7,
        status="pending",
    )
    admin = AdminUserModel(
        email="analytics_admin@test.local",
        hashed_password="x",
        is_active=True,
        role="superadmin",
    )
    db_session.add_all([admin, movie, req])
    await db_session.commit()
    await db_session.refresh(admin)
    await db_session.refresh(movie)

    admin_token = create_access_token(str(admin.id), extra={"role": "superadmin"})
    headers = {"Authorization": f"Bearer {admin_token}"}

    mock_tmdb_feed = {
        "page": 1,
        "total_pages": 1,
        "total_results": 3,
        "results": [
            {
                "id": 101010,
                "media_type": "movie",
                "title": "Existing TMDb Movie",
                "release_date": "2026-10-01",
                "vote_average": 8.1,
                "popularity": 500.5,
                "poster_path": "/p1.jpg",
                "overview": "In library",
            },
            {
                "id": 202020,
                "media_type": "movie",
                "title": "Requested Upcoming",
                "release_date": "2026-12-15",
                "vote_average": 7.6,
                "popularity": 420.0,
                "poster_path": "/p2.jpg",
                "overview": "Requested by users",
            },
            {
                "id": 303030,
                "media_type": "movie",
                "title": "Brand New Premiere",
                "release_date": "2026-12-25",
                "vote_average": 7.9,
                "popularity": 380.2,
                "poster_path": "/p3.jpg",
                "overview": "Not in DB yet",
            },
        ],
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Public track-view endpoint
        with patch("app.core.analytics.get_cache", new=AsyncMock(return_value=None)), patch(
            "app.core.analytics.set_cache", new=AsyncMock(return_value=True)
        ):
            track_res = await client.post(
                "/api/v1/statistics/track-view",
                json={"media_type": "movie", "movie_id": movie.id, "source": "web"},
            )
        assert track_res.status_code == 200
        assert track_res.json()["recorded"] is True

        # Admin analytics overview
        with patch("app.api.v1.statistics.get_cache", new=AsyncMock(return_value=None)), patch(
            "app.api.v1.statistics.set_cache", new=AsyncMock(return_value=True)
        ):
            analytics_res = await client.get("/api/v1/statistics/analytics?days=7", headers=headers)
            assert analytics_res.status_code == 200
            payload = analytics_res.json()
            assert payload["days"] == 7
            assert "summary" in payload
            assert "top_movies" in payload
            assert "top_series" in payload
            assert "top_requests" in payload
            assert "daily_trend" in payload

        # Admin TMDb insights endpoint
        with patch("app.api.v1.statistics.get_cache", new=AsyncMock(return_value=None)), patch(
            "app.api.v1.statistics.set_cache", new=AsyncMock(return_value=True)
        ), patch(
            "app.infrastructure.external.tmdb_client.TMDbClient.get_feed",
            new=AsyncMock(return_value=mock_tmdb_feed),
        ):
            tmdb_res = await client.get(
                "/api/v1/statistics/tmdb-insights?category=upcoming",
                headers=headers,
            )
            assert tmdb_res.status_code == 200
            items = tmdb_res.json()["items"]
            assert len(items) == 3
            assert items[0]["in_library"] is True
            assert items[0]["library_code"] == "4455"
            assert items[1]["is_requested"] is True
            assert items[1]["request_votes"] == 7
            assert items[2]["in_library"] is False
            assert items[2]["is_requested"] is False


@pytest.mark.asyncio
async def test_watch_history_mark_movie_started_records_bot_view(db_session):
    """Bot sending a movie via mark_movie_started increments view_count with source='bot'."""
    from app.core.watch_history import mark_movie_started
    from app.infrastructure.db.models.media_view_event import MediaViewEventModel

    user = UserModel(telegram_id=900099, username="bot_watcher")
    movie = MovieModel(
        title="Bot Watched Movie",
        code="BOT01",
        publish_status="published",
    )
    db_session.add_all([user, movie])
    await db_session.commit()
    await db_session.refresh(movie)

    with patch("app.core.analytics.get_cache", new=AsyncMock(return_value=None)), patch(
        "app.core.analytics.set_cache", new=AsyncMock(return_value=True)
    ):
        await mark_movie_started(900099, movie.id)

    await db_session.refresh(movie)
    assert movie.view_count == 1
    events = (
        await db_session.execute(
            select(MediaViewEventModel).where(MediaViewEventModel.movie_id == movie.id)
        )
    ).scalars().all()
    assert len(events) == 1
    assert events[0].source == "bot"

