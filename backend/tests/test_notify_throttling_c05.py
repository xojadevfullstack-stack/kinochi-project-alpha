from unittest.mock import AsyncMock, patch
import pytest
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_db_session, get_admin_or_bot
from app.infrastructure.db.session import Base
from app.infrastructure.db.models.series import SeriesModel
from app.infrastructure.db.models.series_subscription import SeriesSubscriptionModel
from app.api.v1.series_subscriptions import broadcast_new_episode_notification


from sqlalchemy.pool import StaticPool

@pytest.fixture
async def notify_test_db():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield engine, session_factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_notify_throttling_600_subscribers(notify_test_db):
    """
    C0.5: 600 ta obunachiga xabarnoma yuborilganda:
    - 600 ta 0.05s li sleep chaqiruvi (20 msg/sec cheklovi).
    - Har 500 tada 1 ta 1.0s li qo'shimcha pause.
    """
    _, session_factory = notify_test_db

    async with session_factory() as session:
        ser = SeriesModel(id=1, title="Test Series Throttling", publish_status="published")
        session.add(ser)
        for i in range(1, 601):
            session.add(SeriesSubscriptionModel(series_id=1, telegram_user_id=1000 + i))
        await session.commit()

    sleep_calls = []

    async def mock_sleep(delay):
        sleep_calls.append(delay)

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 123}})

    mock_transport = httpx.MockTransport(mock_handler)

    with patch("asyncio.sleep", side_effect=mock_sleep), \
         patch("httpx.AsyncClient", return_value=httpx.AsyncClient(transport=mock_transport)):
        async with session_factory() as session:
            res = await broadcast_new_episode_notification(
                series_id=1,
                season_number=1,
                episode_number=1,
                display_code="s1e1",
                db=session
            )

    assert res["success"] is True
    assert res["notified_count"] == 600
    assert res["total_subscribers"] == 600

    count_005 = sleep_calls.count(0.05)
    count_10 = sleep_calls.count(1.0)
    assert count_005 == 600, f"Kutilgan 600 ta 0.05s sleep, ammo: {count_005}"
    assert count_10 == 1, f"Kutilgan 1 ta 1.0s sleep (500-chi xabardan keyin), ammo: {count_10}"


@pytest.mark.asyncio
async def test_notify_retry_after_429(notify_test_db):
    """
    C0.5: Telegram 429 RetryAfter qaytarganda:
    - retry_after muddatini kutadi va 1 marta qayta urinadi.
    """
    _, session_factory = notify_test_db

    async with session_factory() as session:
        ser = SeriesModel(id=2, title="Test Series 429", publish_status="published")
        session.add(ser)
        session.add(SeriesSubscriptionModel(series_id=2, telegram_user_id=2001))
        await session.commit()

    sleep_calls = []

    async def mock_sleep(delay):
        sleep_calls.append(delay)

    attempt = 0

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempt
        attempt += 1
        if attempt == 1:
            return httpx.Response(429, json={"ok": False, "parameters": {"retry_after": 2.5}})
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 456}})

    mock_transport = httpx.MockTransport(mock_handler)

    with patch("asyncio.sleep", side_effect=mock_sleep), \
         patch("httpx.AsyncClient", return_value=httpx.AsyncClient(transport=mock_transport)):
        async with session_factory() as session:
            res = await broadcast_new_episode_notification(
                series_id=2,
                season_number=1,
                episode_number=1,
                display_code="s2e1",
                db=session
            )

    assert res["success"] is True
    assert res["notified_count"] == 1
    assert 2.5 in sleep_calls, f"429 da 2.5s kutilgan sleep chaqirilmadi: {sleep_calls}"
    assert attempt == 2, f"Kutilgan 2 marta urinish (1-muvaffaqiyatsiz, 2-qayta), lekin {attempt}"


@pytest.mark.asyncio
async def test_notify_forbidden_403_deletes_subscription(notify_test_db):
    """
    C0.5: Telegram 403 Forbidden (bloklagan foydalanuvchi) qaytganda:
    - Foydalanuvchining serial obunasi bazadan o'chiriladi.
    - Qolgan foydalanuvchilarga jo'natish davom etadi.
    """
    _, session_factory = notify_test_db

    async with session_factory() as session:
        ser = SeriesModel(id=3, title="Test Series 403", publish_status="published")
        session.add(ser)
        session.add(SeriesSubscriptionModel(series_id=3, telegram_user_id=3001))
        session.add(SeriesSubscriptionModel(series_id=3, telegram_user_id=3002))
        await session.commit()

    def mock_handler(request: httpx.Request) -> httpx.Response:
        import json
        payload = json.loads(request.content.decode("utf-8"))
        if payload.get("chat_id") == 3001:
            return httpx.Response(403, json={"ok": False, "error_code": 403, "description": "Forbidden: bot was blocked by the user"})
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 789}})

    mock_transport = httpx.MockTransport(mock_handler)

    with patch("asyncio.sleep", new_callable=AsyncMock), \
         patch("httpx.AsyncClient", return_value=httpx.AsyncClient(transport=mock_transport)):
        async with session_factory() as session:
            res = await broadcast_new_episode_notification(
                series_id=3,
                season_number=1,
                episode_number=1,
                display_code="s3e1",
                db=session
            )

    assert res["success"] is True
    assert res["notified_count"] == 1

    # 3001 obunasi o'chirilgani, 3002 esa qolgani tekshiriladi
    async with session_factory() as session:
        subs = (await session.execute(
            select(SeriesSubscriptionModel.telegram_user_id).where(SeriesSubscriptionModel.series_id == 3)
        )).scalars().all()
        assert 3001 not in subs, "403 qaytargan foydalanuvchi obunadan o'chirilmadi!"
        assert 3002 in subs, "Faol foydalanuvchi obunasi tasodifan o'chirilgan!"


@pytest.mark.asyncio
async def test_notify_endpoint_returns_immediately(notify_test_db):
    """
    C0.5: /series/{id}/notify-new-episode endpoint tezda javob qaytaradi,
    broadcast esa fonda (BackgroundTasks) rejalashtiriladi.
    Endpoint javob formati o'zgarmasligi tasdiqlanadi.
    """
    _, session_factory = notify_test_db

    async with session_factory() as session:
        ser = SeriesModel(id=4, title="Test Series NonBlocking", publish_status="published")
        session.add(ser)
        for i in range(1, 11):
            session.add(SeriesSubscriptionModel(series_id=4, telegram_user_id=4000 + i))
        await session.commit()

    async def override_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_db
    app.dependency_overrides[get_admin_or_bot] = lambda: {"role": "admin"}

    client = TestClient(app)
    try:
        with patch("app.api.v1.series_subscriptions.broadcast_new_episode_notification", new_callable=AsyncMock) as mock_broadcast:
            resp = client.post(
                "/api/v1/series/4/notify-new-episode",
                json={
                    "season_number": 1,
                    "episode_number": 2,
                    "display_code": "s4_e2",
                    "episode_title": "Episode 2"
                }
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["success"] is True
            assert data["notified_count"] == 10
            assert data["total_subscribers"] == 10
            mock_broadcast.assert_called_once()
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        app.dependency_overrides.pop(get_admin_or_bot, None)
