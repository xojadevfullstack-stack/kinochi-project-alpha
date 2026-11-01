import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.core.config import settings
import scraper.config as scraper_cfg
from scraper.queue_manager import QueueItem
from scraper.telethon_moderator_pipeline import TelethonModeratorPipeline


def test_uzmovi_bot_code_verified_defaults_false(monkeypatch):
    monkeypatch.delenv("UZMOVI_BOT_CODE_VERIFIED", raising=False)
    assert settings.UZMOVI_BOT_CODE_VERIFIED is False
    assert scraper_cfg.is_uzmovi_bot_code_verified() is False


@pytest.mark.asyncio
async def test_uzmovi_movie_unverified_sets_needs_review(monkeypatch):
    monkeypatch.setenv("UZMOVI_BOT_CODE_VERIFIED", "false")
    pipeline = object.__new__(TelethonModeratorPipeline)
    pipeline.client = AsyncMock()

    item = QueueItem(
        id="uzmovi_71550",
        source="uzmovi",
        source_id="71550",
        title="Qasoskorlar",
        year=2019,
        media_type="movie",
        url="https://uzmovi.net/71550-qasoskorlar.html",
    )

    with patch("scraper.telethon_moderator_pipeline.QueueManager") as mock_qm:
        msg = await pipeline._fetch_video(item, target_bot="UzmovieTV_Bot")
        assert msg is None
        assert item.status == "needs_review"
        assert item.reason == "uzmovi_code_unverified"
        mock_qm.return_value.update_status.assert_called_once_with(
            "uzmovi_71550", "needs_review", error_message="uzmovi_code_unverified"
        )
        pipeline.client.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_uzmovi_movie_verified_proceeds_to_bot(monkeypatch):
    monkeypatch.setenv("UZMOVI_BOT_CODE_VERIFIED", "true")
    pipeline = object.__new__(TelethonModeratorPipeline)
    pipeline.client = AsyncMock()
    pipeline.client.send_message = AsyncMock(return_value=SimpleNamespace(id=10))

    fake_video = SimpleNamespace(
        id=11,
        text="Qasoskorlar",
        file=SimpleNamespace(duration=5400, size=100 * 1024 * 1024, name="video.mp4"),
    )

    item = QueueItem(
        id="uzmovi_71550",
        source="uzmovi",
        source_id="71550",
        title="Qasoskorlar",
        year=2019,
        media_type="movie",
        url="https://uzmovi.net/71550-qasoskorlar.html",
    )

    with patch("scraper.telethon_moderator_pipeline.poll_new_messages", new=AsyncMock(return_value=[fake_video])), \
         patch("scraper.telethon_moderator_pipeline.QueueManager") as mock_qm:
        msg = await pipeline._fetch_video(item, target_bot="UzmovieTV_Bot")
        assert msg is fake_video
        pipeline.client.send_message.assert_called_once_with("UzmovieTV_Bot", "71550")
        mock_qm.return_value.update_status.assert_not_called()


@pytest.mark.asyncio
async def test_uzmovi_series_unverified_sets_needs_review(monkeypatch):
    monkeypatch.setenv("UZMOVI_BOT_CODE_VERIFIED", "false")
    pipeline = object.__new__(TelethonModeratorPipeline)
    pipeline.client = AsyncMock()
    pipeline.dup_checker = SimpleNamespace(
        check=AsyncMock(return_value=SimpleNamespace(match_type=None, is_duplicate=False))
    )

    item = QueueItem(
        id="uzmovi_9001",
        source="uzmovi",
        source_id="9001",
        title="Test Serial",
        year=2024,
        media_type="series",
        url="https://uzmovi.net/9001-test-serial.html",
    )

    with patch("scraper.telethon_moderator_pipeline.QueueManager") as mock_qm:
        ok = await pipeline.run_single_series(item, target_bot="UzmovieTV_Bot")
        assert ok is False
        assert item.status == "needs_review"
        assert item.reason == "uzmovi_code_unverified"
        mock_qm.return_value.update_status.assert_called_once_with(
            "uzmovi_9001", "needs_review", error_message="uzmovi_code_unverified"
        )
        pipeline.client.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_other_sources_unaffected_when_uzmovi_unverified(monkeypatch):
    monkeypatch.setenv("UZMOVI_BOT_CODE_VERIFIED", "false")
    pipeline = object.__new__(TelethonModeratorPipeline)
    pipeline.client = AsyncMock()
    fake_video = SimpleNamespace(id=22, text="Asilmedia video", file=SimpleNamespace(duration=3600))
    pipeline._fetch_asilmedia_video = AsyncMock(return_value=fake_video)

    asil_item = QueueItem(
        id="asilmedia_444",
        source="asilmedia",
        source_id="444",
        title="Asilmedia Kino",
        year=2024,
        media_type="movie",
        url="http://asilmedia.org/444-kino.html",
    )

    with patch("scraper.telethon_moderator_pipeline.QueueManager") as mock_qm:
        msg = await pipeline._fetch_video(asil_item, target_bot="asilmediabot")
        assert msg is fake_video
        pipeline._fetch_asilmedia_video.assert_called_once_with(query="444", year=2024)
        mock_qm.return_value.update_status.assert_not_called()
