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
