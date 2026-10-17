import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, Chat, Video
import sys
import os

# Ensure bot directory is in sys.path
BOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BOT_DIR not in sys.path:
    sys.path.insert(0, BOT_DIR)

from config import settings
from handlers.auto_index import (
    enqueue_video_message,
    process_movie_message,
    process_series_batch,
    source_batches
)


def make_mock_message(chat_id=1001, topic_id=5, message_id=42, caption="8-qism"):
    msg = MagicMock(spec=Message)
    msg.message_id = message_id
    msg.message_thread_id = topic_id
    msg.caption = caption

    chat = MagicMock(spec=Chat)
    chat.id = chat_id
    msg.chat = chat

    video = MagicMock(spec=Video)
    video.file_id = "BAADBAAD_test_file_id"
    video.file_name = "test_video.mp4"
    msg.video = video
    msg.document = None

    msg.reply = AsyncMock()
    return msg


@pytest.mark.asyncio
async def test_auto_index_ignored_when_auto_content_disabled():
    """AUTO_CONTENT_ENABLED=False bo'lganda kelgan xabarlar navbatga olinmasligi va yozilmasligi kerak."""
    source_batches.clear()
    msg = make_mock_message()
    bot = MagicMock()

    with patch.object(settings, "AUTO_CONTENT_ENABLED", False):
        await enqueue_video_message(msg, bot)
        assert len(source_batches) == 0


@pytest.mark.asyncio
async def test_movie_process_dry_run_does_not_call_backend():
    """AUTO_INDEX_DRY_RUN=True bo'lganda safe_copy_message va link-video chaqirilmasligi kerak."""
    msg = make_mock_message()
    bot = MagicMock()
    movie = {"id": 10, "title": "Test Movie", "code": "mv_10", "release_year": 2024}

    with patch.object(settings, "AUTO_INDEX_DRY_RUN", True):
        with patch("handlers.auto_index.safe_copy_message_with_retry", AsyncMock()) as mock_copy, \
             patch("handlers.auto_index.api_client.client.post", AsyncMock()) as mock_post:
            await process_movie_message(msg, bot, movie)
            mock_copy.assert_not_called()
            mock_post.assert_not_called()


@pytest.mark.asyncio
async def test_movie_process_write_when_dry_run_false():
    """AUTO_INDEX_DRY_RUN=False bo'lganda copy_message va link-video chaqirilishi kerak."""
    msg = make_mock_message()
    bot = MagicMock()
    movie = {"id": 10, "title": "Test Movie", "code": "mv_10", "release_year": 2024}

    storage_msg = MagicMock()
    storage_msg.message_id = 999

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()

    with patch.object(settings, "STORAGE_CHANNEL_ID", -1009999), \
         patch.object(settings, "AUTO_INDEX_DRY_RUN", False), \
         patch("handlers.auto_index.safe_copy_message_with_retry", AsyncMock(return_value=storage_msg)) as mock_copy, \
         patch("handlers.auto_index.api_client.client.post", AsyncMock(return_value=mock_resp)) as mock_post:
        await process_movie_message(msg, bot, movie)
        mock_copy.assert_called_once()
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_series_process_dry_run_does_not_create_or_reserve():
    """AUTO_INDEX_DRY_RUN=True bo'lganda serial uchun fasl/qism yaratilmasligi kerak."""
    msg = make_mock_message(caption="1-qism")
    bot = MagicMock()
    series = {"id": 20, "title": "Test Series", "seasons": []}

    with patch.object(settings, "STORAGE_CHANNEL_ID", -1009999), \
         patch.object(settings, "AUTO_INDEX_DRY_RUN", True), \
         patch("handlers.auto_index.api_client.client.post", AsyncMock()) as mock_post, \
         patch("handlers.auto_index.api_client.reserve_episodes", AsyncMock()) as mock_reserve:
        await process_series_batch([msg], bot, series)
        mock_post.assert_not_called()
        mock_reserve.assert_not_called()
