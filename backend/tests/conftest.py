import os
import sys
import asyncio
from urllib.parse import urlparse
from unittest.mock import AsyncMock, MagicMock
import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Pydantic Settings ilova import qilingandayoq (module-level) baholanadi.
# Shuning uchun testlar ishga tushishidan avval zaruriy test muhit o'zgaruvchilarini beramiz.
os.environ["APP_ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://127.0.0.1:1/0"
os.environ["SECRET_KEY"] = "super-secret-test-key-for-jwt"
os.environ["BOT_TOKEN"] = "123456789:TestBotTokenABC"
os.environ["STORAGE_CHANNEL_ID"] = "-1001234567890"
os.environ["BOT_API_SECRET"] = "test-bot-api-secret"
os.environ["TELEGRAM_STRING_SESSION"] = "dummy_session"
os.environ["TMDB_API_KEY"] = "dummy_tmdb_key"
os.environ["GEMINI_API_KEY"] = "dummy_gemini_key"
os.environ["KINOPOISK_API_KEY"] = "dummy_kinopoisk_key"
os.environ["AUTO_CONTENT_ENABLED"] = "true"  # Seed ingestor testlari kill switch bilan bloklanmasligi uchun

from app.core.config import Settings  # noqa: E402
# Test rejimida .env fayllardan butunlay mustaqil bo'lish kafolati
Settings.model_config["env_file"] = None


def verify_safe_test_db(url_str: str) -> bool:
    """
    Xavfsizlik nazorati:
    Real Postgres testlari FAQAT localhost / 127.0.0.1, ruxsat etilgan port (default 5433,
    yoki CI uchun TEST_DB_PORT) va 'kinochi_v2_test' bazasida bajarilishi shart.
    Aks holda darhol RuntimeError otiladi va barcha operatsiyalar bekor qilinadi.
    """
    if not url_str:
        raise RuntimeError("DATABASE_URL ko'rsatilmagan!")
    clean_url = url_str.replace("postgresql+asyncpg://", "http://").replace("postgres://", "http://")
    parsed = urlparse(clean_url)

    host = parsed.hostname
    port = parsed.port
    db_name = parsed.path.lstrip("/")

    if host not in ("localhost", "127.0.0.1", "::1"):
        raise RuntimeError(f"XAVF: Ruxsat berilmagan DB host: '{host}'. Faqat localhost/127.0.0.1 ga ruxsat!")
    allowed_port = int(os.environ.get("TEST_DB_PORT", "5433"))
    if port != allowed_port:
        raise RuntimeError(f"XAVF: Ruxsat berilmagan DB port: '{port}'. Faqat {allowed_port}-portga ruxsat!")
    if db_name != "kinochi_v2_test":
        raise RuntimeError(f"XAVF: Ruxsat berilmagan DB nomi: '{db_name}'. Faqat 'kinochi_v2_test' ga ruxsat!")
    return True


@pytest.fixture(scope="session", autouse=True)
def mock_env_vars():
    """Testlar davomida test muhit o'zgaruvchilari qat'iy saqlanishini ta'minlaydi."""
    original_env = dict(os.environ)

    os.environ["APP_ENV"] = "testing"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    os.environ["REDIS_URL"] = "redis://127.0.0.1:1/0"
    os.environ["SECRET_KEY"] = "super-secret-test-key-for-jwt"
    os.environ["BOT_TOKEN"] = "123456789:TestBotTokenABC"
    os.environ["STORAGE_CHANNEL_ID"] = "-1001234567890"
    os.environ["BOT_API_SECRET"] = "test-bot-api-secret"
    os.environ["AUTO_CONTENT_ENABLED"] = "true"

    yield

    for k in ["APP_ENV", "DATABASE_URL", "REDIS_URL", "SECRET_KEY", "BOT_TOKEN", "STORAGE_CHANNEL_ID", "BOT_API_SECRET", "AUTO_CONTENT_ENABLED"]:
        if k in original_env:
            os.environ[k] = original_env[k]
        else:
            os.environ.pop(k, None)


from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker  # noqa: E402
import app.infrastructure.db.session as db_session_module  # noqa: E402
from app.infrastructure.db.session import Base  # noqa: E402
from app.infrastructure.db.models import *  # noqa: F403, E402
from app.infrastructure.db.models.ingest_item import IngestItemModel  # noqa: F401, E402


def make_mock_db_result(scalar=None, scalars_list=None, rows=None, first=None) -> MagicMock:
    """
    AsyncMock session.execute natijasida .all(), .scalar_one_or_none(),
    .scalars().all(), .first() SINXRON bo'lishini ta'minlovchi umumiy yordamchi.
    """
    result = MagicMock()
    result.scalar_one_or_none.return_value = scalar
    result.scalar.return_value = scalar
    result.all.return_value = list(rows) if rows is not None else []
    result.first.return_value = first
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = list(scalars_list) if scalars_list is not None else []
    scalars_mock.first.return_value = first
    result.scalars.return_value = scalars_mock
    return result


def configure_mock_session(session: AsyncMock, **kwargs) -> MagicMock:
    """session.execute = AsyncMock(return_value=result) ni sinxron MagicMock result bilan sozlaydi."""
    result = make_mock_db_result(**kwargs)
    session.execute = AsyncMock(return_value=result)
    return result


@pytest.fixture(scope="session")
def engine(tmp_path_factory):
    url = os.environ["DATABASE_URL"]
    if "sqlite" in url and ":memory:" in url:
        db_file = tmp_path_factory.mktemp("test_db") / "test_shared.sqlite3"
        file_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
        _engine = create_async_engine(
            file_url,
            echo=False,
            connect_args={"check_same_thread": False, "timeout": 30},
        )
    else:
        _engine = create_async_engine(url, echo=False)
    yield _engine


@pytest.fixture(scope="session", autouse=True)
def setup_test_db(engine):
    test_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    db_session_module.engine = engine
    db_session_module.async_session_factory = test_session_factory
    try:
        from scraper.queue_manager import QueueManager
        QueueManager._default_session_factory = test_session_factory
    except Exception:
        pass

    async def init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    asyncio.run(init_db())
    yield
    asyncio.run(drop_db())


@pytest.fixture
async def db_session(engine):
    """Har bir test uchun alohida AsyncSession fixture."""
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session


@pytest.fixture
def client():
    """FastAPI ilovasi uchun TestClient fixture."""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


LOCAL_PG_TEST_URL = os.environ.get(
    "LOCAL_PG_TEST_URL",
    f"postgresql+asyncpg://postgres:postgres@localhost:{os.environ.get('TEST_DB_PORT', '5433')}/kinochi_v2_test"
)


@pytest.fixture(scope="session")
def safe_pg_engine():
    """
    Lokal 5433-portdagi kinochi_v2_test uchun xavfsiz PostgreSQL engine.
    verify_safe_test_db orqali har doim tekshiriladi.
    """
    verify_safe_test_db(LOCAL_PG_TEST_URL)
    _engine = create_async_engine(LOCAL_PG_TEST_URL, echo=False)
    yield _engine
    asyncio.run(_engine.dispose())
