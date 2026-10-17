import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, Chat, Video
import sys
import os
import logging

BOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BOT_DIR not in sys.path:
    sys.path.insert(0, BOT_DIR)

from config import settings
from handlers.auto_index import enqueue_video_message, evaluate_dry_run_decision, source_batches


def make_mock_message(chat_id=-100123456, topic_id=77, message_id=101, caption="1-qism", duration=5400):
    msg = MagicMock(spec=Message)
    msg.message_id = message_id
    msg.message_thread_id = topic_id
    msg.caption = caption

    chat = MagicMock(spec=Chat)
    chat.id = chat_id
    msg.chat = chat

    video = MagicMock(spec=Video)
    video.file_id = "BAADBAAD_dry_run_test_file"
    video.file_name = "sample.mp4"
    video.duration = duration
    msg.video = video
    msg.document = None
    msg.reply = AsyncMock()
    return msg


@pytest.mark.asyncio
async def test_dry_run_runs_full_pipeline_when_auto_content_disabled(caplog):
    """AUTO_CONTENT_ENABLED=False bo'lganda ham AUTO_INDEX_DRY_RUN to'liq qarorlar zanjirini bajaradi."""
    source_batches.clear()
    msg = make_mock_message(chat_id=-100123456, topic_id=77, caption="5-qism")
    bot = MagicMock()

    mock_series_resp = MagicMock()
    mock_series_resp.status_code = 200
    mock_series_resp.json.return_value = {
        "id": 10,
        "title": "Test Series",
        "seasons": [{"id": 1, "season_number": 1, "episodes": []}]
    }

    mock_movie_resp = MagicMock()
    mock_movie_resp.status_code = 404

    async def mock_get(url):
        if "/series/by-source" in url:
            return mock_series_resp
        if "/movies/by-source" in url:
            return mock_movie_resp
        return MagicMock(status_code=404)

    with patch.object(settings, "AUTO_CONTENT_ENABLED", False), \
         patch.object(settings, "AUTO_INDEX_DRY_RUN", True), \
         patch.object(settings, "AUTO_INDEX_ALLOWED_CHAT_IDS", [-100123456]), \
         patch("handlers.auto_index.api_client.client.get", side_effect=mock_get), \
         patch("handlers.auto_index.api_client.client.post", AsyncMock()) as mock_post, \
         caplog.at_level(logging.INFO):
        await enqueue_video_message(msg, bot)

        # 0 yozuv (writes)
        mock_post.assert_not_called()
        assert len(source_batches) == 0

        # Log formati: [AUTO_INDEX][DRY_RUN] chat topic decision reason
        assert "[AUTO_INDEX][DRY_RUN] -100123456 77 WOULD_INDEX" in caplog.text


@pytest.mark.asyncio
async def test_dry_run_allowlist_rejection(caplog):
    """Allowlistda bo'lmagan chat dry-run rejimida REJECTED_ALLOWLIST deb qayd qilinadi."""
    msg = make_mock_message(chat_id=-100999999, topic_id=77)
    bot = MagicMock()

    with patch.object(settings, "AUTO_INDEX_DRY_RUN", True), \
         patch.object(settings, "AUTO_INDEX_ALLOWED_CHAT_IDS", [-100123456]), \
         caplog.at_level(logging.INFO):
        decision, reason = await evaluate_dry_run_decision(msg)
        assert decision == "REJECTED_ALLOWLIST"
        assert "[AUTO_INDEX][DRY_RUN] -100999999 77 REJECTED_ALLOWLIST" in caplog.text


@pytest.mark.asyncio
async def test_dry_run_missing_topic_rejection(caplog):
    """Topic_id yo'q bo'lsa dry-run rejimida REJECTED_NO_TOPIC deb qayd qilinadi."""
    msg = make_mock_message(chat_id=-100123456, topic_id=None)
    bot = MagicMock()

    with patch.object(settings, "AUTO_INDEX_DRY_RUN", True), \
         patch.object(settings, "AUTO_INDEX_ALLOWED_CHAT_IDS", [-100123456]), \
         caplog.at_level(logging.INFO):
        decision, reason = await evaluate_dry_run_decision(msg)
        assert decision == "REJECTED_NO_TOPIC"
        assert "[AUTO_INDEX][DRY_RUN] -100123456 None REJECTED_NO_TOPIC" in caplog.text


@pytest.mark.asyncio
async def test_dry_run_ambiguous_topic_both_entities(caplog):
    """Bitta topic ham serial ham kinoga biriktirilgan bo'lsa REJECTED_AMBIGUOUS qayd qilinadi."""
    msg = make_mock_message(chat_id=-100123456, topic_id=77)

    mock_series_resp = MagicMock(status_code=200)
    mock_movie_resp = MagicMock(status_code=200)

    async def mock_get(url):
        if "/series/by-source" in url:
            return mock_series_resp
        return mock_movie_resp

    with patch.object(settings, "AUTO_INDEX_DRY_RUN", True), \
         patch.object(settings, "AUTO_INDEX_ALLOWED_CHAT_IDS", [-100123456]), \
         patch("handlers.auto_index.api_client.client.get", side_effect=mock_get), \
         caplog.at_level(logging.INFO):
        decision, reason = await evaluate_dry_run_decision(msg)
        assert decision == "REJECTED_AMBIGUOUS"
        assert "maps to both movie and series" in reason
        assert "[AUTO_INDEX][DRY_RUN] -100123456 77 REJECTED_AMBIGUOUS" in caplog.text


@pytest.mark.asyncio
async def test_dry_run_series_missing_caption_episode(caplog):
    """Serial mavzusi topilganda lekin captionda qism raqami bo'lmasa REJECTED_GATE bo'ladi."""
    msg = make_mock_message(chat_id=-100123456, topic_id=77, caption="Faqat qiziqarli video")

    mock_series_resp = MagicMock(status_code=200)
    mock_series_resp.json.return_value = {"id": 10, "title": "Serial", "seasons": []}
    mock_movie_resp = MagicMock(status_code=404)

    async def mock_get(url):
        if "/series/by-source" in url:
            return mock_series_resp
        return mock_movie_resp

    with patch.object(settings, "AUTO_INDEX_DRY_RUN", True), \
         patch.object(settings, "AUTO_INDEX_ALLOWED_CHAT_IDS", [-100123456]), \
         patch("handlers.auto_index.api_client.client.get", side_effect=mock_get), \
         caplog.at_level(logging.INFO):
        decision, reason = await evaluate_dry_run_decision(msg)
        assert decision == "REJECTED_GATE"
        assert "cannot extract explicit episode number" in reason


@pytest.mark.asyncio
async def test_dry_run_movie_unknown_duration_rejection(caplog):
    """Kino videosi davomiyligi noma'lum (None yoki 0) bo'lsa duration_unknown bilan rad etiladi."""
    msg = make_mock_message(chat_id=-100123456, topic_id=88, caption="Kino nomi", duration=0)

    mock_series_resp = MagicMock(status_code=404)
    mock_movie_resp = MagicMock(status_code=200)
    mock_movie_resp.json.return_value = {
        "id": 99,
        "title": "Super Kino",
        "duration": 120,
        "translations": []
    }

    async def mock_get(url):
        if "/movies/by-source" in url:
            return mock_movie_resp
        return mock_series_resp

    with patch.object(settings, "AUTO_INDEX_DRY_RUN", True), \
         patch.object(settings, "AUTO_INDEX_ALLOWED_CHAT_IDS", [-100123456]), \
         patch("handlers.auto_index.api_client.client.get", side_effect=mock_get), \
         caplog.at_level(logging.INFO):
        decision, reason = await evaluate_dry_run_decision(msg)
        assert decision == "REJECTED_GATE"
        assert "duration_unknown" in reason
        assert "[AUTO_INDEX][DRY_RUN] -100123456 88 REJECTED_GATE" in caplog.text
