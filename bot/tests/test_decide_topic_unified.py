"""Item 22: decide_topic jonli va dry-run uchun yagona qaror manbai ekanini tekshiradi."""
import itertools
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Chat, Message, Video

BOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BOT_DIR not in sys.path:
    sys.path.insert(0, BOT_DIR)

from config import settings
from handlers import auto_index
from handlers.auto_index import decide_topic, evaluate_dry_run_decision, flush_source_batch, source_batches, SourceBatch

CHAT = -100123456
TOPIC = 77
STATUSES = [200, 404, 409, 500]


def expected_decision(s: int, m: int) -> str:
    if s == 409 or m == 409:
        return "REJECTED_AMBIGUOUS"
    if s == 200 and m == 200:
        return "REJECTED_AMBIGUOUS"
    if s == 404 and m == 404:
        return "SKIPPED_NOT_FOUND"
    if s == 200 and m == 404:
        return "INDEX_SERIES"
    if m == 200 and s == 404:
        return "INDEX_MOVIE"
    return "SKIPPED_ERROR"


def make_get(s: int, m: int):
    def _resp(code, body):
        r = MagicMock()
        r.status_code = code
        r.json.return_value = body
        return r

    async def _get(url):
        if "/series/by-source" in url:
            return _resp(s, {"id": 1, "title": "S", "seasons": []})
        return _resp(m, {"id": 2, "title": "M", "code": "ABC", "translations": []})
    return _get


def make_msg():
    msg = MagicMock(spec=Message)
    msg.message_id = 101
    msg.message_thread_id = TOPIC
    msg.caption = "1-qism"
    chat = MagicMock(spec=Chat)
    chat.id = CHAT
    msg.chat = chat
    video = MagicMock(spec=Video)
    video.file_id = "file"
    video.file_name = "a.mp4"
    video.duration = 5400
    msg.video = video
    msg.document = None
    msg.reply = AsyncMock()
    return msg


@pytest.mark.asyncio
@pytest.mark.parametrize("s,m", list(itertools.product(STATUSES, STATUSES)))
async def test_decide_topic_table(s, m):
    with patch("handlers.auto_index.api_client.client.get", side_effect=make_get(s, m)):
        decision, entity, _ = await decide_topic(CHAT, TOPIC)
    assert decision == expected_decision(s, m)
    assert (entity is not None) == decision.startswith("INDEX_")


@pytest.mark.asyncio
@pytest.mark.parametrize("s,m", list(itertools.product(STATUSES, STATUSES)))
async def test_live_and_dry_run_agree_and_live_writes_only_on_index(s, m):
    expected = expected_decision(s, m)
    msg = make_msg()
    bot = MagicMock()
    process_series = AsyncMock()
    process_movie = AsyncMock()

    with patch.object(settings, "AUTO_CONTENT_ENABLED", True), \
         patch.object(settings, "AUTO_INDEX_DRY_RUN", False), \
         patch.object(settings, "AUTO_INDEX_ALLOWED_CHAT_IDS", [CHAT]), \
         patch("handlers.auto_index.api_client.client.get", side_effect=make_get(s, m)), \
         patch("handlers.auto_index.process_series_batch", process_series), \
         patch("handlers.auto_index.process_movie_message", process_movie):
        # Dry-run qarori
        dry_decision, _ = await evaluate_dry_run_decision(msg, bot)
        # Jonli yo'l
        key = f"{CHAT}:{TOPIC}"
        source_batches.clear()
        source_batches[key] = SourceBatch(messages=[msg]) if "messages" in SourceBatch.__dataclass_fields__ else None
        await flush_source_batch(key, bot, 0)

    if expected in ("INDEX_SERIES", "INDEX_MOVIE"):
        # Dry-run indekslanadigan holatda gate natijasi (WOULD_INDEX yoki REJECTED_GATE/SKIPPED_ALREADY_ATTACHED)
        assert dry_decision not in ("REJECTED_AMBIGUOUS", "SKIPPED_NOT_FOUND", "SKIPPED_ERROR")
    else:
        assert dry_decision == expected

    wrote_series = process_series.await_count
    wrote_movie = process_movie.await_count
    if expected == "INDEX_SERIES":
        assert (wrote_series, wrote_movie) == (1, 0)
    elif expected == "INDEX_MOVIE":
        assert (wrote_series, wrote_movie) == (0, 1)
    else:
        assert (wrote_series, wrote_movie) == (0, 0)
