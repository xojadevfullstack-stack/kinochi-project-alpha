import sys
import os
import asyncio
import time
from unittest.mock import AsyncMock, patch, MagicMock
import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scraper.telethon_moderator_pipeline import (
    get_flood_wait_seconds,
    is_bot_flood_text,
    handle_bot_flood_wait,
    BotFloodWaitError,
    MAX_BOT_FLOOD_WAIT,
)
from scraper.state_manager import StateManager


def test_get_flood_wait_seconds_extraction():
    """get_flood_wait_seconds turli daqiqa va soniya matnlaridan to'g'ri soniyalarni ajratadi."""
    assert is_bot_flood_text("Biroz sekinroq. 41 daqiqadan so'ng urinib ko'ring") is True
    assert is_bot_flood_text("Juda ko'p so'rov. 59 daqiqa kuting") is True
    assert is_bot_flood_text("Biroz sekinroq. 30 soniya kuting") is True

    # 41 daqiqa -> 41 * 60 + 5 = 2465
    sec_41 = get_flood_wait_seconds("Biroz sekinroq. 41 daqiqadan so'ng urinib ko'ring")
    assert sec_41 == 2465

    # 59 daqiqa -> 59 * 60 + 5 = 3545
    sec_59 = get_flood_wait_seconds("Juda ko'p so'rov. 59 daqiqa kuting")
    assert sec_59 == 3545

    # 30 soniya -> 30 + 5 = 35
    sec_30 = get_flood_wait_seconds("Biroz sekinroq. 30 soniya kuting")
    assert sec_30 == 35


@pytest.mark.asyncio
async def test_handle_bot_flood_wait_short_waits():
    """120 soniyadan kam yoki teng bo'lgan qisqa flood waitlar kutiladi va True qaytaradi."""
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep, \
         patch.object(StateManager, "set_bot_status") as mock_set_status:

        res = await handle_bot_flood_wait(bot="asilmediabot", seconds=30, context="test")
        assert res is True
        mock_sleep.assert_called_once_with(30)
        mock_set_status.assert_any_call("flood_wait")
        mock_set_status.assert_any_call("online")


@pytest.mark.asyncio
async def test_handle_bot_flood_wait_long_aborts_without_sleep():
    """120 soniyadan ortiq bo'lgan (masalan 2465s = 41 daqiqa) flood waitlar QOTIB QOLMAYDI, sleep qilinmaydi va BotFloodWaitError chaqiradi."""
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep, \
         patch.object(StateManager, "set_bot_status") as mock_set_status, \
         patch.object(StateManager, "update") as mock_update:

        with pytest.raises(BotFloodWaitError) as exc_info:
            await handle_bot_flood_wait(bot="asilmediabot", seconds=2465, context="test long wait")

        # Uxlash mutlaqo chaqirilmasligi shart!
        mock_sleep.assert_not_called()
        assert exc_info.value.seconds == 2465
        assert exc_info.value.bot == "asilmediabot"

        # StateManager da bot statusi 'flood_wait' bo'lishi va bot_flood_until saqlanishi shart
        mock_set_status.assert_called_with("flood_wait")
        mock_update.assert_called()
        update_args = mock_update.call_args[1]
        assert "bot_flood_until" in update_args
        assert update_args["bot_flood_bot"] == "asilmediabot"


@pytest.mark.asyncio
async def test_run_item_catches_bot_flood_wait_and_fails_fast():
    """run_item BotFloodWaitError yuz berganda 20 daqiqa kutmasdan darhol to'xtaydi va item holatini 'failed' qiladi."""
    from scraper.telethon_moderator_pipeline import TelethonModeratorPipeline
    from scraper.queue_manager import QueueItem, QueueManager

    mock_client = MagicMock()
    mock_checker = MagicMock()
    pipeline = TelethonModeratorPipeline(client=mock_client, duplicate_checker=mock_checker)

    item = QueueItem(id="asilmedia_17049", source="asilmedia", title="Iblislar qotili", media_type="anime")

    with patch.object(pipeline, "_run_item_inner", side_effect=BotFloodWaitError(bot="asilmediabot", seconds=2465)), \
         patch.object(QueueManager, "update_status") as mock_update_status:

        res = await pipeline.run_item(item, target_bot="asilmediabot")
        assert res is False
        mock_update_status.assert_called_once()
        status_call = mock_update_status.call_args
        assert status_call[0][0] == "asilmedia_17049"
        assert status_call[0][1] == "failed"
        assert "Bot flood limiti" in status_call[1]["error_message"]

