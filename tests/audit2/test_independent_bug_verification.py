import os
import sys
import re
import asyncio
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient, ASGITransport
from pathlib import Path

# Setup paths
ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
BOT_DIR = ROOT_DIR / "bot"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

os.environ["APP_ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "super-secret-test-key-for-jwt-32-chars-ok"
os.environ["BOT_TOKEN"] = "123456:TestBotToken"
os.environ["STORAGE_CHANNEL_ID"] = "-100123456789"
os.environ["BOT_API_SECRET"] = "test-bot-secret"

from app.main import app, is_origin_allowed
from app.core.config import settings
from app.infrastructure.security.jwt_handler import create_access_token
from app.infrastructure.db.models.user import UserModel
from app.api.deps import get_db_session


# ─────────────────────────────────────────────────────────────────
# BUG-001: Backend API Banned User Enforcement
# ─────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_audit_bug001_banned_user_blocked_and_active_allowed(tmp_path):
    """Verify banned users receive 403 Forbidden on protected endpoints."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy.pool import StaticPool
    from app.infrastructure.db.session import Base
    
    db_file = tmp_path / "test_audit_user.sqlite3"
    test_engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_file}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as db_session:
        banned_user = UserModel(
            telegram_id=70001,
            first_name="Banned",
            is_banned=True,
        )
        active_user = UserModel(
            telegram_id=70002,
            first_name="Active",
            is_banned=False,
        )
        db_session.add_all([banned_user, active_user])
        await db_session.commit()
        await db_session.refresh(banned_user)
        await db_session.refresh(active_user)

    token_banned = create_access_token(subject=str(banned_user.id), extra={"telegram_id": 70001, "role": "user"})
    token_active = create_access_token(subject=str(active_user.id), extra={"telegram_id": 70002, "role": "user"})

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp_banned = await client.get(
                "/api/v1/users/me/subscriptions",
                headers={"Authorization": f"Bearer {token_banned}"}
            )
            assert resp_banned.status_code == 403, f"Expected 403 for banned user, got {resp_banned.status_code}"
            assert "bloklangan" in resp_banned.json().get("detail", "").lower()

            resp_active = await client.get(
                "/api/v1/users/me/subscriptions",
                headers={"Authorization": f"Bearer {token_active}"}
            )
            assert resp_active.status_code == 200, f"Expected 200 for active user, got {resp_active.status_code}"
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        await test_engine.dispose()


# ─────────────────────────────────────────────────────────────────
# BUG-002: CORS Origin Regex Security
# ─────────────────────────────────────────────────────────────────
def test_audit_bug002_cors_origin_regex_tightening():
    """Verify CORS regex rejects arbitrary subdomains and accepts legitimate Vercel apps."""
    malicious = [
        "https://kinochi-project-alpha-attacker.vercel.app",
        "https://kinochi-admin-phishing.vercel.app",
        "https://kinochi-project-alpha-evil.vercel.app",
        "https://attacker-domain.vercel.app",
        "https://evil.com",
    ]
    for origin in malicious:
        assert not is_origin_allowed(origin), f"Malicious origin {origin} was unexpectedly allowed!"

    legitimate = [
        "https://kinochi-project-alpha.vercel.app",
        "https://kinochi-admin.vercel.app",
        "https://kinochi-project-alpha-iia3u82l1.vercel.app",
        "https://kinochi-project-alpha-git-main.vercel.app",
    ]
    for origin in legitimate:
        assert is_origin_allowed(origin), f"Legitimate origin {origin} was unexpectedly blocked!"


# ─────────────────────────────────────────────────────────────────
# BUG-003: Clean Alembic Migration for Collections & Subscriptions
# ─────────────────────────────────────────────────────────────────
def test_audit_bug003_alembic_migration_collections_table_defined():
    """Verify migration c011ec7100 explicitly defines collections before referencing it."""
    mig_file = ROOT_DIR / "backend" / "alembic" / "versions" / "c011ec7100_add_collection_subscriptions.py"
    assert mig_file.exists(), f"Migration file missing: {mig_file}"
    content = mig_file.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS collections" in content
    assert "CREATE TABLE IF NOT EXISTS collection_subscriptions" in content
    # collections table must be created BEFORE collection_subscriptions
    pos_coll = content.find("CREATE TABLE IF NOT EXISTS collections")
    pos_subs = content.find("CREATE TABLE IF NOT EXISTS collection_subscriptions")
    assert pos_coll < pos_subs, "collections table MUST be created before collection_subscriptions!"


# ─────────────────────────────────────────────────────────────────
# BUG-004: Scraper QueueItem Status Union
# ─────────────────────────────────────────────────────────────────
def test_audit_bug004_queue_item_status_union():
    """Verify admin scraper page and queue_manager support queued and published statuses."""
    admin_scraper_page = ROOT_DIR / "admin-panel" / "app" / "scraper" / "page.tsx"
    assert admin_scraper_page.exists(), f"Admin scraper page missing: {admin_scraper_page}"
    content = admin_scraper_page.read_text(encoding="utf-8")
    assert '"queued"' in content and '"published"' in content, (
        "QueueItem interface in admin-panel/app/scraper/page.tsx must include 'queued' and 'published'!"
    )

    from scraper.queue_manager import _model_to_queue_item
    from unittest.mock import MagicMock
    import datetime

    mock_row_queued = MagicMock()
    mock_row_queued.id = 1
    mock_row_queued.source = "uzmovi"
    mock_row_queued.source_id = "101"
    mock_row_queued.title = "Test Queued Movie"
    mock_row_queued.original_title = None
    mock_row_queued.year = 2024
    mock_row_queued.media_type = "movie"
    mock_row_queued.url = "http://test"
    mock_row_queued.poster_url = None
    mock_row_queued.status = "queued"
    mock_row_queued.payload = {}
    mock_row_queued.updated_at = datetime.datetime.now(datetime.timezone.utc)
    mock_row_queued.priority = 0
    mock_row_queued.tmdb_id = None
    mock_row_queued.reason = None

    item = _model_to_queue_item(mock_row_queued)
    assert item.status == "pending"

    mock_row_pub = MagicMock()
    mock_row_pub.id = 2
    mock_row_pub.source = "uzmovi"
    mock_row_pub.source_id = "102"
    mock_row_pub.title = "Test Pub Movie"
    mock_row_pub.original_title = None
    mock_row_pub.year = 2024
    mock_row_pub.media_type = "movie"
    mock_row_pub.url = "http://test"
    mock_row_pub.poster_url = None
    mock_row_pub.status = "published"
    mock_row_pub.payload = {}
    mock_row_pub.updated_at = datetime.datetime.now(datetime.timezone.utc)
    mock_row_pub.priority = 0
    mock_row_pub.tmdb_id = None
    mock_row_pub.reason = None

    item_pub = _model_to_queue_item(mock_row_pub)
    assert item_pub.status == "completed"



# ─────────────────────────────────────────────────────────────────
# BUG-005: Telegram Bot /cancel Guard in Review FSM
# ─────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_audit_bug005_bot_cancel_fsm_guard():
    """Verify typing /cancel or cancel aborts review submission."""
    from unittest.mock import MagicMock
    from aiogram.fsm.context import FSMContext
    from aiogram.types import Message, Chat, User
    from bot.handlers.reviews import handle_review_comment, ReviewStates

    message = MagicMock(spec=Message)
    message.text = "/cancel"
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 12345
    message.chat = MagicMock(spec=Chat)
    message.chat.id = 12345
    message.reply = AsyncMock()

    state = MagicMock(spec=FSMContext)
    state.get_state = AsyncMock(return_value=ReviewStates.waiting_for_comment.state)
    state.get_data = AsyncMock(return_value={"target_type": "m", "target_id": 100, "movie_id": 100, "rating": 9})
    state.clear = AsyncMock()

    with patch("bot.handlers.reviews.submit_review", new_callable=AsyncMock) as mock_submit:
        await handle_review_comment(message, state)
        mock_submit.assert_not_called()
        state.clear.assert_awaited_once()
        message.reply.assert_awaited_once()
        reply_text = message.reply.call_args[0][0].lower()
        assert "bekor" in reply_text


# ─────────────────────────────────────────────────────────────────
# BUG-006: Bot Single Instance Lock
# ─────────────────────────────────────────────────────────────────
def test_audit_bug006_bot_single_instance_lock(tmp_path):
    """Verify second instance fails to acquire lock when already running."""
    from bot.main import BotInstanceLock, BotAlreadyRunningError
    lock_file = str(tmp_path / ".bot_instance.lock")
    pid_file = str(tmp_path / ".bot_instance.pid")
    lock1 = BotInstanceLock(lock_file=lock_file, pid_file=pid_file)
    lock2 = BotInstanceLock(lock_file=lock_file, pid_file=pid_file)

    try:
        acquired = lock1.acquire()
        assert acquired is True

        with pytest.raises(BotAlreadyRunningError):
            lock2.acquire()
    finally:
        lock1.release()
        lock2.release()


# ─────────────────────────────────────────────────────────────────
# BUG-007: BanCheckMiddleware for Inline Queries and Stale-While-Error
# ─────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_audit_bug007_ban_check_inline_query_and_stale_policy():
    """Verify inline query blocks banned users and stale-while-error holds ban during outage."""
    from unittest.mock import MagicMock
    from aiogram.types import InlineQuery, User
    from bot.middlewares.ban_check import BanCheckMiddleware
    from services.api_client import api_client

    middleware = BanCheckMiddleware()
    event = MagicMock(spec=InlineQuery)
    event.from_user = MagicMock(spec=User)
    event.from_user.id = 8888
    event.answer = AsyncMock()

    handler = AsyncMock()

    with patch.object(api_client, "check_user_banned", new_callable=AsyncMock) as mock_check:
        mock_check.return_value = True
        result = await middleware(handler, event, {})
        assert result is None
        handler.assert_not_called()
        event.answer.assert_awaited_once()
        kwargs = event.answer.call_args[1]
        assert "bloklangan" in kwargs.get("switch_pm_text", "").lower()

    # Test Stale-While-Error policy in api_client
    api_client._ban_cache[8888] = (True, 0.0)  # expired cache of banned user
    with patch.object(api_client, "get_user_summary", new_callable=AsyncMock) as mock_summary:
        mock_summary.return_value = None  # API is down
        is_banned = await api_client.check_user_banned(8888)
        assert is_banned is True, "Stale banned user should remain banned during outage"
    api_client.invalidate_ban_cache(8888)


# ─────────────────────────────────────────────────────────────────
# BUG-008: Ephemeral Thread Loop Engine Disposal
# ─────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_audit_bug008_ephemeral_engine_disposal():
    """Verify null_engine is disposed before thread loop closure."""
    from sqlalchemy.ext.asyncio import AsyncEngine
    from scraper.queue_manager import _run_coro_sync, QueueManager

    real_dispose = AsyncEngine.dispose
    dispose_calls = []

    async def spy_dispose(self, *args, **kwargs):
        dispose_calls.append(self)
        return await real_dispose(self, *args, **kwargs)

    async def sample_coro():
        factory = QueueManager._get_nullpool_session_factory()
        return factory.kw["bind"]

    with patch.object(AsyncEngine, "dispose", side_effect=spy_dispose, autospec=True):
        engine = _run_coro_sync(sample_coro())
        assert engine is not None
        assert len(dispose_calls) == 1, "Engine should be disposed before thread loop shuts down!"


# ─────────────────────────────────────────────────────────────────
# BUG-009: Cinematic Red Design Standard
# ─────────────────────────────────────────────────────────────────
def test_audit_bug009_cinematic_red_standard():
    """Verify no non-rating amber/gold classes exist in audited website pages."""
    disallowed_regex = re.compile(r"(amber-\d+|text-rating-gold|bg-rating-gold|border-rating-gold|yellow-\d+)")
    pages = [
        ROOT_DIR / "website" / "app" / "achievements" / "page.tsx",
        ROOT_DIR / "website" / "app" / "catalog" / "page.tsx",
        ROOT_DIR / "website" / "app" / "notifications" / "page.tsx",
        ROOT_DIR / "website" / "app" / "profile" / "page.tsx",
        ROOT_DIR / "website" / "app" / "subscriptions" / "page.tsx",
    ]
    violations = []
    for p in pages:
        assert p.exists(), f"File missing: {p}"
        lines = p.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, 1):
            matches = disallowed_regex.findall(line)
            if matches:
                # Allowed only on IMDb/Kinopoisk rating badges
                if not any(k in line.lower() for k in ["imdb", "kinopoisk", "star_rating"]):
                    violations.append(f"{p.name}:{idx} -> {matches} in {line.strip()}")

    assert len(violations) == 0, f"Found {len(violations)} design violations:\n" + "\n".join(violations)
