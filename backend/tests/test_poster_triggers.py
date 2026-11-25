"""Tests for Slice 3: automatic poster localization triggers on create/update/audit."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import BackgroundTasks


def test_should_localize_poster_rules():
    from app.api.v1.posters import should_localize_poster

    assert should_localize_poster(tmdb_id=None, poster_url=None) is False
    assert should_localize_poster(tmdb_id=0, poster_url="") is False
    assert should_localize_poster(
        tmdb_id=27205,
        poster_url="https://api.mediaplus.uz/api/v1/posters/tg/AgAC_ALREADY_DONE_123456",
    ) is False
    assert should_localize_poster(tmdb_id=27205, poster_url=None) is True
    assert should_localize_poster(tmdb_id=None, poster_url="https://image.tmdb.org/t/p/w500/abc.jpg") is True


@pytest.mark.asyncio
async def test_run_poster_localization_task_updates_movie_and_series():
    from app.api.v1.posters import run_poster_localization_task

    movie_obj = SimpleNamespace(
        id=10,
        title="Muqaddima",
        code="3958",
        tmdb_id=27205,
        poster_url="https://image.tmdb.org/t/p/w500/old.jpg",
        source_chat_id=-100111,
        source_topic_id=55,
    )
    series_obj = SimpleNamespace(
        id=20,
        title="Taxtlar o'yini",
        tmdb_id=1399,
        poster_url="https://image.tmdb.org/t/p/w500/old_s.jpg",
        source=SimpleNamespace(chat_id=-100222, topic_id=77),
    )

    for media_type, obj, expected_chat, expected_topic in [
        ("movie", movie_obj, -100111, 55),
        ("series", series_obj, -100222, 77),
    ]:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = obj
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_db)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("app.infrastructure.db.session.async_session_factory", return_value=mock_ctx),
            patch(
                "app.infrastructure.external.poster_localizer.localize_poster_and_upload",
                new=AsyncMock(return_value=f"https://api.example.com/api/v1/posters/tg/AgAC_{media_type}"),
            ) as mock_loc,
            patch("app.core.cache.delete_cache_pattern", new=AsyncMock()) as mock_del_cache,
        ):
            await run_poster_localization_task(media_type, obj.id, allow_in_testing=True)

        assert obj.poster_url == f"https://api.example.com/api/v1/posters/tg/AgAC_{media_type}"
        mock_loc.assert_awaited_once()
        assert mock_loc.call_args.kwargs["topic_chat_id"] == expected_chat
        assert mock_loc.call_args.kwargs["topic_id"] == expected_topic
        mock_db.commit.assert_awaited_once()
        mock_del_cache.assert_awaited()


def test_schedule_poster_localization_adds_background_task():
    from app.api.v1.posters import schedule_poster_localization, run_poster_localization_task

    bg = BackgroundTasks()
    schedule_poster_localization(bg, "movie", 42, tmdb_id=27205, poster_url=None)
    assert len(bg.tasks) == 1
    assert bg.tasks[0].func is run_poster_localization_task
    assert bg.tasks[0].args == ("movie", 42)

    bg_skip = BackgroundTasks()
    schedule_poster_localization(
        bg_skip,
        "movie",
        42,
        tmdb_id=27205,
        poster_url="https://api.example.com/api/v1/posters/tg/AgAC_ALREADY_DONE_123456",
    )
    assert len(bg_skip.tasks) == 0


@pytest.mark.asyncio
async def test_create_and_update_movie_series_trigger_poster_localization():
    from starlette.requests import Request as StarletteRequest
    from app.main import app
    from app.api.v1.movies import MovieUpdate, update_movie
    from app.api.v1.series import update_series
    from app.domain.series.entities import SeriesUpdate

    fake_req = StarletteRequest(
        {
            "type": "http",
            "method": "PUT",
            "path": "/api/v1/movies/11",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "query_string": b"",
            "app": app,
        }
    )
    bg_m = BackgroundTasks()
    mock_movie_service = MagicMock()
    mock_movie_service.update_movie = AsyncMock(
        return_value=SimpleNamespace(id=11, tmdb_id=27205, poster_url="https://image.tmdb.org/t/p/w500/m.jpg")
    )
    with (
        patch("app.api.v1.posters.schedule_poster_localization") as mock_sched_m,
        patch("app.api.v1.movies.delete_cache_pattern", new=AsyncMock()),
    ):
        await update_movie(
            request=fake_req,
            movie_id=11,
            movie_in=MovieUpdate(tmdb_id=27205),
            background_tasks=bg_m,
            service=mock_movie_service,
            db=AsyncMock(),
            admin={"id": 1},
        )
        mock_sched_m.assert_called_once()
        assert mock_sched_m.call_args.args[1:3] == ("movie", 11)

    bg_s = BackgroundTasks()
    mock_series_service = MagicMock()
    mock_series_service.update_series = AsyncMock(
        return_value=SimpleNamespace(id=22, tmdb_id=None, poster_url="https://example.com/manual.jpg")
    )
    with (
        patch("app.api.v1.posters.schedule_poster_localization") as mock_sched_s,
        patch("app.api.v1.series.delete_cache_pattern", new=AsyncMock()),
    ):
        await update_series(
            series_id=22,
            series_in=SeriesUpdate(poster_url="https://example.com/manual.jpg"),
            background_tasks=bg_s,
            service=mock_series_service,
            admin={"id": 1},
        )
        mock_sched_s.assert_called_once()
        assert mock_sched_s.call_args.args[1:3] == ("series", 22)

