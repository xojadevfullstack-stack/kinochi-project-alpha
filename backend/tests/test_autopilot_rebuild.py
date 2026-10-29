"""
STAGE 8: Comprehensive Offline Verification Suite for Autopilot Rebuild (M1-M6).

Covers all 9 required test groups without connecting to production DB,
Telegram, or donor websites.
"""
from __future__ import annotations

import os
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure project root, backend, and bot are importable
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
BOT_DIR = os.path.join(ROOT_DIR, "bot")
for p in (ROOT_DIR, BACKEND_DIR, BOT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.infrastructure.db.session import Base
from app.infrastructure.db.models.ingest_item import (
    ALLOWED_STATUS_TRANSITIONS,
    INGEST_STATUSES,
    IngestItemModel,
    validate_status_transition,
)
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.translation import MovieTranslationModel, EpisodeTranslationModel
from app.infrastructure.db.models.series import (
    EpisodeModel,
    SeasonModel,
    SeriesModel,
)
from app.application.ingest_service import IngestService
from app.core.admission_gate import (
    final_check,
    is_blacklist_url_match,
    make_source_key,
    pre_check,
)
from scraper.duplicate_checker import DuplicateChecker, extract_part_number
from scraper.queue_manager import QueueItem
from scraper.site_parser import (
    _extract_asilmedia_items_from_html,
    _extract_uzmovi_items_from_html,
)
from scraper.kinochilar_parser import _extract_kinochilar_items_from_html


@pytest_asyncio.fixture
async def db_session():
    """In-memory SQLite async session with core media + ingest_items tables."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with maker() as session:
        yield session
    await engine.dispose()


# ══════════════════════════════════════════════════════════════════════════════
# 1. STATUS TRANSITIONS (Stage 2d)
# ══════════════════════════════════════════════════════════════════════════════

def test_status_transitions_valid_and_invalid():
    # Valid transitions
    validate_status_transition("discovered", "queued")
    validate_status_transition("queued", "in_progress")
    validate_status_transition("in_progress", "published")
    validate_status_transition("in_progress", "needs_review")
    validate_status_transition("in_progress", "failed")
    validate_status_transition("needs_review", "queued")
    validate_status_transition("failed", "queued")

    # Invalid transitions must raise ValueError
    with pytest.raises(ValueError, match="Taqiqlangan status o'tishi"):
        validate_status_transition("published", "queued")

    with pytest.raises(ValueError, match="Taqiqlangan status o'tishi"):
        validate_status_transition("rejected", "published")

    with pytest.raises(ValueError, match="Taqiqlangan status o'tishi"):
        validate_status_transition("blacklisted", "in_progress")

    with pytest.raises(ValueError, match="Noto'g'ri ingest_items statusi"):
        validate_status_transition("queued", "non_existent_status")


# ══════════════════════════════════════════════════════════════════════════════
# 2. INGEST SERVICE: DEDUP (add_batch), claim_next, recover_stale (Stage 2c)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_ingest_service_dedup_claim_and_recover_stale(db_session: AsyncSession):
    svc = IngestService(db_session)
    batch = [
        {
            "source": "uzmovi",
            "source_id": "101",
            "media_type": "movie",
            "title": "Birinchi Film",
            "year": 2024,
            "url": "https://uzmovi.net/101-birinchi-film.html",
            "status": "queued",
            "priority": 5,
        },
        {
            # Duplicate inside same batch
            "source": "uzmovi",
            "source_id": "101",
            "media_type": "movie",
            "title": "Birinchi Film Dublikat",
            "year": 2024,
            "url": "https://uzmovi.net/101-birinchi-film.html",
            "status": "queued",
        },
        {
            "source": "asilmedia",
            "source_id": "202",
            "media_type": "series",
            "title": "Ikkinchi Serial",
            "year": 2023,
            "url": "http://asilmedia.org/202-ikkinchi-serial.html",
            "status": "queued",
            "priority": 10,
        },
    ]

    inserted = await svc.add_batch(batch)
    assert inserted == 2

    # Re-inserting same (source, source_id) should insert 0
    inserted_again = await svc.add_batch(batch[:1])
    assert inserted_again == 0

    # claim_next picks highest priority queued item -> asilmedia:202 (priority=10)
    claimed = await svc.claim_next(worker_id="test-worker")
    assert claimed is not None
    assert claimed.source == "asilmedia"
    assert claimed.source_id == "202"
    assert claimed.status == "in_progress"
    assert claimed.locked_by == "test-worker"
    assert claimed.attempts == 1

    # Simulate stale lock (> 30 minutes ago)
    claimed.locked_at = datetime.now(timezone.utc) - timedelta(minutes=45)
    await db_session.commit()

    recovered = await svc.recover_stale(max_age_seconds=1800)
    assert recovered == 1

    await db_session.refresh(claimed)
    assert claimed.status == "queued"
    assert claimed.locked_at is None
    assert claimed.locked_by is None


# ══════════════════════════════════════════════════════════════════════════════
# 3. ADMISSION GATE: final_check DURATION MANDATORY & SOURCE_KEY (Stage 5a, 5b)
# ══════════════════════════════════════════════════════════════════════════════

def test_final_check_duration_mandatory_and_source_key():
    assert make_source_key("uzmovi", "71550") == "uzmovi:71550"
    assert make_source_key("uzmovi", "uzmovi_71550") == "uzmovi:71550"

    # Movie without duration key -> must fail with duration_missing
    ok_no_key, defects_no_key = final_check(
        "movie",
        {
            "title": "Test Movie",
            "telegram_file_id": "BAACAgIAAxkBAAIB",
            "storage_channel_message_id": 55,
            "language": "O'zbekcha",
        },
    )
    assert ok_no_key is False
    assert any(d["code"] == "duration_missing" for d in defects_no_key)

    # Movie with duration=0 -> must fail with duration_missing
    ok_zero, defects_zero = final_check(
        "movie",
        {
            "title": "Test Movie",
            "duration": 0,
            "telegram_file_id": "BAACAgIAAxkBAAIB",
            "storage_channel_message_id": 55,
            "language": "O'zbekcha",
        },
    )
    assert ok_zero is False
    assert any(d["code"] == "duration_missing" for d in defects_zero)

    # Episode with duration=None -> must fail with duration_missing
    ok_ep_none, defects_ep_none = final_check(
        "episode",
        {
            "title": "Test Series",
            "duration": None,
            "season_number": 1,
            "episode_number": 1,
            "telegram_file_id": "BAACAgIAAxkBAAIB",
            "storage_channel_message_id": 56,
            "language": "O'zbekcha",
        },
    )
    assert ok_ep_none is False
    assert any(d["code"] == "duration_missing" for d in defects_ep_none)

    # Valid movie with duration > 0 and matching runtime -> passes
    ok_valid, defects_valid = final_check(
        "movie",
        {
            "title": "Test Movie",
            "duration": 7200,
            "runtime": 120,
            "telegram_file_id": "BAACAgIAAxkBAAIB",
            "storage_channel_message_id": 55,
            "language": "O'zbekcha",
        },
        {"runtime": 120, "duration": 7200},
    )
    assert ok_valid is True
    assert defects_valid == []


# ══════════════════════════════════════════════════════════════════════════════
# 4. DUPLICATE CHECKER: extract_part_number & YEAR-LESS FUZZY MATCH (Stage 5e, 5f)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_extract_part_number_and_duplicate_checker():
    # Explicit sequels
    assert extract_part_number("Forsaj 2-qism") == 2
    assert extract_part_number("Avatar Part 3") == 3
    assert extract_part_number("Terminator II") == 2
    assert extract_part_number("Qasoskorlar 2-film") == 2
    assert extract_part_number("Uyda yolg'iz ikkinchi qism") == 2

    # Numbers that are part of the title (NOT sequels)
    assert extract_part_number("13-hudud") is None
    assert extract_part_number("7 hayot") is None
    assert extract_part_number("1917") is None
    assert extract_part_number("300 spartaliklar") is None

    # Year-less token overlap -> needs_review ("possible_duplicate")
    checker = DuplicateChecker()
    checker._last_cache_time = time.time()
    checker.record_added(
        item_id=500,
        title="Qasoskorlar Cheksizlik Jangi",
        original_title="Avengers Infinity War",
        year=2018,
        tmdb_id=299536,
        url="https://uzmovi.net/500-qasoskorlar-cheksizlik-jangi.html",
        media_type="movie",
    )

    # Candidate has NO year, overlaps 3 of 4 words (75%) with existing movie -> possible_duplicate
    res = await checker.check(
        title="Qasoskorlar Cheksizlik Jangi Boshlanishi",
        year=None,
        media_type="movie",
        url="http://asilmedia.org/999-other.html",
    )
    assert res.is_duplicate is False
    assert res.match_type == "possible_duplicate"
    assert res.reason == "possible_duplicate"


# ══════════════════════════════════════════════════════════════════════════════
# 5. BLACKLIST BOUNDARY CHECK (Stage 5c)
# ══════════════════════════════════════════════════════════════════════════════

def test_blacklist_boundary_check():
    # Key "15" must NOT match 71550-test.html
    assert is_blacklist_url_match("https://uzmovi.net/71550-test.html", "uzmovi", "15") is False
    assert is_blacklist_url_match("https://uzmovi.net/150-test.html", "uzmovi", "15") is False
    assert is_blacklist_url_match("https://uzmovi.net/215-test.html", "uzmovi", "15") is False

    # Key "15" MUST match /15-test.html
    assert is_blacklist_url_match("https://uzmovi.net/15-test.html", "uzmovi", "15") is True
    assert is_blacklist_url_match("https://uzmovi.net/tarjima-kinolar/15-forsaj.html", "uzmovi", "uzmovi:15") is True


# ══════════════════════════════════════════════════════════════════════════════
# 6. ROUTING & M3: NO CROSS-SOURCE FALLBACK, EXACT CODE ONLY (Stage 1b, 4e)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_routing_and_m3_no_cross_source_fallback():
    import scraper.run_scraper as rs
    from scraper.telethon_moderator_pipeline import TelethonModeratorPipeline

    # 1b: Unknown target in cmd_download raises ValueError
    with patch.object(rs.DuplicateChecker, "refresh_cache", new=AsyncMock()), \
         patch.object(rs.QueueManager, "recover_stale_in_progress", return_value=0):
        with pytest.raises(ValueError, match="Noma'lum maqsadli manba/bot"):
            await rs.cmd_download(target="unknown_donor_bot", limit=1)

    # M3: Uzmovi without exact code returns no_exact_code and never switches source
    pipeline = object.__new__(TelethonModeratorPipeline)
    pipeline.client = AsyncMock()

    uz_item = QueueItem(
        id="uzmovi_abc",
        source="uzmovi",
        source_id="",
        title="Test Uzmovi Film",
        year=2024,
        media_type="movie",
        url="https://uzmovi.net/invalid-slug.html",
    )

    with patch("scraper.telethon_moderator_pipeline.QueueManager") as mock_qm:
        msg = await pipeline._fetch_video(uz_item, target_bot="UzmovieTV_Bot")
        assert msg is None
        assert uz_item.source == "uzmovi"
        assert uz_item.status == "needs_review"
        assert uz_item.reason == "no_exact_code"
        mock_qm.return_value.update_status.assert_called_with(
            "uzmovi_abc", "needs_review", error_message="no_exact_code"
        )


# ══════════════════════════════════════════════════════════════════════════════
# 7. AUTO_INDEX M4: SCRAPER_ACCOUNT_IDS IGNORE & STARTUP GUARD (Stage 6)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_auto_index_m4_scraper_account_guard():
    import handlers.auto_index as ai

    # Startup guard raises RuntimeError when AUTO_TOPIC_CHAT_ID is in AUTO_INDEX_ALLOWED_CHAT_IDS
    # and SCRAPER_ACCOUNT_IDS is empty
    bad_cfg = SimpleNamespace(
        AUTO_INDEX_ALLOWED_CHAT_IDS=[-1001056603951],
        AUTO_TOPIC_CHAT_ID=-1001056603951,
        SCRAPER_ACCOUNT_IDS=[],
    )
    with pytest.raises(RuntimeError, match="SCRAPER_ACCOUNT_IDS is empty"):
        ai.verify_auto_index_scraper_guard(bad_cfg)

    # Passes when SCRAPER_ACCOUNT_IDS is populated
    good_cfg = SimpleNamespace(
        AUTO_INDEX_ALLOWED_CHAT_IDS=[-1001056603951],
        AUTO_TOPIC_CHAT_ID=-1001056603951,
        SCRAPER_ACCOUNT_IDS=[777888999],
    )
    ai.verify_auto_index_scraper_guard(good_cfg)

    # Message from scraper account is ignored in evaluate_dry_run_decision
    fake_msg = SimpleNamespace(
        chat=SimpleNamespace(id=-1001056603951),
        message_thread_id=42,
        message_id=1001,
        from_user=SimpleNamespace(id=777888999),
        sender_chat=None,
    )
    with patch.object(ai, "settings", good_cfg):
        decision, reason = await ai.evaluate_dry_run_decision(fake_msg, bot=None)
        assert decision == "IGNORED"
        assert reason == "scraper_account"


# ══════════════════════════════════════════════════════════════════════════════
# 8. PIPELINE ORDER M1 & M2: DB WRITE ONLY AFTER STORAGE + FINAL_CHECK (Stage 4)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_pipeline_m1_m2_no_db_write_on_failed_upload_or_missing_s1e1(db_session: AsyncSession):
    from scraper.telethon_moderator_pipeline import TelethonModeratorPipeline

    @asynccontextmanager
    async def fake_session_factory():
        yield db_session

    pipeline = object.__new__(TelethonModeratorPipeline)
    pipeline.client = AsyncMock()
    pipeline.dup_checker = DuplicateChecker()
    pipeline.dup_checker._last_cache_time = time.time()
    pipeline._validate_and_pre_check = AsyncMock(return_value=True)
    pipeline._last_chosen_quality = "720p"

    # Case A (M1): Movie video duration=0 -> final_check fails -> 0 rows in movies table
    movie_item = QueueItem(
        id="uzmovi_555",
        source="uzmovi",
        source_id="555",
        title="Soxta Davomiylik Kino",
        year=2024,
        media_type="movie",
        url="https://uzmovi.net/555-soxta-kino.html",
        status="manually_verified",
    )
    fake_video_msg = SimpleNamespace(
        id=9001,
        text="Soxta Davomiylik Kino",
        message="Soxta Davomiylik Kino",
        media=None,
        file=SimpleNamespace(duration=0, size=50 * 1024 * 1024, name="movie.mp4"),
        document=None,
        video=None,
    )
    fake_storage_msg = SimpleNamespace(
        id=777,
        file_id="BAACAgIAAxkBAAIB",
        media=None,
        file=SimpleNamespace(duration=0, size=50 * 1024 * 1024, name="movie.mp4"),
        document=None,
        video=None,
    )
    pipeline._upload_video_to_chat = AsyncMock(return_value=fake_storage_msg)

    with patch("scraper.telethon_moderator_pipeline.async_session_factory", side_effect=fake_session_factory), \
         patch("scraper.telethon_moderator_pipeline.QueueManager") as mock_qm, \
         patch("scraper.telethon_moderator_pipeline.enrich_movie_smart", new=AsyncMock(return_value={
             "title": "Soxta Davomiylik Kino",
             "original_title": "Fake Duration Movie",
             "release_year": 2024,
             "runtime": 110,
             "tmdb_id": 123456,
             "tmdb_content_type": "movie",
             "description": "To'liq tavsif bu yerda kamida yigirma belgidan ko'p.",
             "genres": "Jangari",
             "poster_url": "https://image.tmdb.org/t/p/w500/test.jpg",
         })):
        ok = await pipeline._process_pipeline(movie_item, fake_video_msg, target_bot="UzmovieTV_Bot")
        assert ok is False
        mock_qm.return_value.update_status.assert_called()
        status_arg = mock_qm.return_value.update_status.call_args[0][1]
        assert status_arg == "rejected"

    movie_count = (await db_session.execute(select(func.count(MovieModel.id)))).scalar()
    assert movie_count == 0

    # Case B (M2): Series without S1:E1 (only button '2-qism' returned by donor) -> rejected, 0 rows in series table
    series_item = QueueItem(
        id="asilmedia_888",
        source="asilmedia",
        source_id="888",
        title="Chala Serial",
        year=2024,
        media_type="series",
        url="http://asilmedia.org/888-chala-serial.html",
        status="manually_verified",
    )
    btn_ep2 = SimpleNamespace(text="2-qism", data=b"ep2")
    card_only_ep2 = SimpleNamespace(
        id=501,
        text="Chala Serial (2024)",
        buttons=[[btn_ep2]],
        file=None,
    )
    pipeline.client.send_message = AsyncMock(return_value=SimpleNamespace(id=500))
    pipeline.client.get_messages = AsyncMock(return_value=card_only_ep2)

    with patch("scraper.telethon_moderator_pipeline.async_session_factory", side_effect=fake_session_factory), \
         patch("scraper.telethon_moderator_pipeline.poll_new_messages", new=AsyncMock(return_value=[card_only_ep2])), \
         patch("scraper.telethon_moderator_pipeline.QueueManager") as mock_qm2, \
         patch("scraper.telethon_moderator_pipeline.enrich_movie_smart", new=AsyncMock(return_value={
             "title": "Chala Serial",
             "original_title": "Incomplete Series",
             "release_year": 2024,
             "tmdb_id": 654321,
             "tmdb_content_type": "tv",
             "description": "To'liq serial tavsifi kamida yigirma belgidan iborat.",
             "genres": "Drama",
             "poster_url": "https://image.tmdb.org/t/p/w500/series.jpg",
         })):
        ok_series = await pipeline.run_single_series(series_item, target_bot="asilmediabot")
        assert ok_series is False
        mock_qm2.return_value.update_status.assert_called_with(
            "asilmedia_888", "rejected", error_message="missing_s1_e1"
        )

    series_count = (await db_session.execute(select(func.count(SeriesModel.id)))).scalar()
    ep_count = (await db_session.execute(select(func.count(EpisodeModel.id)))).scalar()
    assert series_count == 0
    assert ep_count == 0


# ══════════════════════════════════════════════════════════════════════════════
# 9. HTML CARD PARSERS: UZMOVI, ASILMEDIA, KINOCHILAR (Stage 3c)
# ══════════════════════════════════════════════════════════════════════════════

def test_html_card_parsers_extract_exact_source_id():
    uzmovi_html = """
    <div class="shortstory">
        <a href="https://uzmovi.net/tarjima-kinolar/71550-qasoskorlar-4-uzbek-tilida.html" title="Qasoskorlar 4 (2019) O'zbek tilida">
            <img src="/uploads/posts/2019-05/71550.jpg" alt="Qasoskorlar 4" />
        </a>
    </div>
    """
    uz_items = _extract_uzmovi_items_from_html(uzmovi_html)
    assert len(uz_items) == 1
    assert uz_items[0].source == "uzmovi"
    assert uz_items[0].source_id == "71550"
    assert uz_items[0].id == "uzmovi_71550"

    asilmedia_html = """
    <article class="card">
        <div class="title">Gladiator 2 (2024)</div>
        <a href="http://asilmedia.org/48210-gladiator-2-uzbek-tilida-2024.html" title="Gladiator 2 (2024)">
            <img data-src="/uploads/mini/48210.jpg" />
        </a>
    </article>
    """
    as_items = _extract_asilmedia_items_from_html(asilmedia_html)
    assert len(as_items) == 1
    assert as_items[0].source == "asilmedia"
    assert as_items[0].source_id == "48210"
    assert as_items[0].id == "asilmedia_48210"

    kinochilar_html = """
    <div class="movie-card">
        <a href="https://kinochilar.com/tarjima-kinolar/9312-oppengeymer-2023.html" title="Oppengeymer (2023)">
            <img src="https://kinochilar.com/uploads/9312.jpg" alt="Oppengeymer (2023)" />
            Oppengeymer (2023) 1080p FHD
        </a>
    </div>
    """
    kc_items = _extract_kinochilar_items_from_html(kinochilar_html)
    assert len(kc_items) == 1
    assert kc_items[0].source == "kinochilar"
    assert kc_items[0].source_id == "9312"
    assert kc_items[0].id == "kinochilar_9312"
    assert kc_items[0].payload == {"quality_tag": "1080p"}
