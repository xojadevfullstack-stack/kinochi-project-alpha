import pytest
from unittest.mock import AsyncMock
from app.application.series.series_service import SeriesService
from app.infrastructure.db.repositories.series_repository import SeriesRepository
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel
from app.infrastructure.db.models.translation import EpisodeTranslationModel

@pytest.mark.asyncio
async def test_get_episode_detail_by_code_optimized(db_session):
    """get_episode_detail_by_code optimallashtirilgan tezkor usulda prev/next va kontekstni to'g'ri qaytarishi shart."""
    # 1. Test ma'lumotlarini yaratish
    series = SeriesModel(
        title="Test Serial",
        publish_status="published"
    )
    db_session.add(series)
    await db_session.flush()

    season = SeasonModel(
        series_id=series.id,
        season_number=1,
        title="1-Mavsum"
    )
    db_session.add(season)
    await db_session.flush()

    ep1 = EpisodeModel(
        season_id=season.id,
        episode_number=1,
        code="EP1CODE1",
        display_code="S1-CH1",
        title="1-qism"
    )
    ep2 = EpisodeModel(
        season_id=season.id,
        episode_number=2,
        code="EP2CODE2",
        display_code="S1-CH2",
        title="2-qism"
    )
    db_session.add_all([ep1, ep2])
    await db_session.flush()

    tr1 = EpisodeTranslationModel(
        episode_id=ep1.id,
        language="O'zbekcha",
        telegram_file_id="FILE123",
        storage_channel_message_id=1001
    )
    db_session.add(tr1)
    await db_session.commit()

    repo = SeriesRepository(db_session)
    service = SeriesService(repository=repo, telegram_api=AsyncMock())
    
    # Qism 1 ni tekshiramiz
    ep_detail = await service.get_episode_detail_by_code("EP1CODE1", publish_status="published")
    assert ep_detail is not None
    assert ep_detail.code == "EP1CODE1"
    assert ep_detail.episode_number == 1
    assert ep_detail.season_number == 1
    assert ep_detail.series_id == series.id
    assert ep_detail.series_title == "Test Serial"
    assert ep_detail.prev_episode_code is None
    assert ep_detail.next_episode_code == "EP2CODE2"
    assert len(ep_detail.translations) == 1
    assert ep_detail.translations[0].telegram_file_id == "FILE123"

    # Qism 2 ni tekshiramiz
    ep2_detail = await service.get_episode_detail_by_code("EP2CODE2", publish_status="published")
    assert ep2_detail is not None
    assert ep2_detail.code == "EP2CODE2"
    assert ep2_detail.prev_episode_code == "EP1CODE1"
    assert ep2_detail.next_episode_code is None
