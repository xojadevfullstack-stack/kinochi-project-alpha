"""Tests for bot auto_index no overwrites and duplicate skipping."""
import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

BOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BOT_DIR not in sys.path:
    sys.path.insert(0, BOT_DIR)

from config import settings
from handlers.auto_index import process_movie_message, process_series_batch


@pytest.fixture(autouse=True)
def setup_settings():
    settings.AUTO_CONTENT_ENABLED = True
    settings.AUTO_INDEX_DRY_RUN = False
    settings.AUTO_INDEX_ALLOWED_CHAT_IDS = [-1001234567890]
    settings.STORAGE_CHANNEL_ID = -1009999999999
    yield


@pytest.mark.asyncio
async def test_process_movie_message_skips_when_already_has_video():
    """Filmda O'zbekcha video tarjimasi allaqachon mavjud bo'lsa, qayta yuklanmasligi va ustiga yozilmasligi kerak."""
    mock_bot = AsyncMock()
    mock_msg = AsyncMock()
    mock_msg.message_id = 101
    mock_msg.chat.id = -1001234567890
    mock_msg.message_thread_id = 55
    mock_msg.video = MagicMock(file_id="new_file_id", file_name="video.mp4")
    mock_msg.document = None

    movie = {
        "id": 1,
        "title": "Mavjud Film",
        "code": "1001",
        "release_year": 2024,
        "translations": [
            {
                "id": 10,
                "language": "O'zbekcha",
                "telegram_file_id": "existing_file_id",
                "storage_channel_message_id": 999
            }
        ]
    }

    with patch("handlers.auto_index.safe_copy_message_with_retry") as mock_copy:
        await process_movie_message(mock_msg, mock_bot, movie)
        # copy_message yoki backend link-video chaqirilmagan bo'lishi kerak
        assert not mock_copy.called


@pytest.mark.asyncio
async def test_process_series_batch_skips_duplicate_reservation():
    """Qayta forward qilingan dublikat qism (is_duplicate=True) aniqlansa, saqlash kanaliga ko'chirilmasligi kerak."""
    mock_bot = AsyncMock()
    mock_msg = AsyncMock()
    mock_msg.message_id = 201
    mock_msg.chat.id = -1001234567890
    mock_msg.message_thread_id = 88
    mock_msg.caption = "1-qism"
    mock_msg.video = MagicMock(file_id="dup_file_id", file_name="ep1.mp4")
    mock_msg.document = None

    series = {
        "id": 5,
        "title": "Serial Test",
        "seasons": [
            {
                "id": 10,
                "season_number": 1,
                "status": "ongoing",
                "episodes": []
            }
        ]
    }

    # reserve_episodes javobida is_duplicate=True qaytadi
    mock_reserved = [
        {
            "id": 101,
            "episode_number": 1,
            "code": "ep_101",
            "display_code": "S1-CH1",
            "source_message_id": 201,
            "season_number": 1,
            "is_update": False,
            "is_duplicate": True
        }
    ]

    with patch("handlers.auto_index.api_client.reserve_episodes", return_value=mock_reserved), \
         patch("handlers.auto_index.safe_copy_message_with_retry") as mock_copy:
        await process_series_batch([mock_msg], mock_bot, series)
        # Dublikat bo'lgani uchun copy_message chaqirilmagan bo'lishi shart
        assert not mock_copy.called
