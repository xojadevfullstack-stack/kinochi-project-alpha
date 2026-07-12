import os
import pytest

# Pydantic Settings ilova import qilingandayoq (module-level) baholanadi.
# Shuning uchun testlar ishga tushishidan avval zaruriy muhit o'zgaruvchilarini beramiz.
os.environ["APP_ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "super-secret-test-key-for-jwt"
os.environ["BOT_TOKEN"] = "123456789:TestBotTokenABC"
os.environ["STORAGE_CHANNEL_ID"] = "-1001234567890"
os.environ["BOT_API_SECRET"] = "test-bot-api-secret"

@pytest.fixture(scope="session", autouse=True)
def mock_env_vars():
    """
    Testlar davomida minimal muhit o'zgaruvchilari bo'lishini kafolatlaydigan fixture.
    Agar biron test o'zgaruvchini o'chirib yuborsa, bu yerda qayta tiklash mumkin.
    """
    original_env = dict(os.environ)
    
    os.environ["APP_ENV"] = "testing"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    os.environ["SECRET_KEY"] = "super-secret-test-key-for-jwt"
    os.environ["BOT_TOKEN"] = "123456789:TestBotTokenABC"
    os.environ["STORAGE_CHANNEL_ID"] = "-1001234567890"
    os.environ["BOT_API_SECRET"] = "test-bot-api-secret"
    
    yield
    
    os.environ.clear()
    os.environ.update(original_env)

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.infrastructure.db.session import Base
from app.infrastructure.db.models import * # Import all models to register with Base

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
