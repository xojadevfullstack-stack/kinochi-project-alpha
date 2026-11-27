from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.smm import SmmClipJobModel, SmmSettingsModel
from app.infrastructure.db.models.translation import MovieTranslationModel
from scraper.smm_publishers.base import PublishResult
from scraper.smm_worker import (
    enqueue_smm_clip_job,
    is_schedule_due,
    maybe_enqueue_smm_for_movie,
    process_generating_job,
    process_publish_job,
    resolve_smm_session_string,
    run_smm_worker_cycle,
)


def test_is_schedule_due_respects_daily_limit_and_slots():
    now = datetime(2026, 11, 19, 12, 3, tzinfo=timezone.utc)
    assert is_schedule_due(["09:00", "12:00"], now, last_published_at=None, daily_count=1, daily_limit=6) is True
    assert is_schedule_due(["09:00", "12:00"], now, last_published_at=None, daily_count=6, daily_limit=6) is False
    same_hour = datetime(2026, 11, 19, 12, 1, tzinfo=timezone.utc)
    assert is_schedule_due(["09:00", "12:00"], now, last_published_at=same_hour, daily_count=1, daily_limit=6) is False


@pytest.mark.asyncio
async def test_enqueue_process_generating_and_publish_lifecycle(db_session, tmp_path):
    # Seed movie + translation + settings
    movie = MovieModel(title="Otamga qasida", code="99889", imdb_rating=8.4, genres="Drama")
    db_session.add(movie)
    await db_session.flush()
    db_session.add(MovieTranslationModel(movie_id=movie.id, language="O'zbek tilida", storage_channel_message_id=5064))
    cfg = SmmSettingsModel(id=1, mode="SEMI_AUTO", enabled_platforms=["telegram", "instagram"], telegram_channel_id="-100123")
    cfg = await db_session.merge(cfg)
    await db_session.commit()

    # 1. Enqueue
    job = await enqueue_smm_clip_job(db_session, movie_code="99889", title="Otamga qasida", media_id=movie.id)
    assert job.status == "generating"

    # 2. Generate clip -> SEMI_AUTO transitions to waiting_approval
    tg_client = AsyncMock()
    tg_client.get_messages = AsyncMock(return_value=MagicMock(id=5064))
    fake_clip_meta = {"output_path": str(tmp_path / f"clip_{job.id}.mp4"), "start_sec": 310.0, "duration_sec": 45.0, "blur_bottom_ad": False}
    (tmp_path / f"clip_{job.id}.mp4").write_bytes(b"rendered-mp4")

    with patch("scraper.smm_worker.create_smart_smm_clip", new=AsyncMock(return_value=fake_clip_meta)):
        updated = await process_generating_job(db_session, job, cfg, tg_client, storage_chat_id=-100999, uploads_dir=str(tmp_path))

    assert updated.status == "waiting_approval"
    assert updated.start_sec == 310.0
    assert updated.clip_path and f"clip_{job.id}.mp4" in updated.clip_path
    assert "889" in (updated.caption or "")

    # 3. Publish -> partial platform success still marks completed and records per-platform errors
    mock_disp = MagicMock()
    mock_disp.publish_all = AsyncMock(
        return_value={
            "telegram": PublishResult("telegram", True, post_id="44"),
            "instagram": PublishResult("instagram", False, error="No video_url"),
        }
    )
    published = await process_publish_job(db_session, updated, cfg, dispatcher=mock_disp)
    assert published.status == "completed"
    assert published.platforms_status["telegram"]["status"] == "published"
    assert published.platforms_status["instagram"]["status"] == "failed"

    saved = (await db_session.execute(select(SmmClipJobModel).where(SmmClipJobModel.id == job.id))).scalar_one()
    assert saved.status == "completed"


@pytest.mark.asyncio
async def test_maybe_enqueue_smm_for_movie_respects_env_guard_and_isolates_errors(db_session, monkeypatch):
    movie = MovieModel(title="Matritsa", code="777", imdb_rating=8.7, genres="Sci-Fi")
    db_session.add(movie)
    await db_session.flush()

    monkeypatch.delenv("SMM_AUTOPILOT_ENABLED", raising=False)
    assert await maybe_enqueue_smm_for_movie(db_session, movie_id=movie.id, movie_code="777", title="Matritsa") is None

    monkeypatch.setenv("SMM_AUTOPILOT_ENABLED", "true")
    job = await maybe_enqueue_smm_for_movie(db_session, movie_id=movie.id, movie_code="777", title="Matritsa")
    assert job is not None
    assert job.movie_code == "777"
    assert job.status == "generating"

    with patch("scraper.smm_worker.enqueue_smm_clip_job", side_effect=RuntimeError("db hiccup")):
        res = await maybe_enqueue_smm_for_movie(db_session, movie_id=movie.id, movie_code="778", title="FailSafe")
        assert res is None

    # Outer transaction still healthy and can commit cleanly
    await db_session.commit()
    persisted = (await db_session.execute(select(MovieModel).where(MovieModel.code == "777"))).scalar_one()
    assert persisted.id == movie.id


def test_resolve_smm_session_string_avoids_sharing_scraper_session(monkeypatch):
    monkeypatch.setenv("TELEGRAM_STRING_SESSION", "shared_scraper_sess")
    monkeypatch.delenv("SMM_TELEGRAM_STRING_SESSION", raising=False)
    monkeypatch.delenv("SMM_ALLOW_SHARED_SESSION", raising=False)
    assert resolve_smm_session_string() == ""

    monkeypatch.setenv("SMM_TELEGRAM_STRING_SESSION", "dedicated_smm_sess")
    assert resolve_smm_session_string() == "dedicated_smm_sess"

    monkeypatch.delenv("SMM_TELEGRAM_STRING_SESSION", raising=False)
    monkeypatch.setenv("SMM_ALLOW_SHARED_SESSION", "true")
    assert resolve_smm_session_string() == "shared_scraper_sess"


@pytest.mark.asyncio
async def test_run_smm_worker_cycle_skips_when_disabled(monkeypatch):
    monkeypatch.delenv("SMM_AUTOPILOT_ENABLED", raising=False)
    res = await run_smm_worker_cycle(tg_client=None)
    assert res == {"generated": 0, "published": 0, "skipped": True}


@pytest.mark.asyncio
async def test_smm_worker_prefers_movie_short_code_and_mediaplus_bot(db_session, tmp_path):
    movie = MovieModel(
        title="Qisqa Kodli Film",
        code="QSKD99",
        short_code="1042",
        imdb_rating=8.1,
        genres="Jangari",
    )
    db_session.add(movie)
    await db_session.flush()
    db_session.add(MovieTranslationModel(movie_id=movie.id, language="O'zbekcha", storage_channel_message_id=7771))
    cfg = SmmSettingsModel(
        id=1,
        mode="SEMI_AUTO",
        enabled_platforms=["telegram", "youtube"],
        bot_username="@MediaPlusOfficialBot",
        telegram_channel_id="-100999",
    )
    cfg = await db_session.merge(cfg)
    await db_session.commit()

    job = await enqueue_smm_clip_job(db_session, movie_code="QSKD99", title="Qisqa Kodli Film", media_id=movie.id)
    tg_client = AsyncMock()
    tg_client.get_messages = AsyncMock(return_value=MagicMock(id=7771))
    fake_clip = {"output_path": str(tmp_path / f"clip_{job.id}.mp4"), "start_sec": 100.0, "duration_sec": 45.0, "blur_bottom_ad": False}
    (tmp_path / f"clip_{job.id}.mp4").write_bytes(b"mp4")

    with patch("scraper.smm_worker.create_smart_smm_clip", new=AsyncMock(return_value=fake_clip)) as mock_clip:
        updated = await process_generating_job(db_session, job, cfg, tg_client, storage_chat_id=-100999, uploads_dir=str(tmp_path))

    assert mock_clip.await_args.kwargs["movie_code"] == "1042"
    assert mock_clip.await_args.kwargs["bot_username"] == "@MediaPlusOfficialBot"
    assert "#1042" in (updated.caption or "")
    assert "@MediaPlusOfficialBot" in (updated.caption or "")

    mock_disp = MagicMock()
    mock_disp.publish_all = AsyncMock(
        return_value={"telegram": PublishResult("telegram", True, post_id="1")}
    )
    await process_publish_job(db_session, updated, cfg, dispatcher=mock_disp)
    assert mock_disp.publish_all.await_args.kwargs["movie_code"] == "1042"


@pytest.mark.asyncio
async def test_smm_worker_supports_episode_short_code_and_storage_video(db_session, tmp_path):
    from app.infrastructure.db.models.series import EpisodeModel, SeasonModel, SeriesModel
    from app.infrastructure.db.models.translation import EpisodeTranslationModel

    ser = SeriesModel(title="Taxtlar Oyini", imdb_rating=9.2, publish_status="published")
    db_session.add(ser)
    await db_session.flush()
    seas = SeasonModel(series_id=ser.id, season_number=2)
    db_session.add(seas)
    await db_session.flush()
    ep = EpisodeModel(
        season_id=seas.id,
        episode_number=5,
        code="EpAbCd12",
        short_code="1091",
        display_code="S2-CH5",
        title="5-qism",
    )
    db_session.add(ep)
    await db_session.flush()
    db_session.add(EpisodeTranslationModel(episode_id=ep.id, language="O'zbekcha", storage_channel_message_id=8882))
    cfg = SmmSettingsModel(
        id=1,
        mode="SEMI_AUTO",
        enabled_platforms=["telegram"],
        bot_username="@MediaPlusOfficialBot",
        telegram_channel_id="-100999",
    )
    cfg = await db_session.merge(cfg)
    await db_session.commit()

    job = await enqueue_smm_clip_job(
        db_session,
        movie_code="EpAbCd12",
        title="Taxtlar Oyini 2x5",
        media_id=ep.id,
        media_type="episode",
    )
    tg_client = AsyncMock()
    tg_client.get_messages = AsyncMock(return_value=MagicMock(id=8882))
    fake_clip = {"output_path": str(tmp_path / f"clip_{job.id}.mp4"), "start_sec": 42.0, "duration_sec": 45.0, "blur_bottom_ad": False}
    (tmp_path / f"clip_{job.id}.mp4").write_bytes(b"mp4")

    with patch("scraper.smm_worker.create_smart_smm_clip", new=AsyncMock(return_value=fake_clip)) as mock_clip:
        updated = await process_generating_job(db_session, job, cfg, tg_client, storage_chat_id=-100999, uploads_dir=str(tmp_path))

    assert updated.status == "waiting_approval"
    assert mock_clip.await_args.kwargs["movie_code"] == "1091"
    assert mock_clip.await_args.kwargs["imdb_rating"] == 9.2
    assert "#1091" in (updated.caption or "")

    mock_disp = MagicMock()
    mock_disp.publish_all = AsyncMock(return_value={"telegram": PublishResult("telegram", True, post_id="2")})
    await process_publish_job(db_session, updated, cfg, dispatcher=mock_disp)
    assert mock_disp.publish_all.await_args.kwargs["movie_code"] == "1091"


@pytest.mark.asyncio
async def test_supervised_smm_worker_logs_status_and_survives_connect_timeout(monkeypatch, caplog):
    import asyncio
    from scraper.smm_worker import supervised_run_smm_worker

    monkeypatch.setenv("SMM_AUTOPILOT_ENABLED", "true")
    monkeypatch.setenv("SMM_TELEGRAM_STRING_SESSION", "sess_test_123")
    monkeypatch.setenv("TELEGRAM_API_ID", "12345")
    monkeypatch.setenv("TELEGRAM_API_HASH", "hash_abc")

    fake_tg = MagicMock()
    fake_tg.connect = AsyncMock(side_effect=asyncio.TimeoutError("connect timed out"))
    mock_cycle = AsyncMock(return_value={"generated": 0, "published": 0})

    with (
        caplog.at_level("INFO", logger="scraper.smm_worker"),
        patch("telethon.TelegramClient", return_value=fake_tg),
        patch("telethon.sessions.StringSession", return_value="str_sess"),
        patch("scraper.smm_worker.run_smm_worker_cycle", mock_cycle),
        patch("scraper.smm_worker.asyncio.sleep", new=AsyncMock(side_effect=asyncio.CancelledError)),
    ):
        with pytest.raises(asyncio.CancelledError):
            await supervised_run_smm_worker()

    mock_cycle.assert_awaited_once_with(tg_client=None)
    assert any("SMM worker" in rec.message for rec in caplog.records)


@pytest.mark.asyncio
async def test_process_generating_job_marks_failed_instead_of_poison_queue(db_session, tmp_path):
    from sqlalchemy import delete
    from scraper.smm_worker import run_smm_worker_tick

    await db_session.execute(delete(SmmClipJobModel).where(SmmClipJobModel.status == "generating"))
    movie = MovieModel(title="Ouk Strit", code="WPZ79R", short_code="3956", imdb_rating=7.0)
    db_session.add(movie)
    await db_session.flush()
    db_session.add(MovieTranslationModel(movie_id=movie.id, language="O'zbekcha", storage_channel_message_id=9811))
    cfg = SmmSettingsModel(id=1, mode="SEMI_AUTO", enabled_platforms=["telegram"], telegram_channel_id="-100123")
    cfg = await db_session.merge(cfg)
    await db_session.commit()

    job = await enqueue_smm_clip_job(db_session, movie_code="WPZ79R", title="Ouk Strit", media_id=movie.id)
    tg_client = AsyncMock()
    tg_client.get_messages = AsyncMock(return_value=MagicMock(id=9811))

    with patch("scraper.smm_worker.create_smart_smm_clip", new=AsyncMock(side_effect=RuntimeError("FFmpeg render failed"))):
        tick_res = await run_smm_worker_tick(db_session, tg_client=tg_client, storage_chat_id=-100999)

    await db_session.refresh(job)
    assert job.status == "failed"
    assert tick_res["generated"] == 0


@pytest.mark.asyncio
async def test_process_generating_job_sends_admin_preview_in_both_modes(db_session, tmp_path):
    movie = MovieModel(title="Preview Kino", code="PRV1", short_code="3959", imdb_rating=8.2)
    db_session.add(movie)
    await db_session.flush()
    db_session.add(MovieTranslationModel(movie_id=movie.id, language="O'zbekcha", storage_channel_message_id=9820))
    cfg = SmmSettingsModel(
        id=1,
        mode="SEMI_AUTO",
        enabled_platforms=["telegram"],
        telegram_channel_id="-100123",
        admin_telegram_id="777888999",
    )
    cfg = await db_session.merge(cfg)
    await db_session.commit()

    job = await enqueue_smm_clip_job(db_session, movie_code="PRV1", title="Preview Kino", media_id=movie.id)
    tg_client = AsyncMock()
    tg_client.get_messages = AsyncMock(return_value=MagicMock(id=9820))
    fake_meta = {"output_path": str(tmp_path / f"clip_{job.id}.mp4"), "start_sec": 200.0, "duration_sec": 45.0}
    (tmp_path / f"clip_{job.id}.mp4").write_bytes(b"mp4")

    with (
        patch("scraper.smm_worker.create_smart_smm_clip", new=AsyncMock(return_value=fake_meta)),
        patch("scraper.smm_worker.send_admin_smm_preview", new=AsyncMock(return_value=True)) as mock_preview,
    ):
        res_semi = await process_generating_job(db_session, job, cfg, tg_client, storage_chat_id=-100999, uploads_dir=str(tmp_path))
        assert res_semi.progress_pct == 100
        assert mock_preview.await_args.kwargs["mode"] == "SEMI_AUTO"
        assert mock_preview.await_args.kwargs["admin_telegram_id"] == "777888999"

        cfg.mode = "FULL_AUTO"
        res_semi.status = "generating"
        await process_generating_job(db_session, res_semi, cfg, tg_client, storage_chat_id=-100999, uploads_dir=str(tmp_path))
        assert mock_preview.await_args.kwargs["mode"] == "FULL_AUTO"


@pytest.mark.asyncio
async def test_process_generating_job_persists_clip_storage_message_id(db_session, tmp_path, monkeypatch):
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    movie = MovieModel(title="Storage Backup Kino", code="STRG1", short_code="3962", imdb_rating=8.0)
    db_session.add(movie)
    await db_session.flush()
    db_session.add(MovieTranslationModel(movie_id=movie.id, language="O'zbekcha", storage_channel_message_id=9850))
    cfg = SmmSettingsModel(id=1, mode="SEMI_AUTO", enabled_platforms=["telegram"])
    cfg = await db_session.merge(cfg)
    await db_session.commit()

    job = await enqueue_smm_clip_job(db_session, movie_code="STRG1", title="Storage Backup Kino", media_id=movie.id)
    tg_client = AsyncMock()
    tg_client.get_messages = AsyncMock(return_value=MagicMock(id=9850))
    tg_client.send_file = AsyncMock(return_value=MagicMock(id=9991))
    fake_meta = {"output_path": str(tmp_path / f"clip_{job.id}.mp4"), "start_sec": 100.0, "duration_sec": 45.0}
    (tmp_path / f"clip_{job.id}.mp4").write_bytes(b"mp4-content")

    with (
        patch("scraper.smm_worker.create_smart_smm_clip", new=AsyncMock(return_value=fake_meta)),
        patch("scraper.smm_worker.send_admin_smm_preview", new=AsyncMock(return_value=False)),
    ):
        updated = await process_generating_job(db_session, job, cfg, tg_client, storage_chat_id=-100999, uploads_dir=str(tmp_path))

    assert updated.clip_storage_message_id == 9991
    tg_client.send_file.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_publish_job_uses_api_video_url_and_restores_missing_file(db_session, tmp_path):
    movie = MovieModel(title="Restore Pub Kino", code="RPB1", short_code="3963", imdb_rating=8.3)
    db_session.add(movie)
    await db_session.flush()
    cfg = SmmSettingsModel(id=1, mode="FULL_AUTO", enabled_platforms=["telegram"], telegram_channel_id="-100123")
    cfg = await db_session.merge(cfg)

    missing_path = str(tmp_path / "clip_restore.mp4")
    job = SmmClipJobModel(
        media_type="movie",
        media_id=movie.id,
        movie_code="RPB1",
        title="Restore Pub Kino",
        clip_path=missing_path,
        clip_storage_message_id=5067,
        caption="Test",
        status="publishing",
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    async def fake_download(msg, file):
        with open(file, "wb") as f:
            f.write(b"restored-mp4")
        return file

    tg_client = AsyncMock()
    tg_client.get_messages = AsyncMock(return_value=MagicMock(id=5067, media=MagicMock()))
    tg_client.download_media = AsyncMock(side_effect=fake_download)

    mock_disp = MagicMock()
    mock_disp.publish_all = AsyncMock(return_value={"telegram": PublishResult("telegram", True, post_id="77")})
    res = await process_publish_job(
        db_session,
        job,
        cfg,
        dispatcher=mock_disp,
        base_public_url="https://api.example.com",
        tg_client=tg_client,
        storage_chat_id=-100999,
    )

    assert res.status == "completed"
    assert mock_disp.publish_all.await_args.kwargs["video_url"] == f"https://api.example.com/api/v1/smm/jobs/{job.id}/video"
    tg_client.download_media.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_publish_job_skips_already_published_platforms(db_session, tmp_path):
    movie = MovieModel(title="Retry Failed Only", code="RTF1", short_code="3964", imdb_rating=8.1)
    db_session.add(movie)
    await db_session.flush()
    cfg = SmmSettingsModel(
        id=1,
        mode="SEMI_AUTO",
        enabled_platforms=["telegram", "youtube", "tiktok"],
        telegram_channel_id="-100123",
    )
    cfg = await db_session.merge(cfg)

    vid = tmp_path / "clip_retry.mp4"
    vid.write_bytes(b"mp4")
    job = SmmClipJobModel(
        media_type="movie",
        media_id=movie.id,
        movie_code="RTF1",
        title="Retry Failed Only",
        clip_path=str(vid),
        caption="Test",
        status="publishing",
        platforms_status={
            "telegram": {"enabled": True, "status": "published", "post_id": "3", "error": None},
            "youtube": {"enabled": True, "status": "published", "post_id": "yt_1", "error": None},
            "tiktok": {"enabled": True, "status": "failed", "post_id": None, "error": "ConnectError"},
        },
    )
    db_session.add(job)
    await db_session.commit()

    mock_disp = MagicMock()
    mock_disp.publish_all = AsyncMock(return_value={"tiktok": PublishResult("tiktok", True, post_id="tk_99")})
    res = await process_publish_job(db_session, job, cfg, dispatcher=mock_disp)

    assert list(mock_disp.publish_all.await_args.kwargs["platforms"]) == ["tiktok"]
    assert res.status == "completed"
    assert res.platforms_status["telegram"]["post_id"] == "3"
    assert res.platforms_status["youtube"]["post_id"] == "yt_1"
    assert res.platforms_status["tiktok"]["post_id"] == "tk_99"


def test_smm_worker_imports_gracefully_when_cv2_missing(monkeypatch):
    import importlib
    import sys

    monkeypatch.setitem(sys.modules, "cv2", None)
    for mod in ("scraper.video_verifier", "scraper.smm_scene_scorer", "scraper.smm_pipeline", "scraper.smm_worker"):
        sys.modules.pop(mod, None)
    worker_mod = importlib.import_module("scraper.smm_worker")
    assert hasattr(worker_mod, "get_smm_worker_state")
    assert hasattr(worker_mod, "process_publish_job")
    state = worker_mod.get_smm_worker_state()
    assert "started_at" in state
    assert "last_tick_at" in state


@pytest.mark.asyncio
async def test_supervised_run_smm_worker_waits_startup_delay_before_first_tick(monkeypatch):
    import asyncio
    from scraper import smm_worker

    events = []
    monkeypatch.setenv("SMM_AUTOPILOT_ENABLED", "true")
    monkeypatch.setenv("SMM_STARTUP_DELAY_SEC", "25")
    monkeypatch.setenv("SMM_WORKER_INTERVAL_SEC", "180")
    monkeypatch.setattr(smm_worker, "resolve_smm_session_string", lambda: "")

    async def _fake_sleep(secs):
        events.append(("sleep", secs))
        if len([e for e in events if e[0] == "cycle"]) >= 1:
            raise asyncio.CancelledError()

    async def _fake_cycle(**kwargs):
        events.append(("cycle", kwargs))
        return {"generated": 0, "published": 0}

    monkeypatch.setattr(smm_worker.asyncio, "sleep", _fake_sleep)
    monkeypatch.setattr(smm_worker, "run_smm_worker_cycle", _fake_cycle)

    with pytest.raises(asyncio.CancelledError):
        await smm_worker.supervised_run_smm_worker()

    assert events[0] == ("sleep", 25)
    assert events[1][0] == "cycle"


def test_compute_worker_sleep_seconds_fast_chains_when_generated():
    from scraper.smm_worker import compute_worker_sleep_seconds

    assert compute_worker_sleep_seconds(180, {"generated": 1, "published": 0}) == 10
    assert compute_worker_sleep_seconds(180, {"generated": 0, "published": 0}) == 180
    assert compute_worker_sleep_seconds(5, {"generated": 1, "published": 0}) == 5



def test_is_schedule_due_enforces_monthly_limit_and_tashkent_tz():
    from datetime import timedelta

    tashkent = timezone(timedelta(hours=5))
    now_local = datetime(2026, 11, 26, 11, 15, tzinfo=tashkent)
    # 06:05 UTC is 11:05 Tashkent (same local hour)
    last_utc = datetime(2026, 11, 26, 6, 5, tzinfo=timezone.utc)
    assert is_schedule_due(["11:00", "16:00"], now_local, last_published_at=last_utc, daily_count=0, daily_limit=3, monthly_count=10, monthly_limit=90) is False
    # Monthly quota reached blocks publishing even when daily_count < daily_limit
    assert is_schedule_due(["11:00", "16:00"], now_local, last_published_at=None, daily_count=0, daily_limit=3, monthly_count=90, monthly_limit=90) is False
    # Allowed when under both daily and monthly limit
    assert is_schedule_due(["11:00", "16:00"], now_local, last_published_at=None, daily_count=1, daily_limit=3, monthly_count=89, monthly_limit=90) is True


@pytest.mark.asyncio
async def test_auto_pick_catalog_movie_selects_unused_published_movie_with_storage(db_session):
    from scraper.smm_worker import auto_pick_catalog_movie

    m_draft = MovieModel(title="Draft Kino", code="DRF1", short_code="9001", publish_status="pending")
    m_used = MovieModel(title="Eski Kesilgan", code="USD2", short_code="9002", publish_status="published")
    m_fresh = MovieModel(title="Yangi Tanlov", code="FRSH3", short_code="9003", publish_status="published")
    db_session.add_all([m_draft, m_used, m_fresh])
    await db_session.flush()
    db_session.add_all([
        MovieTranslationModel(movie_id=m_draft.id, language="O'zbekcha", storage_channel_message_id=101),
        MovieTranslationModel(movie_id=m_used.id, language="O'zbekcha", storage_channel_message_id=102),
        MovieTranslationModel(movie_id=m_fresh.id, language="O'zbekcha", storage_channel_message_id=103),
    ])
    await db_session.merge(
        SmmSettingsModel(id=1, mode="FULL_AUTO", daily_limit=3, auto_pick_from_catalog=True, enabled_platforms=["telegram"])
    )
    db_session.add(
        SmmClipJobModel(media_type="movie", media_id=m_used.id, movie_code="9002", title="Eski Kesilgan", status="completed")
    )
    await db_session.commit()

    picked_job = await auto_pick_catalog_movie(db_session)
    assert picked_job is not None
    assert picked_job.media_id == m_fresh.id
    assert picked_job.movie_code == "9003"
    assert picked_job.status == "generating"


@pytest.mark.asyncio
async def test_run_smm_worker_tick_triggers_auto_pick_and_respects_monthly_cap(db_session, tmp_path, monkeypatch):
    from sqlalchemy import delete
    from scraper import smm_worker

    await db_session.execute(delete(SmmClipJobModel))
    movie = MovieModel(title="Avto Film", code="AVT1", short_code="9101", publish_status="published")
    db_session.add(movie)
    await db_session.flush()
    db_session.add(MovieTranslationModel(movie_id=movie.id, language="O'zbekcha", storage_channel_message_id=202))
    await db_session.merge(
        SmmSettingsModel(
            id=1,
            mode="FULL_AUTO",
            daily_limit=3,
            schedule_hours=["11:00", "16:00", "21:00"],
            auto_pick_from_catalog=True,
            enabled_platforms=["telegram"],
        )
    )
    await db_session.commit()

    tg_client = AsyncMock()
    tg_client.get_messages = AsyncMock(return_value=MagicMock(id=202))

    monkeypatch.setenv("SMM_MONTHLY_LIMIT", "1")
    # Seed 1 completed job in current month -> monthly cap reached -> no auto-pick or publish
    db_session.add(
        SmmClipJobModel(
            media_type="movie",
            media_id=None,
            movie_code="OLD01",
            title="Old Completed",
            status="completed",
            updated_at=datetime.now(timezone.utc),
        )
    )
    await db_session.commit()
    res_capped = await smm_worker.run_smm_worker_tick(db_session, tg_client=tg_client, storage_chat_id=-1001)
    assert res_capped == {"generated": 0, "published": 0}

    # Increase monthly limit -> auto_pick creates and generates Avto Film job
    monkeypatch.setenv("SMM_MONTHLY_LIMIT", "90")
    fake_clip = {"output_path": str(tmp_path / "clip.mp4"), "start_sec": 50.0, "duration_sec": 45.0}
    with patch("scraper.smm_worker.create_smart_smm_clip", new=AsyncMock(return_value=fake_clip)):
        res_ok = await smm_worker.run_smm_worker_tick(db_session, tg_client=tg_client, storage_chat_id=-1001)
    assert res_ok["generated"] == 1


@pytest.mark.asyncio
async def test_auto_pick_catalog_movie_prioritizes_gems_and_skips_low_rated_old_movies(db_session):
    from sqlalchemy import delete
    from scraper.smm_worker import auto_pick_catalog_movie

    await db_session.execute(delete(SmmClipJobModel))
    await db_session.execute(delete(MovieTranslationModel))
    await db_session.execute(delete(MovieModel))

    m_mid = MovieModel(title="Mid Film", code="MID1", short_code="9201", release_year=2015, imdb_rating=6.4, publish_status="published")
    m_gem = MovieModel(title="Interstellar Hit", code="GEM1", short_code="9202", release_year=2014, imdb_rating=8.6, view_count=5, publish_status="published")
    m_boring_newest = MovieModel(title="Zerikarli Flop", code="BRG1", short_code="9203", release_year=1990, imdb_rating=4.7, publish_status="published")
    db_session.add_all([m_mid, m_gem, m_boring_newest])
    await db_session.flush()
    db_session.add_all([
        MovieTranslationModel(movie_id=m_mid.id, language="O'zbekcha", storage_channel_message_id=301),
        MovieTranslationModel(movie_id=m_gem.id, language="O'zbekcha", storage_channel_message_id=302),
        MovieTranslationModel(movie_id=m_boring_newest.id, language="O'zbekcha", storage_channel_message_id=303),
    ])
    await db_session.merge(
        SmmSettingsModel(id=1, mode="FULL_AUTO", daily_limit=3, auto_pick_from_catalog=True, enabled_platforms=["telegram"])
    )
    await db_session.commit()

    # Must pick IMDb 8.6 gem even though boring 4.7 movie has newer id
    j1 = await auto_pick_catalog_movie(db_session)
    assert j1 is not None and j1.movie_code == "9202"
    j2 = await auto_pick_catalog_movie(db_session)
    assert j2 is not None and j2.movie_code == "9201"
    # Boring old 4.7 movie must be skipped instead of wasting quota
    j3 = await auto_pick_catalog_movie(db_session)
    assert j3 is None


@pytest.mark.asyncio
async def test_auto_pick_catalog_movie_boosts_high_retention_genres(db_session):
    from sqlalchemy import delete
    from scraper.smm_worker import auto_pick_catalog_movie

    await db_session.execute(delete(SmmClipJobModel))
    await db_session.execute(delete(MovieTranslationModel))
    await db_session.execute(delete(MovieModel))

    m_drama = MovieModel(
        title="Sokin Drama",
        code="DRM1",
        short_code="9301",
        release_year=2024,
        imdb_rating=7.2,
        genres="Drama, Melodrama",
        publish_status="published",
    )
    m_thriller = MovieModel(
        title="Tezkor Triller",
        code="THR1",
        short_code="9302",
        release_year=2024,
        imdb_rating=7.0,
        genres="Triller, Jangari, Fantastika",
        publish_status="published",
    )
    db_session.add_all([m_drama, m_thriller])
    await db_session.flush()
    db_session.add_all([
        MovieTranslationModel(movie_id=m_drama.id, language="O'zbekcha", storage_channel_message_id=401),
        MovieTranslationModel(movie_id=m_thriller.id, language="O'zbekcha", storage_channel_message_id=402),
    ])
    await db_session.merge(
        SmmSettingsModel(id=1, mode="FULL_AUTO", daily_limit=3, auto_pick_from_catalog=True, enabled_platforms=["telegram"])
    )
    await db_session.commit()

    picked = await auto_pick_catalog_movie(db_session)
    assert picked is not None
    assert picked.movie_code == "9302"
    assert picked.clip_mode == "scene"


@pytest.mark.asyncio
async def test_resolve_media_poster_url_localizes_unlocalized_poster_before_cover(db_session):
    from scraper.smm_worker import _resolve_media_poster_url

    movie = MovieModel(
        title="Qasoskorlar 4 Intiho",
        code="AV4",
        short_code="9401",
        tmdb_id=299534,
        poster_url="https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg",
        publish_status="published",
    )
    db_session.add(movie)
    await db_session.flush()
    job = SmmClipJobModel(movie_code="9401", title="Qasoskorlar 4 Intiho", media_type="movie", media_id=movie.id, status="generating")
    db_session.add(job)
    await db_session.commit()

    localized_url = "https://kinochi-project-alpha-9g6j.onrender.com/api/v1/posters/tg/AgAC_LOCALIZED_AV4"
    with patch(
        "app.infrastructure.external.poster_localizer.localize_poster_and_upload",
        new=AsyncMock(return_value=localized_url),
    ) as mock_loc:
        resolved = await _resolve_media_poster_url(db_session, job)

    assert resolved == localized_url
    assert movie.poster_url == localized_url
    mock_loc.assert_awaited_once()


@pytest.mark.asyncio
async def test_auto_pick_catalog_movie_selects_weekly_rubric_in_prime_slot(db_session):
    from datetime import timedelta
    from scraper.smm_worker import auto_pick_catalog_movie

    tashkent = timezone(timedelta(hours=5))
    movie = MovieModel(
        title="Muqaddima",
        code="INC1",
        short_code="1012",
        release_year=2010,
        imdb_rating=8.4,
        tmdb_id=27205,
        genres="Triller",
        publish_status="published",
    )
    db_session.add(movie)
    await db_session.flush()
    db_session.add(MovieTranslationModel(movie_id=movie.id, language="O'zbekcha", storage_channel_message_id=501))
    await db_session.merge(SmmSettingsModel(id=1, mode="FULL_AUTO", daily_limit=3, auto_pick_from_catalog=True, enabled_platforms=["telegram"]))
    await db_session.flush()

    # Monday 21:05 Tashkent prime slot -> selects 'tavsiya'
    mon_prime = datetime(2026, 11, 23, 21, 5, tzinfo=tashkent)
    picked = await auto_pick_catalog_movie(db_session, now_local=mon_prime)
    assert picked is not None
    assert picked.movie_code == "1012"
    assert picked.clip_mode == "tavsiya"


@pytest.mark.asyncio
async def test_process_generating_job_routes_rubric_to_golden_standard_engine(db_session, tmp_path):
    from pathlib import Path
    from scraper.smm_worker import process_generating_job as run_gen_job

    movie = MovieModel(
        title="Yulduzlar sari",
        code="AST1",
        short_code="3955",
        release_year=2026,
        imdb_rating=8.1,
        tmdb_id=1359005,
        description="Kosmik kema tush tizimi ishdan chiqadi.",
        genres="Fantastika",
        publish_status="published",
    )
    db_session.add(movie)
    await db_session.flush()
    db_session.add(MovieTranslationModel(movie_id=movie.id, language="O'zbek tilida", storage_channel_message_id=601))
    cfg = await db_session.merge(SmmSettingsModel(id=1, mode="FULL_AUTO", enabled_platforms=["telegram"], telegram_channel_id="-100123"))
    job = SmmClipJobModel(movie_code="3955", title="Yulduzlar sari", media_type="movie", media_id=movie.id, clip_mode="yangiliklar", status="generating")
    db_session.add(job)
    await db_session.flush()

    tg_client = AsyncMock()
    tg_client.get_messages = AsyncMock(return_value=MagicMock(id=601))
    out_file = tmp_path / f"clip_{job.id}.mp4"

    async def _fake_sparse(client, msg, chunk_path, **kwargs):
        Path(chunk_path).write_bytes(b"fake-chunk")
        return chunk_path, 1800.0

    async def _fake_rubric(**kwargs):
        Path(kwargs["output_path"]).write_bytes(b"rubric-mp4")
        return {"output_path": kwargs["output_path"], "rubric": "yangiliklar", "hook_text": "2026 PREMYERASI", "duration_sec": 28.0, "narration_end": 21.5}

    with (
        patch("scraper.smm_worker.download_sparse_clip_source", new=AsyncMock(side_effect=_fake_sparse)),
        patch("scraper.smm_worker.create_rubric_smm_clip", new=AsyncMock(side_effect=_fake_rubric)) as mock_rubric,
        patch("scraper.smm_worker._resolve_media_poster_url", new=AsyncMock(return_value=None)),
        patch("scraper.smm_worker._post_telegram_video", new=AsyncMock(return_value=(True, "777", None))),
    ):
        updated = await run_gen_job(db_session, job, cfg, tg_client, storage_chat_id=-100999, uploads_dir=str(tmp_path))

    assert out_file.exists()
    assert updated.status == "scheduled"
    assert updated.hook_text == "2026 PREMYERASI"
    assert updated.clip_mode == "yangiliklar"
    mock_rubric.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_smm_worker_tick_prioritizes_rubrics_and_publishes_due_scheduled_at(db_session):
    from datetime import timedelta
    from sqlalchemy import delete
    from scraper.smm_worker import run_smm_worker_tick as run_tick

    await db_session.execute(delete(SmmClipJobModel))
    await db_session.merge(
        SmmSettingsModel(
            id=1,
            mode="FULL_AUTO",
            daily_limit=1,
            schedule_hours=["21:00"],
            auto_pick_from_catalog=False,
            enabled_platforms=["telegram"],
            telegram_channel_id="-100123",
        )
    )
    scene_job = SmmClipJobModel(movie_code="1014", title="Old scene", clip_mode="scene", status="generating")
    rubric_job = SmmClipJobModel(movie_code="3968", title="Spider", clip_mode="yangiliklar", status="generating")
    due_pub = SmmClipJobModel(
        movie_code="3955",
        title="Due Rubric",
        clip_mode="tavsiya",
        status="scheduled",
        scheduled_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    db_session.add_all([scene_job, rubric_job, due_pub])
    await db_session.flush()

    picked_gen_ids = []
    picked_pub_ids = []

    async def _fake_gen(db, job, cfg, tg_client, storage_chat_id):
        picked_gen_ids.append(job.id)
        job.status = "scheduled"
        return job

    async def _fake_pub(db, job, cfg, **kwargs):
        picked_pub_ids.append(job.id)
        job.status = "completed"
        return job

    with (
        patch("scraper.smm_worker.process_generating_job", side_effect=_fake_gen),
        patch("scraper.smm_worker.process_publish_job", side_effect=_fake_pub),
    ):
        res = await run_tick(db_session, tg_client=MagicMock(), storage_chat_id=-100999)

    assert picked_gen_ids == [rubric_job.id]
    assert picked_pub_ids == [due_pub.id]
    assert res == {"generated": 1, "published": 1}




