import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.api.deps import get_admin_or_bot, get_series_service
from app.domain.series.entities import Season, Series
from app.domain.series.source_entities import SourceResponse
from app.infrastructure.db.models.series import SeriesModel, SeasonModel


def test_series_model_seasons_order_by():
    """Verify that SeriesModel.seasons has explicit order_by for season_number."""
    order_by_clause = SeriesModel.seasons.property.order_by
    assert order_by_clause is not False
    assert len(order_by_clause) > 0
    # Check that season_number is part of the ordering clause
    col_str = str(order_by_clause[0])
    assert "season_number" in col_str


@pytest.mark.asyncio
async def test_create_season_with_announce_in_topic():
    app.dependency_overrides[get_admin_or_bot] = lambda: {"username": "admin", "role": "admin"}

    mock_source = SourceResponse(
        id=1,
        name="Topic Source",
        type="superguruh",
        chat_id=-1001234567,
        topic_id=456,
        created_at=datetime.now(),
    )
    mock_series = Series(
        id=5,
        title="Breaking Bad",
        release_year=2008,
        source_id=1,
        source=mock_source,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    mock_season = Season(
        id=12,
        series_id=5,
        season_number=2,
        title="2-mavsum",
        status="ongoing",
        created_at=datetime.now(),
    )

    with patch("app.infrastructure.telegram.telegram_client.telegram_client.send_topic_message", new_callable=AsyncMock) as mock_send_msg, \
         patch("app.api.v1.series.delete_cache_pattern", new_callable=AsyncMock):

        mock_srv = AsyncMock()
        mock_srv.create_season.return_value = mock_season
        mock_srv.get_series_by_id.return_value = mock_series
        app.dependency_overrides[get_series_service] = lambda: mock_srv

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            payload = {
                "series_id": 5,
                "season_number": 2,
                "title": "2-mavsum",
                "status": "ongoing",
            }
            resp = await ac.post("/api/v1/series/5/seasons?announce_in_topic=true", json=payload)
            assert resp.status_code == 201
            data = resp.json()
            assert data["id"] == 12
            assert data["season_number"] == 2

            mock_send_msg.assert_called_once()
            call_kwargs = mock_send_msg.call_args.kwargs
            assert call_kwargs["chat_id"] == -1001234567
            assert call_kwargs["message_thread_id"] == 456
            assert "2-FASL" in call_kwargs["text"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_announce_season_in_topic_endpoint():
    app.dependency_overrides[get_admin_or_bot] = lambda: {"username": "admin", "role": "admin"}

    mock_source = SourceResponse(
        id=1,
        name="Topic Source",
        type="superguruh",
        chat_id=-1001234567,
        topic_id=789,
        created_at=datetime.now(),
    )
    mock_series = Series(
        id=5,
        title="Breaking Bad",
        release_year=2008,
        source_id=1,
        source=mock_source,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    mock_season = Season(
        id=12,
        series_id=5,
        season_number=3,
        title="3-mavsum",
        status="ongoing",
        created_at=datetime.now(),
    )

    with patch("app.infrastructure.telegram.telegram_client.telegram_client.send_topic_message", new_callable=AsyncMock) as mock_send_msg:
        mock_srv = AsyncMock()
        mock_srv.get_series_by_id.return_value = mock_series
        mock_srv.get_season_by_id.return_value = mock_season
        app.dependency_overrides[get_series_service] = lambda: mock_srv

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/api/v1/series/5/seasons/12/announce")
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["season_number"] == 3
            assert data["topic_id"] == 789

            mock_send_msg.assert_called_once()
            call_kwargs = mock_send_msg.call_args.kwargs
            assert call_kwargs["chat_id"] == -1001234567
            assert call_kwargs["message_thread_id"] == 789
            assert "3-FASL" in call_kwargs["text"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_announce_season_no_topic_fails():
    app.dependency_overrides[get_admin_or_bot] = lambda: {"username": "admin", "role": "admin"}

    mock_series = Series(
        id=5,
        title="Breaking Bad",
        release_year=2008,
        source_id=None,
        source=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    mock_season = Season(
        id=12,
        series_id=5,
        season_number=1,
        title="1-mavsum",
        status="ongoing",
        created_at=datetime.now(),
    )

    mock_srv = AsyncMock()
    mock_srv.get_series_by_id.return_value = mock_series
    mock_srv.get_season_by_id.return_value = mock_season
    app.dependency_overrides[get_series_service] = lambda: mock_srv

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/series/5/seasons/12/announce")
        assert resp.status_code == 400
        assert "biriktirilmagan" in resp.json()["detail"]

    app.dependency_overrides.clear()
