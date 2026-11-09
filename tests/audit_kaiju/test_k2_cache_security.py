import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.core.cache import clear_memory_cache, get_cache, set_cache
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel

@pytest.mark.asyncio
async def test_k2_admin_pending_series_does_not_leak_to_public(db_session):
    """
    K2 tekshiruvi: Admin huquqi bilan pending serial so'ralganda keshlanadi.
    Undan so'ng anonim/public foydalanuvchi xuddi shu serialni so'raganda,
    pending serial keshdan sizib chiqmasligi, balki 404 qaytishi SHART.
    """
    clear_memory_cache()

    # 1. DB ga faqat pending holatdagi serial qo'shamiz
    pending_series = SeriesModel(
        id=99991,
        title="Maxfiy Pending Serial",
        publish_status="pending"
    )
    db_session.add(pending_series)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Mock admin auth
        with patch("app.api.deps.get_current_admin", return_value={"id": 1, "role": "admin"}):
            # Admin publish_status=pending bilan so'raydi
            res_admin = await client.get("/api/v1/series/99991?publish_status=pending")
            assert res_admin.status_code == 200, f"Admin ko'ra olishi kerak, ammo: {res_admin.text}"
            data_admin = res_admin.json()
            assert data_admin["title"] == "Maxfiy Pending Serial"

        # Keshda 'cache:series:detail:99991:pending' paydo bo'ldi
        cached_admin = await get_cache("cache:series:detail:99991:pending")
        assert cached_admin is not None

        # 2. Public / Anonim foydalanuvchi so'raydi (tokensiz, default publish_status=published)
        res_public = await client.get("/api/v1/series/99991")
        # Public foydalanuvchiga 404 qaytishi SHART!
        assert res_public.status_code == 404, (
            f"XAVF: Pending serial public foydalanuvchiga keshdan sizib chiqdi! Status: {res_public.status_code}"
        )

        # 3. Public foydalanuvchi ataylab ?publish_status=pending yuborsa (tokensiz)
        res_leak_attempt = await client.get("/api/v1/series/99991?publish_status=pending")
        # 401 Unauthorized qaytishi shart!
        assert res_leak_attempt.status_code in (401, 403), (
            f"XAVF: Tokensiz foydalanuvchi ?publish_status=pending bilan keshni o'qiy oldi! Status: {res_leak_attempt.status_code}"
        )


@pytest.mark.asyncio
async def test_k2_404_responses_are_never_cached(db_session):
    """
    K2 tekshiruvi: Mavjud bo'lmagan serial yoki qism so'ralganda 404 qaytadi
    va bu xato javob keshga (in-memory yoki Redis) saqlanmasligi shart.
    """
    clear_memory_cache()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Mavjud bo'lmagan serial
        res_series = await client.get("/api/v1/series/88888888")
        assert res_series.status_code == 404

        # Keshda yo'qligini tekshiramiz
        cached_series = await get_cache("cache:series:detail:88888888:published")
        assert cached_series is None, "404 serial keshga yozilmasligi kerak!"

        # Mavjud bo'lmagan qism
        res_ep = await client.get("/api/v1/series/episodes/code/NONEXISTENTCODE99")
        assert res_ep.status_code == 404

        cached_ep = await get_cache("cache:episode:detail:NONEXISTENTCODE99")
        assert cached_ep is None, "404 qism keshga yozilmasligi kerak!"
