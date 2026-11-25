import pytest
import time
import hmac
import hashlib
from httpx import AsyncClient, ASGITransport
from urllib.parse import urlencode

from app.main import app
from app.core.config import settings
from app.api.limiter import limiter

@pytest.fixture(autouse=True)
def manage_limiter():
    limiter.enabled = False
    yield
    limiter.enabled = True

@pytest.mark.asyncio
async def test_telegram_login_widget_success(monkeypatch):
    # Mock DB dependency
    from app.api.deps import get_db_session
    app.dependency_overrides[get_db_session] = lambda: None
    
    # Mock _upsert_telegram_user
    import app.api.v1.telegram_auth as auth_module
    
    class MockUser:
        id = 1
        telegram_id = 123456789
        is_banned = False
        
    async def mock_upsert(*args, **kwargs):
        return MockUser()
        
    monkeypatch.setattr(auth_module, "_upsert_telegram_user", mock_upsert)

    settings.BOT_TOKEN = "test_bot_token:123456"
    auth_date = int(time.time())
    
    payload = {
        "id": 123456789,
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser",
        "auth_date": auth_date,
    }
    
    sorted_items = sorted(payload.items(), key=lambda x: x[0])
    data_check_string = "\n".join([f"{k}={v}" for k, v in sorted_items])
    secret_key = hashlib.sha256(settings.BOT_TOKEN.encode('utf-8')).digest()
    computed_hash = hmac.new(
        secret_key, 
        data_check_string.encode('utf-8'), 
        hashlib.sha256
    ).hexdigest()
    
    payload["hash"] = computed_hash
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/auth/telegram-login", json=payload)
        assert resp.status_code == 200
        assert "access_token" in resp.json()

@pytest.mark.asyncio
async def test_telegram_login_widget_expired():
    settings.BOT_TOKEN = "test_bot_token:123456"
    auth_date = int(time.time()) - 90000  # Expired
    
    payload = {
        "id": 123456789,
        "auth_date": auth_date,
    }
    
    data_check_string = f"auth_date={auth_date}\nid=123456789"
    secret_key = hashlib.sha256(settings.BOT_TOKEN.encode('utf-8')).digest()
    payload["hash"] = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/auth/telegram-login", json=payload)
        assert resp.status_code == 401
        assert "expired" in resp.json()["detail"].lower()

@pytest.mark.asyncio
async def test_telegram_login_widget_tampered_hash():
    settings.BOT_TOKEN = "test_bot_token:123456"
    auth_date = int(time.time())
    
    payload = {
        "id": 123456789,
        "auth_date": auth_date,
        "hash": "invalidhash123456"
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/auth/telegram-login", json=payload)
        assert resp.status_code == 401
        assert "invalid hash" in resp.json()["detail"].lower()

@pytest.mark.asyncio
async def test_telegram_webapp_success(monkeypatch):
    # Mock DB dependency
    from app.api.deps import get_db_session
    app.dependency_overrides[get_db_session] = lambda: None
    
    # Mock _upsert_telegram_user
    import app.api.v1.telegram_auth as auth_module
    
    class MockUser:
        id = 1
        telegram_id = 123456789
        is_banned = False
        
    async def mock_upsert(*args, **kwargs):
        return MockUser()
        
    monkeypatch.setattr(auth_module, "_upsert_telegram_user", mock_upsert)

    settings.BOT_TOKEN = "test_bot_token:123456"
    auth_date = int(time.time())
    
    user_json = '{"id":123456789,"first_name":"Test","last_name":"User","username":"testuser"}'
    raw_data = {
        "query_id": "AAExx...",
        "user": user_json,
        "auth_date": str(auth_date),
    }
    
    sorted_items = sorted(raw_data.items(), key=lambda x: x[0])
    data_check_string = "\n".join([f"{k}={v}" for k, v in sorted_items])
    secret_key = hmac.new(
        "WebAppData".encode('utf-8'),
        settings.BOT_TOKEN.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    computed_hash = hmac.new(
        secret_key,
        data_check_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    raw_data["hash"] = computed_hash
    initData = urlencode(raw_data)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/auth/telegram-webapp", json={"initData": initData})
        assert resp.status_code == 200
        assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_bot_login_unauthorized_without_secret():
    settings.BOT_API_SECRET = "super_secret_bot_token_12345"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/auth/bot-login", json={"telegram_id": 999111})
        assert resp.status_code in (403, 422)


@pytest.mark.asyncio
async def test_bot_login_wrong_secret():
    settings.BOT_API_SECRET = "super_secret_bot_token_12345"
    headers = {"X-Bot-Secret": "wrong_secret"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/auth/bot-login", json={"telegram_id": 999111}, headers=headers)
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_bot_login_success(monkeypatch):
    from app.api.deps import get_db_session
    app.dependency_overrides[get_db_session] = lambda: None

    import app.api.v1.telegram_auth as auth_module

    class MockUser:
        id = 42
        telegram_id = 999111
        is_banned = False

    async def mock_upsert(*args, **kwargs):
        return MockUser()

    monkeypatch.setattr(auth_module, "_upsert_telegram_user", mock_upsert)
    settings.BOT_API_SECRET = "super_secret_bot_token_12345"
    headers = {"X-Bot-Secret": "super_secret_bot_token_12345"}

    payload = {
        "telegram_id": 999111,
        "first_name": "Asilbek",
        "username": "asilbek_dev"
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/auth/bot-login", json=payload, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["message"] == "Login successful"


@pytest.mark.asyncio
async def test_public_config_returns_bot_username_and_stream_flag(monkeypatch):
    monkeypatch.setattr(settings, "BOT_USERNAME", "@MediaPlusNewBot")
    monkeypatch.setattr(settings, "WEBSITE_URL", "https://kinochi-project-alpha.vercel.app/")
    if hasattr(settings, "STREAM_SERVICE_URL"):
        monkeypatch.setattr(settings, "STREAM_SERVICE_URL", "")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/auth/public-config")
        assert resp.status_code == 200
        data = resp.json()
        assert data["bot_username"] == "MediaPlusNewBot"
        assert data["website_url"] == "https://kinochi-project-alpha.vercel.app"
        assert data["stream_enabled"] is False


@pytest.mark.asyncio
async def test_public_config_includes_social_links_with_env_overrides(monkeypatch):
    monkeypatch.setattr(settings, "BOT_USERNAME", "@MediaPlusOfficialBot")
    monkeypatch.delenv("TELEGRAM_CHANNEL_URL", raising=False)
    monkeypatch.delenv("REDIRECT_CHANNEL_URL", raising=False)
    monkeypatch.delenv("TIKTOK_URL", raising=False)
    monkeypatch.setenv("YOUTUBE_CHANNEL_URL", "https://www.youtube.com/@CustomMediaPlus")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/v1/auth/public-config")
    assert resp.status_code == 200
    links = resp.json()["social_links"]
    assert links["telegram_bot"] == "https://t.me/MediaPlusOfficialBot"
    assert links["telegram_channel"] == "https://t.me/MediaPlusOfficial"
    assert links["instagram"] == "https://www.instagram.com/mediaplusofficialbot/"
    assert links["youtube"] == "https://www.youtube.com/@CustomMediaPlus"
    assert links["facebook"] == "https://www.facebook.com/profile.php?id=1321205927744639"
    assert links["tiktok"] == ""

    monkeypatch.setenv("TIKTOK_URL", "https://www.tiktok.com/@mediaplusofficial")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp2 = await ac.get("/api/v1/auth/public-config")
    assert resp2.json()["social_links"]["tiktok"] == "https://www.tiktok.com/@mediaplusofficial"

