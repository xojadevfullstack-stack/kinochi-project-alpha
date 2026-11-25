from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_copy_only_aborts_before_fast_download_on_copy_error(tmp_path):
    from scraper.telethon_moderator_pipeline import TelethonModeratorPipeline

    mock_client = AsyncMock()
    mock_client.get_input_entity = AsyncMock(return_value=-100123456)
    mock_client.send_file = AsyncMock(side_effect=RuntimeError("CHAT_FORWARDS_RESTRICTED"))

    pipeline = TelethonModeratorPipeline(
        client=mock_client,
        duplicate_checker=MagicMock(),
        copy_only=True,
    )
    video_msg = MagicMock(id=99, file=MagicMock(size=50 * 1024 * 1024), media=MagicMock(document=MagicMock()))

    with patch("scraper.telethon_moderator_pipeline.fast_download", new=AsyncMock()) as mock_fast_dl:
        res = await pipeline._upload_video_to_chat(video_msg, -100123456, reply_to=None, caption="Test")

    assert res is None
    assert mock_client.send_file.await_count >= 1
    mock_fast_dl.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_catalog_worker_tick_respects_daily_cap_sources_and_session_guard(monkeypatch):
    from scraper import catalog_worker

    assert set(catalog_worker.FORWARD_ONLY_SOURCES) == {"uzmovi", "asilmedia"}

    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("AUTO_CONTENT_ENABLED", "true")
    monkeypatch.setenv("SCRAPER_ENABLED", "true")
    monkeypatch.setenv("RENDER_CATALOG_DAILY_LIMIT", "4")
    monkeypatch.setenv("TELEGRAM_API_ID", "12345")
    monkeypatch.setenv("TELEGRAM_API_HASH", "hash123")
    monkeypatch.setenv("TELEGRAM_STRING_SESSION", "same_sess")
    monkeypatch.setenv("SMM_TELEGRAM_STRING_SESSION", "same_sess")

    # 1. Collision with SMM session refuses cleanly
    res_coll = await catalog_worker.run_catalog_worker_tick()
    assert res_coll["skipped"] == "session_collision"

    # 2. Separate session + daily cap reached skips cleanly without connecting Telethon
    monkeypatch.setenv("TELEGRAM_STRING_SESSION", "cat_sess")
    monkeypatch.setenv("SMM_TELEGRAM_STRING_SESSION", "smm_sess")
    with patch.object(catalog_worker, "_count_today_forward_published", new=AsyncMock(return_value=4)):
        res_cap = await catalog_worker.run_catalog_worker_tick()
    assert res_cap["skipped"] == "daily_limit"

    # 3. Under cap -> claims uzmovi/asilmedia item, runs copy_only=True, disconnects client
    fake_item = MagicMock(id="uzmovi_555", source="uzmovi", title="Test Kino")
    fake_qm = MagicMock()
    fake_qm.recover_stale_in_progress_async = AsyncMock(return_value=0)
    fake_qm.claim_next_async = AsyncMock(return_value=fake_item)

    fake_tg = AsyncMock()
    fake_tg.connect = AsyncMock()
    fake_tg.is_user_authorized = AsyncMock(return_value=True)
    fake_tg.disconnect = AsyncMock()

    fake_pipeline = MagicMock()
    fake_pipeline.run_item = AsyncMock(return_value=True)

    with (
        patch.object(catalog_worker, "_count_today_forward_published", new=AsyncMock(return_value=1)),
        patch.object(catalog_worker, "QueueManager", return_value=fake_qm),
        patch.object(catalog_worker, "_build_telethon_client", return_value=fake_tg),
        patch.object(catalog_worker, "TelethonModeratorPipeline", return_value=fake_pipeline) as mock_cls,
        patch("scraper.catalog_worker.DuplicateChecker") as mock_dup,
    ):
        mock_dup.return_value.refresh_cache = AsyncMock()
        res_ok = await catalog_worker.run_catalog_worker_tick()

    assert res_ok["processed"] == 1
    assert res_ok["source"] == "uzmovi"
    assert mock_cls.call_args.kwargs["copy_only"] is True
    fake_tg.disconnect.assert_awaited_once()

    monkeypatch.setenv("RENDER_CATALOG_ENABLED", "true")
    state = catalog_worker.get_catalog_worker_state()
    assert state["enabled"] is True
    assert state["has_catalog_session"] is True
    assert state["session_collision"] is False
    assert state["has_api_creds"] is True
