from unittest.mock import MagicMock
import pytest

from app.domain.movies.entities import Movie
from app.domain.series.entities import EpisodeCreate, SeasonCreate, SeriesCreate
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.repositories.movie_repo import MovieRepositoryImpl
from app.infrastructure.db.repositories.series_repository import SeriesRepository
from app.application.series.series_service import SeriesService


@pytest.mark.asyncio
async def test_global_short_code_sequence_spans_movies_and_episodes_without_collision(db_session):
    movie_repo = MovieRepositoryImpl(db_session)
    series_repo = SeriesRepository(db_session)
    series_service = SeriesService(series_repo, MagicMock())

    m1 = await movie_repo.create(Movie(title="Kino Bir", code="KINO01", publish_status="published"))
    ser = await series_repo.create_series(SeriesCreate(title="Serial Bir", publish_status="published"))
    seas = await series_repo.create_season(SeasonCreate(series_id=ser.id, season_number=1))
    ep1 = await series_service.create_episode(EpisodeCreate(season_id=seas.id, episode_number=1, title="1-qism"))
    m2 = await movie_repo.create(Movie(title="Kino Ikki", code="KINO02", publish_status="published"))
    ep2 = await series_service.create_episode(EpisodeCreate(season_id=seas.id, episode_number=2, title="2-qism"))
    await db_session.commit()

    codes = [m1.short_code, ep1.short_code, m2.short_code, ep2.short_code]
    assert all(c is not None and c.isdigit() for c in codes)
    nums = [int(c) for c in codes]
    assert nums == [nums[0], nums[0] + 1, nums[0] + 2, nums[0] + 3]


@pytest.mark.asyncio
async def test_episode_short_code_not_hijacked_by_movie_numeric_id_collision(db_session):
    movie_repo = MovieRepositoryImpl(db_session)
    series_repo = SeriesRepository(db_session)
    series_service = SeriesService(series_repo, MagicMock())

    ser = await series_repo.create_series(SeriesCreate(title="Qasos Serial", publish_status="published"))
    seas = await series_repo.create_season(SeasonCreate(series_id=ser.id, season_number=1))
    ep = await series_service.create_episode(EpisodeCreate(season_id=seas.id, episode_number=1, title="1-qism"))
    ep_short = int(ep.short_code)

    # Create a movie whose database id equals the episode's short_code, while its own short_code differs
    m_collide = MovieModel(
        id=ep_short,
        title="Id Collision Film",
        code="COLL99",
        short_code="9999",
        publish_status="published",
    )
    db_session.add(m_collide)
    await db_session.commit()

    # Lookup on movie repository MUST NOT steal episode's short_code via MovieModel.id fallback
    found_movie = await movie_repo.get_by_code(str(ep_short), publish_status="published")
    assert found_movie is None

    # Lookup on episode context / API resolves the exact episode by short_code
    found_ep, found_seas, found_ser = await series_repo.get_episode_with_context_by_code(
        str(ep_short), publish_status="published"
    )
    assert found_ep is not None and found_ep.id == ep.id
    assert found_ser is not None and found_ser.id == ser.id
    assert found_seas is not None and found_seas.id == seas.id


@pytest.mark.asyncio
async def test_episode_code_endpoint_resolves_short_code(client, db_session):
    series_repo = SeriesRepository(db_session)
    series_service = SeriesService(series_repo, MagicMock())

    ser = await series_repo.create_series(SeriesCreate(title="Test Serial", publish_status="published"))
    seas = await series_repo.create_season(SeasonCreate(series_id=ser.id, season_number=1))
    ep = await series_service.create_episode(EpisodeCreate(season_id=seas.id, episode_number=1, title="1-qism"))
    await db_session.commit()

    resp = client.get(f"/api/v1/series/episodes/code/{ep.short_code}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == ep.id
    assert body["short_code"] == ep.short_code
    assert body["series_id"] == ser.id
