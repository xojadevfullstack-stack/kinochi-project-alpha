import pytest
from unittest.mock import MagicMock, patch
from aiogram.types import Message, Chat, Video
import sys
import os
import logging

BOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BOT_DIR not in sys.path:
    sys.path.insert(0, BOT_DIR)

from config import settings
from handlers.auto_index import enqueue_video_message, source_batches


def make_mock_message(chat_id=-100123456, topic_id=77, message_id=101):
    msg = MagicMock(spec=Message)
    msg.message_id = message_id
    msg.message_thread_id = topic_id
    msg.caption = "Test Video"

    chat = MagicMock(spec=Chat)
    chat.id = chat_id
    msg.chat = chat

    video = MagicMock(spec=Video)
    video.file_id = "BAADBAAD_allowlist_test"
    video.file_name = "test.mp4"
    msg.video = video
    msg.document = None
    return msg


@pytest.mark.asyncio
async def test_allowlist_empty_ignores_all_chats(caplog):
    """AUTO_INDEX_ALLOWED_CHAT_IDS bo'sh bo'lganda (standart) barcha chatlar e'tiborsiz qoldiriladi."""
    source_batches.clear()
    msg = make_mock_message(chat_id=-100123456, topic_id=77)
    bot = MagicMock()

    with patch.object(settings, "AUTO_CONTENT_ENABLED", True), \
         patch.object(settings, "AUTO_INDEX_DRY_RUN", False), \
         patch.object(settings, "AUTO_INDEX_ALLOWED_CHAT_IDS", []), \
         caplog.at_level(logging.INFO):
        await enqueue_video_message(msg, bot)
        assert len(source_batches) == 0
        assert "[AUTO_INDEX DECISION]" in caplog.text
        assert "decision=IGNORED" in caplog.text
        assert "AUTO_INDEX_ALLOWED_CHAT_IDS allowlist" in caplog.text


@pytest.mark.asyncio
async def test_unlisted_chat_ignored(caplog):
    """Ro'yxatda yo'q chat kelganda IGNORED log qilinadi va buferga olinmaydi."""
    source_batches.clear()
    msg = make_mock_message(chat_id=-100999999, topic_id=77)
    bot = MagicMock()

    with patch.object(settings, "AUTO_CONTENT_ENABLED", True), \
         patch.object(settings, "AUTO_INDEX_DRY_RUN", False), \
         patch.object(settings, "AUTO_INDEX_ALLOWED_CHAT_IDS", [-100123456]), \
         caplog.at_level(logging.INFO):
        await enqueue_video_message(msg, bot)
        assert len(source_batches) == 0
        assert "decision=IGNORED" in caplog.text


@pytest.mark.asyncio
async def test_missing_topic_id_ignored(caplog):
    """Chat allowlistda bo'lsa ham topic_id (message_thread_id) bo'lmasa, xabar IGNORED qilinadi."""
    source_batches.clear()
    msg = make_mock_message(chat_id=-100123456, topic_id=None)
    bot = MagicMock()

    with patch.object(settings, "AUTO_CONTENT_ENABLED", True), \
         patch.object(settings, "AUTO_INDEX_DRY_RUN", False), \
         patch.object(settings, "AUTO_INDEX_ALLOWED_CHAT_IDS", [-100123456]), \
         caplog.at_level(logging.INFO):
        await enqueue_video_message(msg, bot)
        assert len(source_batches) == 0
        assert "decision=IGNORED" in caplog.text
        assert "message has no topic_id" in caplog.text


@pytest.mark.asyncio
async def test_allowed_chat_and_valid_topic_buffered(caplog):
    """Chat allowlistda bo'lib topic_id mavjud bo'lsa, xabar BUFFERED log qilinadi va buferga olinadi."""
    source_batches.clear()
    msg = make_mock_message(chat_id=-100123456, topic_id=77)
    bot = MagicMock()

    with patch.object(settings, "AUTO_CONTENT_ENABLED", True), \
         patch.object(settings, "AUTO_INDEX_DRY_RUN", False), \
         patch.object(settings, "AUTO_INDEX_ALLOWED_CHAT_IDS", [-100123456]), \
         caplog.at_level(logging.INFO):
        await enqueue_video_message(msg, bot)
        assert len(source_batches) == 1
        assert "-100123456:77" in source_batches
        assert "decision=BUFFERED" in caplog.text
