import sys
import os
import asyncio
import time
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from telethon.errors import FloodWaitError

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scraper.run_scraper import handle_flood_wait
from scraper.queue_manager import QueueManager, QueueItem


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


def test_recover_stale_in_progress(tmp_path):
    """
    30 daqiqadan (1800 soniya) eski 'in_progress' elementlar 'pending' holatiga qaytishi,
    yangi (10 soniya oldin yangilangan) 'in_progress' lar esa o'zgarmasligi tekshiriladi.
    """
    queue_file = str(tmp_path / "test_queue.json")
    qm = QueueManager(filepath=queue_file)

    now = time.time()
    stale_item = QueueItem(
        id="uzmovi_1",
        source="uzmovi",
        title="Eski film",
        status="in_progress",
        updated_at=now - 2000,  # 33 daqiqa oldin
    )
    fresh_item = QueueItem(
        id="uzmovi_2",
        source="uzmovi",
        title="Yangi film",
        status="in_progress",
        updated_at=now - 100,   # 1.6 daqiqa oldin
    )
    completed_item = QueueItem(
        id="uzmovi_3",
        source="uzmovi",
        title="Tugagan film",
        status="completed",
        updated_at=now - 5000,
    )

    qm.add_items_batch([stale_item, fresh_item, completed_item])

    recovered = qm.recover_stale_in_progress(max_age_seconds=1800)
    assert recovered == 1

    qm.load()
    assert qm.items["uzmovi_1"].status == "pending"
    assert qm.items["uzmovi_2"].status == "in_progress"
    assert qm.items["uzmovi_3"].status == "completed"
