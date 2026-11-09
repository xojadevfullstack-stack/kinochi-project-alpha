import pytest
from unittest.mock import AsyncMock
from app.application.series.series_service import SeriesService
from app.infrastructure.db.repositories.series_repository import SeriesRepository
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel
from app.infrastructure.db.models.translation import EpisodeTranslationModel

@pytest.mark.asyncio
async def test_k4_single_season_prev_next_and_gaps(db_session):
    """
    K4 tekshiruvi: 1-faslli serial, 1-qism, oxirgi qism va bo'shliqli raqamlar (1, 2, 5, 8).
    """
    series = SeriesModel(id=8001, title="1-Faslli Serial", publish_status="published")
    db_session.add(series)
    await db_session.flush()

    season1 = SeasonModel(id=9001, series_id=series.id, season_number=1, title="1-Mavsum")
    db_session.add(season1)
    await db_session.flush()

    # Qismlar: 1, 2, 5, 8 (bo'shliqli)
    ep1 = EpisodeModel(id=7001, season_id=season1.id, episode_number=1, code="C_S1_E1", display_code="S1-CH1", title="1-qism")
    ep2 = EpisodeModel(id=7002, season_id=season1.id, episode_number=2, code="C_S1_E2", display_code="S1-CH2", title="2-qism")
    ep5 = EpisodeModel(id=7005, season_id=season1.id, episode_number=5, code="C_S1_E5", display_code="S1-CH5", title="5-qism")
    ep8 = EpisodeModel(id=7008, season_id=season1.id, episode_number=8, code="C_S1_E8", display_code="S1-CH8", title="8-qism")
    db_session.add_all([ep1, ep2, ep5, ep8])
    await db_session.flush()

    # Tarjimalar
    for ep in [ep1, ep2, ep5, ep8]:
        db_session.add(EpisodeTranslationModel(episode_id=ep.id, language="O'zbekcha", telegram_file_id="FILE_OK", storage_channel_message_id=ep.id))
    await db_session.commit()

    repo = SeriesRepository(db_session)
    service = SeriesService(repository=repo, telegram_api=AsyncMock())

    # 1. Ep 1 (Birinchi qism): prev bo'lmasligi, next esa Ep 2 bo'lishi kerak
    det1 = await service.get_episode_detail_by_code("C_S1_E1", publish_status="published")
    assert det1 is not None
    assert det1.prev_episode_code is None, "1-qismning prev_episode_code None bo'lishi shart"
    assert det1.next_episode_code == "C_S1_E2", f"1-qismdan keyin 2-qism kelishi kerak, lekin: {det1.next_episode_code}"

    # 2. Ep 2 (Bo'shliqdan oldingi qism): next 3 yoki 4 emas, aynan mavjud Ep 5 bo'lishi kerak!
    det2 = await service.get_episode_detail_by_code("C_S1_E2", publish_status="published")
    assert det2 is not None
    assert det2.prev_episode_code == "C_S1_E1"
    assert det2.next_episode_code == "C_S1_E5", f"2-qismdan keyin 5-qism kelishi kerak (bo'shliq sakrashi), lekin: {det2.next_episode_code}"

    # 3. Ep 5 (Bo'shliqdan keyingi qism): prev Ep 2, next Ep 8 bo'lishi kerak
    det5 = await service.get_episode_detail_by_code("C_S1_E5", publish_status="published")
    assert det5 is not None
    assert det5.prev_episode_code == "C_S1_E2", f"5-qismning prev qismi 2-qism bo'lishi kerak, lekin: {det5.prev_episode_code}"
    assert det5.next_episode_code == "C_S1_E8", f"5-qismdan keyin 8-qism kelishi kerak, lekin: {det5.next_episode_code}"

    # 4. Ep 8 (Oxirgi qism): next None bo'lishi shart!
    det8 = await service.get_episode_detail_by_code("C_S1_E8", publish_status="published")
    assert det8 is not None
    assert det8.prev_episode_code == "C_S1_E5"
    assert det8.next_episode_code is None, "Oxirgi qismning next_episode_code None bo'lishi shart"


@pytest.mark.asyncio
async def test_k4_multi_season_cross_season_transition(db_session):
    """
    K4 tekshiruvi: Ko'p faslli serial va mavsumlararo o'tish (Season 1 oxirgi qismi -> Season 2 birinchi qismi).
    """
    series = SeriesModel(id=8002, title="Ko'p Faslli Serial", publish_status="published")
    db_session.add(series)
    await db_session.flush()

    # 1-mavsum (2 ta qism)
    season1 = SeasonModel(id=9011, series_id=series.id, season_number=1, title="1-Mavsum")
    # 2-mavsum (2 ta qism)
    season2 = SeasonModel(id=9012, series_id=series.id, season_number=2, title="2-Mavsum")
    db_session.add_all([season1, season2])
    await db_session.flush()

    s1_ep1 = EpisodeModel(id=7101, season_id=season1.id, episode_number=1, code="S1_EP1", display_code="S1-CH1", title="1-qism")
    s1_ep2 = EpisodeModel(id=7102, season_id=season1.id, episode_number=2, code="S1_EP2", display_code="S1-CH2", title="2-qism")

    s2_ep1 = EpisodeModel(id=7201, season_id=season2.id, episode_number=1, code="S2_EP1", display_code="S2-CH1", title="1-qism")
    s2_ep2 = EpisodeModel(id=7202, season_id=season2.id, episode_number=2, code="S2_EP2", display_code="S2-CH2", title="2-qism")
    db_session.add_all([s1_ep1, s1_ep2, s2_ep1, s2_ep2])
    await db_session.flush()

    for ep in [s1_ep1, s1_ep2, s2_ep1, s2_ep2]:
        db_session.add(EpisodeTranslationModel(episode_id=ep.id, language="O'zbekcha", telegram_file_id="FILE_OK", storage_channel_message_id=ep.id))
    await db_session.commit()

    repo = SeriesRepository(db_session)
    service = SeriesService(repository=repo, telegram_api=AsyncMock())

    # Mavsumlararo o'tish 1: Season 1 Ep 2 (1-mavsum oxirgi qismi)
    # Buning next_episode_code aynan 2-mavsumning 1-qismi (S2_EP1) bo'lishi SHART!
    det_s1_ep2 = await service.get_episode_detail_by_code("S1_EP2", publish_status="published")
    assert det_s1_ep2 is not None
    assert det_s1_ep2.prev_episode_code == "S1_EP1"
    assert det_s1_ep2.next_episode_code == "S2_EP1", (
        f"Mavsumlararo o'tish xatosi: 1-mavsum oxirgi qismidan keyin 2-mavsum 1-qismi kelishi kerak! Olingan: {det_s1_ep2.next_episode_code}"
    )

    # Mavsumlararo o'tish 2: Season 2 Ep 1 (2-mavsum 1-qismi)
    # Buning prev_episode_code aynan 1-mavsumning oxirgi qismi (S1_EP2) bo'lishi SHART!
    det_s2_ep1 = await service.get_episode_detail_by_code("S2_EP1", publish_status="published")
    assert det_s2_ep1 is not None
    assert det_s2_ep1.prev_episode_code == "S1_EP2", (
        f"Mavsumlararo o'tish xatosi: 2-mavsum 1-qismidan oldin 1-mavsum oxirgi qismi bo'lishi kerak! Olingan: {det_s2_ep1.prev_episode_code}"
    )
    assert det_s2_ep1.next_episode_code == "S2_EP2"

    # Season 2 Ep 2 (butun serialning oxirgi qismi): next None
    det_s2_ep2 = await service.get_episode_detail_by_code("S2_EP2", publish_status="published")
    assert det_s2_ep2 is not None
    assert det_s2_ep2.next_episode_code is None
