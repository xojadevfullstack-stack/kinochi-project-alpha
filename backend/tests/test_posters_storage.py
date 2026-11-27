"""Tests for Slice 1: Telegram poster upload (channel + topic) and public proxy endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import ASGITransport, AsyncClient


def test_build_telegram_poster_url_uses_public_base(monkeypatch):
    from app.api.v1.posters import build_telegram_poster_url

    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.mediaplus.uz/")
    url = build_telegram_poster_url("AgACAgIAAxkBAAIB2IVpTPkhU2zhvPr2Iv36")
    assert url == "https://api.mediaplus.uz/api/v1/posters/tg/AgACAgIAAxkBAAIB2IVpTPkhU2zhvPr2Iv36"


@pytest.mark.asyncio
async def test_send_photo_with_result_passes_topic_and_extracts_file_id():
    from app.infrastructure.telegram.telegram_client import TelegramClient

    client = TelegramClient()
    client.bot_token = "123456:TEST_TOKEN"
    client.base_url = "https://api.telegram.org/bot123456:TEST_TOKEN"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "ok": True,
        "result": {
            "message_id": 777,
            "photo": [
                {"file_id": "AgAC_SMALL_123456789012345"},
                {"file_id": "AgAC_LARGE_ABCDEFGHIJKLMNO"},
            ],
        },
    }

    mock_http = AsyncMock()
    mock_http.post = AsyncMock(return_value=mock_resp)
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_http)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("app.infrastructure.telegram.telegram_client.httpx.AsyncClient", return_value=mock_ctx):
        res = await client.send_photo_with_result(
            chat_id=-1001234567890,
            photo_bytes=b"\x89PNG\r\n\x1a\nfake",
            filename="poster.png",
            caption="Test",
            message_thread_id=42,
        )

    assert res.success is True
    assert res.file_id == "AgAC_LARGE_ABCDEFGHIJKLMNO"
    called_data = mock_http.post.call_args.kwargs["data"]
    assert called_data["message_thread_id"] == "42"


@pytest.mark.asyncio
async def test_upload_poster_to_telegram_saves_in_channel_and_topic(monkeypatch):
    from app.api.v1.posters import upload_poster_to_telegram
    from app.infrastructure.telegram.telegram_client import SendMessageResult

    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.example.com")

    calls = []

    async def fake_send_photo_with_result(**kwargs):
        calls.append(kwargs)
        return SendMessageResult(success=True, file_id="AgAC_POSTER_FILE_ID_1234567890")

    with (
        patch("app.api.v1.posters.settings.STORAGE_CHANNEL_ID", -100999888777),
        patch(
            "app.api.v1.posters.telegram_client.send_photo_with_result",
            side_effect=fake_send_photo_with_result,
        ),
    ):
        url = await upload_poster_to_telegram(
            photo_bytes=b"fake_jpeg_bytes",
            title="Muqaddima",
            code="1234",
            topic_chat_id=-100555444333,
            topic_id=91,
        )

    assert url == "https://api.example.com/api/v1/posters/tg/AgAC_POSTER_FILE_ID_1234567890"
    assert len(calls) == 2
    assert calls[0]["chat_id"] == -100999888777
    assert calls[0].get("message_thread_id") is None
    assert calls[1]["chat_id"] == -100555444333
    assert calls[1]["message_thread_id"] == 91


@pytest.mark.asyncio
async def test_get_telegram_poster_proxy_validates_and_streams():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        bad_resp = await ac.get("/api/v1/posters/tg/short")
        assert bad_resp.status_code == 400

        with patch(
            "app.api.v1.posters.telegram_client.download_file_bytes",
            new=AsyncMock(return_value=(b"\xff\xd8\xff\xe0JPEGDATA", "image/jpeg")),
        ):
            ok_resp = await ac.get("/api/v1/posters/tg/AgACAgIAAxkBAAIB2IVpTPkhU2zhvPr2Iv36")
            assert ok_resp.status_code == 200
            assert ok_resp.content == b"\xff\xd8\xff\xe0JPEGDATA"
            assert ok_resp.headers["content-type"] == "image/jpeg"
            assert "immutable" in ok_resp.headers["cache-control"]

        with patch(
            "app.api.v1.posters.telegram_client.download_file_bytes",
            new=AsyncMock(return_value=None),
        ):
            missing_resp = await ac.get("/api/v1/posters/tg/AgACAgIAAxkBAAIB2IVpTPkhU2zhvPr2MISSING")
            assert missing_resp.status_code == 404


@pytest.mark.asyncio
async def test_download_file_bytes_caches_file_path_with_ttl_seconds():
    from app.infrastructure.telegram.telegram_client import TelegramClient

    client = TelegramClient()
    client.bot_token = "123456:TEST_TOKEN"
    client.base_url = "https://api.telegram.org/bot123456:TEST_TOKEN"

    meta_resp = MagicMock()
    meta_resp.status_code = 200
    meta_resp.json.return_value = {"ok": True, "result": {"file_path": "photos/file_12.jpg"}}

    dl_resp = MagicMock()
    dl_resp.status_code = 200
    dl_resp.content = b"IMG_BYTES"

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(side_effect=[meta_resp, dl_resp])
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_http)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.infrastructure.telegram.telegram_client.httpx.AsyncClient", return_value=mock_ctx),
        patch("app.core.cache.get_cache", new=AsyncMock(return_value=None)),
        patch("app.core.cache.set_cache", new=AsyncMock(return_value=True)) as mock_set_cache,
    ):
        res = await client.download_file_bytes("AgACAgIAAxkBAAIB2IVpTPkhU2zhvPr2Iv36")

    assert res == (b"IMG_BYTES", "image/jpeg")
    mock_set_cache.assert_awaited_once()
    assert "ttl_seconds" in mock_set_cache.call_args.kwargs


@pytest.mark.asyncio
async def test_download_file_bytes_falls_back_to_legacy_bot_token(monkeypatch):
    from app.infrastructure.telegram.telegram_client import TelegramClient

    monkeypatch.setenv("LEGACY_BOT_TOKEN", "999999:LEGACY_TOKEN")
    client = TelegramClient()
    client.bot_token = "123456:NEW_TOKEN"
    client.base_url = "https://api.telegram.org/bot123456:NEW_TOKEN"

    fail_meta = MagicMock(status_code=400)
    fail_meta.json.return_value = {"ok": False, "description": "Bad Request: wrong file_id"}
    ok_meta = MagicMock(status_code=200)
    ok_meta.json.return_value = {"ok": True, "result": {"file_path": "photos/legacy.jpg"}}
    ok_dl = MagicMock(status_code=200, content=b"LEGACY_BYTES")

    mock_http = AsyncMock()
    mock_http.get = AsyncMock(side_effect=[fail_meta, ok_meta, ok_dl])
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_http)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with (
        patch("app.infrastructure.telegram.telegram_client.httpx.AsyncClient", return_value=mock_ctx),
        patch("app.core.cache.get_cache", new=AsyncMock(return_value=None)),
        patch("app.core.cache.set_cache", new=AsyncMock(return_value=True)),
    ):
        res = await client.download_file_bytes("AgACAgIAAyEGAATgPfgXAAIT02sHHfkREfhwTogaQ4vpYCpYDDxAAAKwJmsbXv44SPuOK6nl_9VYAQADAgADeAADPQQ")

    assert res == (b"LEGACY_BYTES", "image/jpeg")


@pytest.mark.asyncio
async def test_backfill_one_unlocalized_poster_updates_db_and_skips_failed_with_cooldown(monkeypatch):
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.api.v1 import posters as posters_mod
    from app.infrastructure.db.models.movie import MovieModel
    from app.infrastructure.db.models.series import SeriesModel
    from app.infrastructure.db.session import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    posters_mod._BACKFILL_SKIP_CACHE.clear()
    posters_mod._BACKFILL_DAY_COUNTS.clear()
    fake_redis_cache: dict[str, str] = {}

    async def fake_get_cache(key):
        return fake_redis_cache.get(key)

    async def fake_set_cache(key, val, ttl_seconds=0):
        fake_redis_cache[key] = str(val)
        return True

    async def fake_del_pattern(pattern):
        return 0

    calls = []

    async def fake_localize(title, tmdb_id=None, content_type="movie", manual_poster_url=None, **kwargs):
        calls.append((content_type, title))
        if title == "Rejected Poster":
            return None
        return f"https://kinochi.example/api/v1/posters/tg/{title.replace(' ', '_')}"

    monkeypatch.setattr("app.core.cache.get_cache", fake_get_cache)
    monkeypatch.setattr("app.core.cache.set_cache", fake_set_cache)
    monkeypatch.setattr("app.core.cache.delete_cache_pattern", fake_del_pattern)
    monkeypatch.setattr("app.infrastructure.external.poster_localizer.localize_poster_and_upload", fake_localize)

    async with Session() as db:
        db.add(MovieModel(title="Rejected Poster", code="REJ01", tmdb_id=101, poster_url="https://image.tmdb.org/t/p/w500/r.jpg"))
        db.add(SeriesModel(title="Yigitlar", tmdb_id=76479, poster_url="https://image.tmdb.org/t/p/w500/y.jpg"))
        await db.commit()

        # First call rejects Movie #1 ("Rejected Poster") and sets cooldown
        r1 = await posters_mod.backfill_one_unlocalized_poster(db, allow_in_testing=True)
        await db.commit()
        assert r1["localized"] == 0 and r1["skipped"] == 1

        # Second call MUST skip "Rejected Poster" due to cooldown and localize Series "Yigitlar"
        r2 = await posters_mod.backfill_one_unlocalized_poster(db, allow_in_testing=True)
        await db.commit()
        assert r2["localized"] == 1 and r2["media_type"] == "series"
        assert calls == [("movie", "Rejected Poster"), ("tv", "Yigitlar")]

    await engine.dispose()


@pytest.mark.asyncio
async def test_backfill_stops_when_daily_quota_cap_reached(monkeypatch):
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.api.v1 import posters as posters_mod
    from app.infrastructure.db.models.movie import MovieModel
    from app.infrastructure.db.session import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    posters_mod._BACKFILL_SKIP_CACHE.clear()
    posters_mod._BACKFILL_DAY_COUNTS.clear()
    monkeypatch.setenv("POSTER_BACKFILL_DAILY_LIMIT", "1")
    fake_cache: dict[str, str] = {}

    async def fake_get_cache(key):
        return fake_cache.get(key)

    async def fake_set_cache(key, val, ttl_seconds=0):
        fake_cache[key] = str(val)
        return True

    async def fake_del_pattern(pattern):
        return 0

    calls = []

    async def fake_localize(title, **kwargs):
        calls.append(title)
        return f"https://kinochi.example/api/v1/posters/tg/{title}"

    monkeypatch.setattr("app.core.cache.get_cache", fake_get_cache)
    monkeypatch.setattr("app.core.cache.set_cache", fake_set_cache)
    monkeypatch.setattr("app.core.cache.delete_cache_pattern", fake_del_pattern)
    monkeypatch.setattr("app.infrastructure.external.poster_localizer.localize_poster_and_upload", fake_localize)

    async with Session() as db:
        db.add(MovieModel(title="Film1", code="F01", tmdb_id=1, poster_url="https://image.tmdb.org/t/p/w500/1.jpg"))
        db.add(MovieModel(title="Film2", code="F02", tmdb_id=2, poster_url="https://image.tmdb.org/t/p/w500/2.jpg"))
        await db.commit()

        first = await posters_mod.backfill_one_unlocalized_poster(db, allow_in_testing=True)
        await db.commit()
        second = await posters_mod.backfill_one_unlocalized_poster(db, allow_in_testing=True)
        assert first["localized"] == 1
        assert second.get("capped") is True
        assert second["localized"] == 0
        assert len(calls) == 1

    await engine.dispose()



