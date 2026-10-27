import pytest
from sqlalchemy import text
from app.core.config import Settings as BackendSettings
from bot.config import Settings as BotSettings
from tests.conftest import verify_safe_test_db


def test_autopilot_class_defaults_frozen():
    """
    F0 / C0.1 talabi: Autopilot default qiymatlari klass darajasida qat'iy tekshiriladi:
    - Backend: AUTO_CONTENT_ENABLED=False, AUTO_INDEX_DRY_RUN=True, AUTO_INDEX_ALLOWED_CHAT_IDS=[]
    - Bot: AUTO_CONTENT_ENABLED=False, AUTO_INDEX_DRY_RUN=False, AUTO_INDEX_ALLOWED_CHAT_IDS=[]
    """
    # Backend klass defaultlari
    assert BackendSettings.model_fields["AUTO_CONTENT_ENABLED"].default is False
    assert BackendSettings.model_fields["AUTO_INDEX_DRY_RUN"].default is True
    assert BackendSettings.model_fields["AUTO_INDEX_ALLOWED_CHAT_IDS"].default == []

    # Bot klass defaultlari
    assert BotSettings.model_fields["AUTO_CONTENT_ENABLED"].default is False
    assert BotSettings.model_fields["AUTO_INDEX_DRY_RUN"].default is False
    assert BotSettings.model_fields["AUTO_INDEX_ALLOWED_CHAT_IDS"].default == []


def test_settings_env_isolation_from_dotenv():
    """
    F0 / C0.1 talabi: Testlar lokal .env faylini o'qimasligi shart.
    Test rejimida Settings model_config['env_file'] bo'sh/None bo'lishi kafolatlanadi.
    """
    # Test rejimida env_file o'qilmaydi
    assert BackendSettings.model_config.get("env_file") is None


def test_postgres_safety_guard_rejects_unsafe_databases():
    """
    F0 / C0.1 talabi: Postgres fixture faqat localhost:5433 dagi 'kinochi_v2_test'
    bazasiga ruxsat beradi. Aks holda RuntimeError otilishi shart.
    """
    # 1. Masofaviy Neon host bo'lsa -> Rad etiladi
    with pytest.raises(RuntimeError, match="Ruxsat berilmagan DB host"):
        verify_safe_test_db("postgresql+asyncpg://user:pass@ep-frosty-cherry.neon.tech:5432/neondb")

    # 2. Port 5433 bo'lmasa -> Rad etiladi
    with pytest.raises(RuntimeError, match="Ruxsat berilmagan DB port"):
        verify_safe_test_db("postgresql+asyncpg://postgres:postgres@localhost:5432/kinochi_v2_test")

    # 3. DB nomi kinochi_v2_test bo'lmasa -> Rad etiladi
    with pytest.raises(RuntimeError, match="Ruxsat berilmagan DB nomi"):
        verify_safe_test_db("postgresql+asyncpg://postgres:postgres@localhost:5433/production_db")

    # 4. Aynan localhost, 5433 va kinochi_v2_test -> Muvaffaqiyatli
    assert verify_safe_test_db("postgresql+asyncpg://postgres:postgres@localhost:5433/kinochi_v2_test") is True
    assert verify_safe_test_db("postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/kinochi_v2_test") is True


@pytest.mark.asyncio
async def test_db_session_fixture(db_session):
    """C0.1: db_session fixture to'g'ri ishlashini tekshirish."""
    res = await db_session.execute(text("SELECT 1 AS num"))
    val = res.scalar()
    assert val == 1


def test_api_client_fixture(client):
    """C0.1: API client fixture to'g'ri ishlashini tekshirish."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
