import pytest
import time
import hmac
import hashlib
from httpx import AsyncClient, ASGITransport
from urllib.parse import urlencode

from app.main import app
from app.core.config import settings

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
