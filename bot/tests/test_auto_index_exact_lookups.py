"""Tests for bot auto_index exact lookup handling and 409 rejection."""
import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

BOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BOT_DIR not in sys.path:
    sys.path.insert(0, BOT_DIR)

from config import settings
from handlers.auto_index import flush_source_batch, SourceBatch, source_batches


@pytest.fixture(autouse=True)
def setup_settings():
    settings.AUTO_CONTENT_ENABLED = True
    settings.AUTO_INDEX_DRY_RUN = False
    settings.AUTO_INDEX_ALLOWED_CHAT_IDS = [-1001234567890]
    settings.STORAGE_CHANNEL_ID = -1009999999999
    yield


@pytest.mark.asyncio
async def test_flush_source_batch_rejects_ambiguous_series():
    """Serial by-source 409 (ambiguous) qaytarganda bot REJECTED_AMBIGUOUS qaror qabul qilishi va hech narsa yozmasligi kerak."""
    mock_bot = AsyncMock()
    mock_msg = AsyncMock()
    mock_msg.message_id = 101
    mock_msg.chat.id = -1001234567890
    mock_msg.message_thread_id = 42

    key = "-1001234567890:42"
    source_batches[key] = SourceBatch(messages=[mock_msg], first_arrival=1.0)

    # 409 response for /series/by-source
    mock_resp = MagicMock()
    mock_resp.status_code = 409

    with patch("handlers.auto_index.api_client.client.get", return_value=mock_resp) as mock_get:
        await flush_source_batch(key, mock_bot, delay=0)

        mock_get.assert_called_once()
        assert not mock_bot.copy_message.called


@pytest.mark.asyncio
async def test_flush_source_batch_rejects_ambiguous_movie():
    """Movie by-source 409 (ambiguous) qaytarganda bot REJECTED_AMBIGUOUS qaror qabul qilishi va hech narsa yozmasligi kerak."""
    mock_bot = AsyncMock()
    mock_msg = AsyncMock()
    mock_msg.message_id = 102
    mock_msg.chat.id = -1001234567890
    mock_msg.message_thread_id = 42

    key = "-1001234567890:42"
    source_batches[key] = SourceBatch(messages=[mock_msg], first_arrival=1.0)

    # 404 for series, 409 for movie
    resp_series = MagicMock()
    resp_series.status_code = 404

    resp_movie = MagicMock()
    resp_movie.status_code = 409

    with patch("handlers.auto_index.api_client.client.get", side_effect=[resp_series, resp_movie]) as mock_get:
        await flush_source_batch(key, mock_bot, delay=0)

        assert mock_get.call_count == 2
        assert not mock_bot.copy_message.called
