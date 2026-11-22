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
