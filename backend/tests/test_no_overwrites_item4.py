"""Tests for Item 4: No overwrites and cross-title uniqueness."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.infrastructure.db.repositories.movie_repo import MovieRepositoryImpl
from app.infrastructure.db.repositories.series_repository import SeriesRepository
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import EpisodeModel, SeasonModel, SeriesModel
from app.infrastructure.db.models.translation import MovieTranslationModel, EpisodeTranslationModel
from app.api.deps import get_db_session, get_admin_or_bot
from tests.conftest import configure_mock_session


@pytest.mark.asyncio
async def test_movie_repo_no_overwrite_existing_translation():
    """Mavjud kino tarjimasi videosini yangisiga almashtirish taqiqlangan bo'lishi shart."""
    session = AsyncMock(spec=AsyncSession)
    repo = MovieRepositoryImpl(session)

    existing_tr = MagicMock(spec=MovieTranslationModel)
    existing_tr.telegram_file_id = "file_old_123"
    existing_tr.storage_channel_message_id = 1001

    res_mock = MagicMock()
    res_mock.scalar_one_or_none.return_value = existing_tr
    session.execute.return_value = res_mock

    with pytest.raises(ValueError, match="Mavjud kino tarjimasini almashtirish taqiqlangan"):
        await repo.add_translation(
            movie_id=1,
            language="O'zbekcha",
            telegram_file_id="file_new_456",
            storage_channel_message_id=1002
        )


@pytest.mark.asyncio
async def test_series_repo_no_overwrite_existing_episode_translation():
    """Mavjud qism videosini yangisiga almashtirish taqiqlangan bo'lishi shart."""
    session = AsyncMock(spec=AsyncSession)
    repo = SeriesRepository(session)

    existing_tr = MagicMock(spec=EpisodeTranslationModel)
    existing_tr.telegram_file_id = "file_old_123"
    existing_tr.storage_channel_message_id = 1001

    res_mock = MagicMock()
    res_mock.scalar_one_or_none.return_value = existing_tr
    session.execute.return_value = res_mock

    with pytest.raises(ValueError, match="Mavjud qism videosini almashtirish taqiqlangan"):
        await repo.add_episode_translation(
            episode_id=1,
            language="O'zbekcha",
            telegram_file_id="file_new_456",
            storage_channel_message_id=1002
        )


@pytest.mark.asyncio
async def test_movie_repo_cross_title_duplicate_rejected():
    """Boshqa kinoga biriktirilgan faylni yangi kinoga biriktirish taqiqlangan bo'lishi shart."""
    session = AsyncMock(spec=AsyncSession)
    repo = MovieRepositoryImpl(session)

    # 1-so'rov: existing_tr (None)
    res_existing = MagicMock()
    res_existing.scalar_one_or_none.return_value = None

    # 2-so'rov: other_movie_stmt (boshqa kinoda topildi)
    other_movie_tr = MagicMock(spec=MovieTranslationModel)
    other_movie_tr.movie_id = 99
    res_other = MagicMock()
    res_other.scalar_one_or_none.return_value = other_movie_tr

    session.execute.side_effect = [res_existing, res_other]

    with pytest.raises(ValueError, match="boshqa kinoga biriktirilgan"):
        await repo.add_translation(
            movie_id=1,
            language="O'zbekcha",
            telegram_file_id="duplicate_file_id",
            storage_channel_message_id=5000
        )


@pytest.mark.asyncio
async def test_series_reserve_episodes_reforwarded_duplicate_does_not_create_episode():
    """Qayta forward qilingan (re-forwarded duplicate) xabar yangi qism yaratmasligi kerak."""
    session = AsyncMock(spec=AsyncSession)
    repo = SeriesRepository(session)

    mock_season = MagicMock()
    mock_season.id = 10
    mock_season.season_number = 1

    # Season lock
    res_season = MagicMock()
    res_season.scalar_one_or_none.return_value = mock_season

    # Existing episode with source_message_id = 777
    existing_ep = MagicMock()
    existing_ep.id = 55
    existing_ep.episode_number = 1
    existing_ep.code = "ep_code_1"
    existing_ep.display_code = "S1-CH1"
    existing_ep.source_message_id = 777
    existing_ep.translations = []

    res_episodes = MagicMock()
    res_episodes.scalars.return_value.all.return_value = [existing_ep]

    session.execute.side_effect = [res_season, res_episodes]

    # Dublikat xabar yuborilmoqda (source_message_id = 777)
    items = [{
        "source_message_id": 777,
        "explicit_episode_number": None,
        "telegram_file_id": None,
        "title": "1-qism"
    }]

    reserved = await repo.reserve_episodes_atomic(season_id=10, items=items)
    assert len(reserved) == 1
    assert reserved[0]["is_duplicate"] is True
    assert reserved[0]["id"] == 55
    assert reserved[0]["episode_number"] == 1
    # session.add chaqirilmagan bo'lishi kerak (yangi qism yaratilmadi)
    assert not session.add.called


@pytest.mark.asyncio
async def test_link_movie_video_endpoint_returns_409_on_overwrite():
    """Mavjud videoni qayta bog'lamoqchi bo'lganda /movies/{id}/link-video 409 Conflict qaytarishi kerak."""
    mock_session = AsyncMock(spec=AsyncSession)
    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_admin_or_bot] = lambda: {"role": "admin"}

    try:
        mock_movie = MagicMock(spec=MovieModel)
        mock_movie.id = 1
        mock_movie.title = "Test Movie"
        mock_movie.runtime = None
        mock_movie.translations = []
        mock_session.get.return_value = mock_movie
        configure_mock_session(mock_session, scalar=None, rows=[])

        with patch("app.application.movies.service.MovieService.link_movie_video_from_message", side_effect=ValueError("Mavjud kino tarjimasini almashtirish taqiqlangan (No overwrite)")):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/v1/movies/1/link-video", json={
                    "message_id": 999,
                    "language": "O'zbekcha",
                    "telegram_file_id": "file_123",
                    "duration": 3600
                })
                assert resp.status_code == status.HTTP_409_CONFLICT
                data = resp.json()
                assert data["detail"]["defect"] == "no_overwrite"
                assert mock_session.commit.called
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        app.dependency_overrides.pop(get_admin_or_bot, None)


@pytest.mark.asyncio
async def test_link_episode_video_endpoint_returns_409_on_overwrite():
    """Mavjud qism videosini qayta bog'lamoqchi bo'lganda /series/episodes/{id}/link-video 409 Conflict qaytarishi kerak."""
    mock_session = AsyncMock(spec=AsyncSession)
    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_admin_or_bot] = lambda: {"role": "admin"}

    try:
        mock_ep = MagicMock(spec=EpisodeModel)
        mock_ep.id = 1
        mock_ep.season_id = 1
        mock_ep.episode_number = 1
        mock_ep.title = "1-qism"
        mock_season = MagicMock(spec=SeasonModel)
        mock_season.id = 1
        mock_season.series_id = 1
        mock_season.season_number = 1
        mock_series = MagicMock(spec=SeriesModel)
        mock_series.id = 1
        mock_series.publish_status = "published"
        mock_session.get.side_effect = lambda model, id_: mock_ep if model == EpisodeModel else (mock_season if model == SeasonModel else mock_series)
        configure_mock_session(mock_session, scalar=None, rows=[])

        with patch("app.application.series.series_service.SeriesService.link_episode_video_from_message", side_effect=ValueError("Mavjud qism videosini almashtirish taqiqlangan (No overwrite)")):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/v1/series/episodes/1/link-video", json={
                    "message_id": 999,
                    "language": "O'zbekcha",
                    "telegram_file_id": "file_123",
                    "duration": 2400
                })
                assert resp.status_code == status.HTTP_409_CONFLICT
                data = resp.json()
                assert data["detail"]["defect"] == "no_overwrite"
                assert mock_session.commit.called
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        app.dependency_overrides.pop(get_admin_or_bot, None)
