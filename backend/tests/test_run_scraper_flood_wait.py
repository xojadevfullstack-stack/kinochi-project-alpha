import sys
import os
import asyncio
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from sqlalchemy import update
from telethon.errors import FloodWaitError

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scraper.run_scraper import handle_flood_wait
from scraper.queue_manager import QueueManager, QueueItem
from app.infrastructure.db.models.ingest_item import IngestItemModel


@pytest.mark.asyncio
async def test_handle_flood_wait_retries_and_sets_status():
    """
    FloodWaitError bo'lganda:
    - 1-3 urinishlarda bot statusi 'flood_wait' ga o'tib, keyin 'online' ga qaytadi
    - sleep qilinadi (fe.seconds + 2)
    - True qaytariladi (qayta urinish uchun)
    """
    fe = FloodWaitError(request=None)
    fe.seconds = 1  # testda 1 soniya

    with patch("scraper.run_scraper.StateManager") as mock_sm_cls, \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        
        mock_sm = MagicMock()
        mock_sm_cls.return_value = mock_sm

        # 1-urinish
        can_retry_1 = await handle_flood_wait(fe, attempt=1, max_attempts=3, item_label="Test Item")
        assert can_retry_1 is True
        mock_sm.set_bot_status.assert_any_call("flood_wait")
        mock_sm.set_bot_status.assert_any_call("online")
        mock_sleep.assert_called_with(3)  # 1 + 2

        # 3-urinish (oxirgi ruxsat etilgan urinish)
        can_retry_3 = await handle_flood_wait(fe, attempt=3, max_attempts=3, item_label="Test Item")
        assert can_retry_3 is True

        # 4-urinish (limitdan oshgan holat)
        can_retry_4 = await handle_flood_wait(fe, attempt=4, max_attempts=3, item_label="Test Item")
        assert can_retry_4 is False


@pytest.mark.asyncio
async def test_recover_stale_in_progress(setup_test_db, engine):
    """
    30 daqiqadan (1800 soniya) eski 'in_progress' elementlar 'queued' holatiga qaytishi,
    yangi (1.6 daqiqa oldin qulflangan) 'in_progress' lar esa o'zgarmasligi tekshiriladi.
    """
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    qm = QueueManager(session_factory=session_factory)
    await qm.clear_all_async()

    now_dt = datetime.now(timezone.utc)
    stale_item = QueueItem(
        id="uzmovi_1",
        source="uzmovi",
        source_id="1",
        title="Eski film",
        status="in_progress",
    )
    fresh_item = QueueItem(
        id="uzmovi_2",
        source="uzmovi",
        source_id="2",
        title="Yangi film",
        status="in_progress",
    )
    published_item = QueueItem(
        id="uzmovi_3",
        source="uzmovi",
        source_id="3",
        title="Tugagan film",
        status="published",
    )

    await qm.add_items_batch_async([stale_item, fresh_item, published_item])

    async with session_factory() as session:
        await session.execute(
            update(IngestItemModel)
            .where(IngestItemModel.source == "uzmovi", IngestItemModel.source_id == "1")
            .values(locked_at=now_dt - timedelta(seconds=2000), locked_by="w1")
        )
        await session.execute(
            update(IngestItemModel)
            .where(IngestItemModel.source == "uzmovi", IngestItemModel.source_id == "2")
            .values(locked_at=now_dt - timedelta(seconds=100), locked_by="w2")
        )
        await session.commit()

    recovered = await qm.recover_stale_in_progress_async(max_age_seconds=1800)
    assert recovered == 1

    it1 = await qm.get_item_async("uzmovi_1")
    it2 = await qm.get_item_async("uzmovi_2")
    it3 = await qm.get_item_async("uzmovi_3")
    assert it1.status in ("queued", "pending")
    assert it2.status == "in_progress"
    assert it3.status in ("published", "completed")
    await qm.clear_all_async()


@pytest.mark.asyncio
async def test_series_episode_flood_wait_raises_immediately():
    """
    Serial qismlarini yuklash jarayonida donor botdan uzoq muddatli flood-wait (BotFloodWaitError)
    yuz berganda, generic except orqali yutib yuborilmasdan, darhol BotFloodWaitError ko'tarilishi
    va keyingi qismlarga o'tilmasligi assert qilinadi.
    """
    from scraper.telethon_moderator_pipeline import TelethonModeratorPipeline, BotFloodWaitError
    from scraper.queue_manager import QueueItem
    from telethon.tl.custom.message import Message

    mock_client = MagicMock()
    mock_client.send_message = AsyncMock(return_value=MagicMock(id=1))

    mock_btn1 = MagicMock()
    mock_btn1.text = "1"
    mock_btn1.data = b"ep_1"
    mock_btn2 = MagicMock()
    mock_btn2.text = "2"
    mock_btn2.data = b"ep_2"

    card_msg = MagicMock(spec=Message)
    card_msg.id = 10
    card_msg.text = "Vinland haqida afsona"
    card_msg.buttons = [[mock_btn1, mock_btn2]]

    mock_client.get_messages = AsyncMock(return_value=card_msg)

    mock_checker = MagicMock()
    dup_res = MagicMock()
    dup_res.match_type = None
    dup_res.is_duplicate = False
    dup_res.is_incomplete = False
    dup_res.matched_id = None
    mock_checker.check = AsyncMock(return_value=dup_res)

    pipeline = TelethonModeratorPipeline(client=mock_client, duplicate_checker=mock_checker)
    pipeline.enricher = MagicMock()
    pipeline.enricher.enrich_item = AsyncMock(return_value={
        "title": "Vinland haqida afsona",
        "release_year": 2019,
        "tmdb_content_type": "tv",
        "tmdb_id": 890,
        "poster_url": "https://image.tmdb.org/t/p/w500/test.jpg"
    })
    pipeline._validate_and_pre_check = AsyncMock(return_value=True)
    pipeline.safe_click = AsyncMock(return_value=(False, 2465))

    item = QueueItem(
        id="asilmedia_100",
        source="asilmedia",
        title="Vinland haqida afsona",
        media_type="series",
        status="manually_verified",
        payload={"bot_code": "100"}
    )

    with patch("scraper.telethon_moderator_pipeline.poll_new_messages", new_callable=AsyncMock) as mock_poll, \
         patch("scraper.telethon_moderator_pipeline.async_session_factory") as mock_asf, \
         patch("asyncio.sleep", new_callable=AsyncMock):
        mock_poll.return_value = [card_msg]
        mock_session = AsyncMock()
        mock_asf.return_value.__aenter__.return_value = mock_session

        with pytest.raises(BotFloodWaitError) as exc_info:
            await pipeline.run_single_series(item=item, target_bot="asilmediabot")

        assert exc_info.value.seconds == 2465
        assert exc_info.value.bot == "asilmediabot"
        # Episode 1 da flood wait bo'lgani uchun safe_click faqat 1 marta chaqirilishi kerak (2-qismga o'tmaslik)
        assert pipeline.safe_click.call_count == 1


