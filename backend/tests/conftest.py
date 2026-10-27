import os
import sys
import asyncio
from urllib.parse import urlparse
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

    os.environ.clear()
    os.environ.update(original_env)


from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker  # noqa: E402
from app.infrastructure.db.session import Base  # noqa: E402
from app.infrastructure.db.models import *  # noqa: F403, E402


@pytest.fixture(scope="session")
def engine():
    _engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)
    yield _engine


@pytest.fixture(scope="session", autouse=True)
def setup_test_db(engine):
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
