"""Tests for Item 18: Admin-only explicit video replace with mandatory reason."""
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


@pytest.mark.asyncio
async def test_movie_repo_allow_replace_updates_translation():
    """allow_replace=True bo'lganda mavjud tarjimaning video fayli va xabar ID yangilanadi."""
    session = AsyncMock(spec=AsyncSession)
    repo = MovieRepositoryImpl(session)

    existing_tr = MagicMock(spec=MovieTranslationModel)
    existing_tr.movie_id = 1
    existing_tr.language = "O'zbekcha"
    existing_tr.telegram_file_id = "old_file_111"
    existing_tr.storage_channel_message_id = 100

    # 1-so'rov: existing_tr
    res_mock = MagicMock()
    res_mock.scalar_one_or_none.return_value = existing_tr

    # 2 & 3: cross-title check (boshqa kinoda yo'q)
    res_empty1 = MagicMock()
    res_empty1.scalar_one_or_none.return_value = None
    res_empty2 = MagicMock()
    res_empty2.scalar_one_or_none.return_value = None
    res_empty3 = MagicMock()
    res_empty3.scalar_one_or_none.return_value = None
    res_empty4 = MagicMock()
    res_empty4.scalar_one_or_none.return_value = None

    # get_by_id uchun
    mock_movie = MagicMock(spec=MovieModel)
    mock_movie.id = 1
    mock_movie.title = "Test Movie"
    mock_movie.translations = [existing_tr]
    res_movie = MagicMock()
    res_movie.scalar_one_or_none.return_value = mock_movie

    session.execute.side_effect = [res_mock, res_empty1, res_empty2, res_empty3, res_empty4, res_movie]

    with patch.object(repo, "get_by_id", return_value=mock_movie):
        res = await repo.add_translation(
            movie_id=1,
            language="O'zbekcha",
            telegram_file_id="new_file_222",
            storage_channel_message_id=200,
            allow_replace=True
        )
        assert existing_tr.telegram_file_id == "new_file_222"
        assert existing_tr.storage_channel_message_id == 200
        assert session.flush.called


@pytest.mark.asyncio
async def test_series_repo_allow_replace_updates_episode_translation():
    """allow_replace=True bo'lganda mavjud qismning video fayli va xabar ID yangilanadi."""
    session = AsyncMock(spec=AsyncSession)
    repo = SeriesRepository(session)

    existing_tr = MagicMock(spec=EpisodeTranslationModel)
    existing_tr.episode_id = 5
    existing_tr.language = "O'zbekcha"
    existing_tr.telegram_file_id = "old_ep_file"
    existing_tr.storage_channel_message_id = 300

    res_mock = MagicMock()
    res_mock.scalar_one_or_none.return_value = existing_tr

    res_empty1 = MagicMock()
    res_empty1.scalar_one_or_none.return_value = None
    res_empty2 = MagicMock()
    res_empty2.scalar_one_or_none.return_value = None
    res_empty3 = MagicMock()
    res_empty3.scalar_one_or_none.return_value = None
    res_empty4 = MagicMock()
    res_empty4.scalar_one_or_none.return_value = None

    session.execute.side_effect = [res_mock, res_empty1, res_empty2, res_empty3, res_empty4]

    with patch.object(repo, "get_episode_by_id", return_value=MagicMock()):
        await repo.add_episode_translation(
            episode_id=5,
            language="O'zbekcha",
            telegram_file_id="new_ep_file",
            storage_channel_message_id=400,
            allow_replace=True
        )
        assert existing_tr.telegram_file_id == "new_ep_file"
        assert existing_tr.storage_channel_message_id == 400
        assert session.flush.called


@pytest.mark.asyncio
async def test_link_movie_video_endpoint_admin_replace_success():
    """Admin replace=true va reason berganda video muvaffaqiyatli almashtiriladi."""
    mock_session = AsyncMock(spec=AsyncSession)
    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_admin_or_bot] = lambda: {"role": "admin"}

    mock_movie = MagicMock(spec=MovieModel)
    mock_movie.id = 1
    mock_movie.title = "Inception"
    mock_movie.runtime = 148
    mock_movie.translations = []
    mock_session.get.return_value = mock_movie

    try:
        from app.domain.movies.entities import Movie
        mock_domain_movie = Movie(
            id=1,
            title="Inception",
            code="inc123",
            publish_status="published",
            translations=[],
            categories=[],
            pages=[]
        )
        with patch("app.application.movies.service.MovieService.link_movie_video_from_message", return_value=mock_domain_movie) as mock_link:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/v1/movies/1/link-video", json={
                    "message_id": 555,
                    "language": "O'zbekcha",
                    "telegram_file_id": "file_new_555",
                    "replace": True,
                    "reason": "Sifatliroq 1080p variant yuklandi"
                })
                assert resp.status_code == status.HTTP_200_OK
                mock_link.assert_called_once_with(
                    1, 555, "O'zbekcha", source_url=None, telegram_file_id="file_new_555", allow_replace=True
                )
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        app.dependency_overrides.pop(get_admin_or_bot, None)


@pytest.mark.asyncio
async def test_link_movie_video_endpoint_replace_missing_reason_rejected():
    """Admin replace=true qilib lekin sabab (reason) bermasa 400 Bad Request qaytariladi."""
    mock_session = AsyncMock(spec=AsyncSession)
    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_admin_or_bot] = lambda: {"role": "admin"}

    mock_movie = MagicMock(spec=MovieModel)
    mock_movie.id = 1
    mock_movie.translations = []
    mock_session.get.return_value = mock_movie

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/v1/movies/1/link-video", json={
                "message_id": 555,
                "language": "O'zbekcha",
                "telegram_file_id": "file_new_555",
                "replace": True,
                "reason": ""  # Bo'sh sabab
            })
            assert resp.status_code == status.HTTP_400_BAD_REQUEST
            assert "sabab (reason)" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        app.dependency_overrides.pop(get_admin_or_bot, None)


@pytest.mark.asyncio
async def test_link_movie_video_endpoint_non_admin_cannot_replace():
    """Bot yoki admin bo'lmagan foydalanuvchi replace=true so'rasa 403 Forbidden beriladi."""
    mock_session = AsyncMock(spec=AsyncSession)
    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_admin_or_bot] = lambda: {"role": "bot"}

    mock_movie = MagicMock(spec=MovieModel)
    mock_movie.id = 1
    mock_movie.translations = []
    mock_session.get.return_value = mock_movie

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/v1/movies/1/link-video", json={
                "message_id": 555,
                "language": "O'zbekcha",
                "telegram_file_id": "file_new_555",
                "replace": True,
                "reason": "Avtomatik almashtirish urinishi"
            })
            assert resp.status_code == status.HTTP_403_FORBIDDEN
            assert "Faqat admin" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        app.dependency_overrides.pop(get_admin_or_bot, None)


@pytest.mark.asyncio
async def test_link_episode_video_endpoint_admin_replace_success():
    """Admin serial qismini replace=true va reason bilan almashtirishi mumkin."""
    mock_session = AsyncMock(spec=AsyncSession)
    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_admin_or_bot] = lambda: {"role": "admin"}

    mock_ep = MagicMock(spec=EpisodeModel)
    mock_ep.id = 10
    mock_ep.season_id = 2
    mock_ep.episode_number = 1
    mock_ep.title = "1-qism"

    mock_season = MagicMock(spec=SeasonModel)
    mock_season.id = 2
    mock_season.series_id = 3
    mock_season.season_number = 1

    mock_series = MagicMock(spec=SeriesModel)
    mock_series.id = 3
    mock_series.publish_status = "published"

    mock_session.get.side_effect = lambda model, id_: mock_ep if model == EpisodeModel else (mock_season if model == SeasonModel else mock_series)

    try:
        from datetime import datetime, timezone
        from app.domain.series.entities import Episode
        mock_domain_ep = Episode(
            id=10,
            season_id=2,
            episode_number=1,
            code="c_10",
            display_code="S1-CH1",
            title="1-qism",
            created_at=datetime.now(timezone.utc),
            translations=[]
        )
        with patch("app.application.series.series_service.SeriesService.link_episode_video_from_message", return_value=mock_domain_ep) as mock_link:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/api/v1/series/episodes/10/link-video", json={
                    "message_id": 666,
                    "language": "O'zbekcha",
                    "telegram_file_id": "file_ep_666",
                    "replace": True,
                    "reason": "Qism to'liq ovozli dublyajga almashtirildi"
                })
                assert resp.status_code == status.HTTP_200_OK
                mock_link.assert_called_once_with(
                    10, 666, "O'zbekcha", source_url=None, telegram_file_id="file_ep_666", allow_replace=True
                )
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        app.dependency_overrides.pop(get_admin_or_bot, None)


@pytest.mark.asyncio
async def test_link_episode_video_endpoint_non_admin_cannot_replace():
    """Bot serial qismini replace=true bilan almashtira olmaydi (403 Forbidden)."""
    mock_session = AsyncMock(spec=AsyncSession)
    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_admin_or_bot] = lambda: {"role": "bot"}

    mock_ep = MagicMock(spec=EpisodeModel)
    mock_ep.id = 10
    mock_session.get.return_value = mock_ep

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/v1/series/episodes/10/link-video", json={
                "message_id": 666,
                "language": "O'zbekcha",
                "telegram_file_id": "file_ep_666",
                "replace": True,
                "reason": "Bot orqali urinish"
            })
            assert resp.status_code == status.HTTP_403_FORBIDDEN
            assert "Faqat admin" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        app.dependency_overrides.pop(get_admin_or_bot, None)
