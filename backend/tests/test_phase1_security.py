import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import Settings, settings
from app.api.deps import get_db_session


@pytest.mark.asyncio
async def test_dev_login_forbidden_in_production(monkeypatch):
    """Faza 1a: /auth/dev-login must return 403 in production."""
    monkeypatch.setattr(settings, "APP_ENV", "production")
    
    app.dependency_overrides[get_db_session] = lambda: None
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/api/v1/auth/dev-login", json={"telegram_id": 999999, "username": "hacker"})
            assert resp.status_code == 403, f"Expected 403 Forbidden in production, got {resp.status_code}"
    finally:
        app.dependency_overrides.pop(get_db_session, None)


def test_telegram_creds_defaults_are_empty(monkeypatch):
    """Faza 1b: TELEGRAM_API_ID/HASH/STRING_SESSION defaults must be empty/None."""
    monkeypatch.delenv("TELEGRAM_API_ID", raising=False)
    monkeypatch.delenv("TELEGRAM_API_HASH", raising=False)
    monkeypatch.delenv("TELEGRAM_STRING_SESSION", raising=False)
    s = Settings(
        BOT_TOKEN="test_token",
        STORAGE_CHANNEL_ID="12345",
        _env_file=None,
    )
    assert not s.TELEGRAM_API_ID or s.TELEGRAM_API_ID == 0
    assert s.TELEGRAM_API_HASH == ""
    assert s.TELEGRAM_STRING_SESSION == ""


def test_secret_key_production_validator():
    """Faza 1c: APP_ENV=production with default SECRET_KEY must fail validation."""
    with pytest.raises(Exception) as exc_info:
        Settings(
            APP_ENV="production",
            SECRET_KEY="change-me-in-production",
            BOT_TOKEN="test_token",
            STORAGE_CHANNEL_ID="12345",
            _env_file=None,
        )
    assert "SECRET_KEY" in str(exc_info.value)


def test_docker_compose_no_hardcoded_telegram_secrets():
    """Faza 1b: docker-compose.yml must not hardcode TELEGRAM_API_ID/HASH secrets."""
    with open("docker-compose.yml", "r", encoding="utf-8") as f:
        content = f.read()
    assert "32571063" not in content
    assert "fe3038cd47d8c37788a5f4bdeef00138" not in content


def test_gitignore_has_dump_and_bak():
    """Faza 1d: .gitignore must contain *.dump and *.bak."""
    with open(".gitignore", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]
    assert "*.dump" in lines
    assert "*.bak" in lines


def test_is_production_conflict_safest_wins():
    """
    APP_ENV va ENVIRONMENT to'qnashganda eng xavfsiz (production) tomoni g'alaba qozonishi shart.
    """
    # 1. APP_ENV=production, ENVIRONMENT=development
    s1 = Settings(APP_ENV="production", ENVIRONMENT="development", _env_file=None, BOT_TOKEN="x", STORAGE_CHANNEL_ID="1", SECRET_KEY="a"*32)
    assert s1.is_production is True

    # 2. APP_ENV=development, ENVIRONMENT=production
    s2 = Settings(APP_ENV="development", ENVIRONMENT="production", _env_file=None, BOT_TOKEN="x", STORAGE_CHANNEL_ID="1", SECRET_KEY="a"*32)
    assert s2.is_production is True

    # 3. APP_ENV=staging, ENVIRONMENT=dev
    s3 = Settings(APP_ENV="staging", ENVIRONMENT="dev", _env_file=None, BOT_TOKEN="x", STORAGE_CHANNEL_ID="1", SECRET_KEY="a"*32)
    assert s3.is_production is True

    # 4. Ikkalasi ham development
    s4 = Settings(APP_ENV="development", ENVIRONMENT="development", _env_file=None, BOT_TOKEN="x", STORAGE_CHANNEL_ID="1", SECRET_KEY="a"*32)
    assert s4.is_production is False


@pytest.mark.asyncio
async def test_dev_login_requires_explicit_enable_flag(monkeypatch):
    """
    /auth/dev-login faqat no-production rejimida VA explicit ENABLE_DEV_LOGIN=true bo'lganda ruxsat etiladi.
    """
    app.dependency_overrides[get_db_session] = lambda: None
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # Rejim 1: development ammo ENABLE_DEV_LOGIN=False (default) -> 403
            monkeypatch.setattr(settings, "APP_ENV", "development")
            monkeypatch.setattr(settings, "ENVIRONMENT", None)
            monkeypatch.setattr(settings, "ENABLE_DEV_LOGIN", False)
            resp = await ac.post("/api/v1/auth/dev-login", json={"telegram_id": 1111, "username": "dev1"})
            assert resp.status_code == 403
            assert "Dev login is disabled" in resp.text

            # Rejim 2: production ammo ENABLE_DEV_LOGIN=True -> baribir 403 (fail-safe)
            monkeypatch.setattr(settings, "APP_ENV", "production")
            monkeypatch.setattr(settings, "ENABLE_DEV_LOGIN", True)
            resp = await ac.post("/api/v1/auth/dev-login", json={"telegram_id": 1111, "username": "dev1"})
            assert resp.status_code == 403
    finally:
        app.dependency_overrides.pop(get_db_session, None)
