import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


@pytest.mark.asyncio
async def test_pipeline_pre_check_called_before_create():
    """F-002 regression test: telethon_moderator_pipeline must invoke pre_check before creating media."""
    import scraper.telethon_moderator_pipeline as tmp_module
    from scraper.telethon_moderator_pipeline import TelethonModeratorPipeline

    # Check that pre_check is imported in scraper.telethon_moderator_pipeline
    assert hasattr(tmp_module, "pre_check"), "pre_check must be imported and exposed in telethon_moderator_pipeline"

    # Mock client and duplicate checker
    mock_client = AsyncMock()
    mock_dup = AsyncMock()
    mock_dup.check.return_value = MagicMock(match_type=None)

    pipeline = TelethonModeratorPipeline(client=mock_client, duplicate_checker=mock_dup)

    # Mock queue item
    mock_item = MagicMock()
    mock_item.id = 123
    mock_item.title = "Test Serial"
    mock_item.year = 2024
    mock_item.source = "asilmedia"
    mock_item.original_title = "Test Serial Original"
    mock_item.url = "https://asilmedia.org/test"
    mock_item.code = "test_code"

    mock_session = AsyncMock()
    mock_session.get.return_value = None

    with patch.object(tmp_module, "pre_check", new_callable=AsyncMock) as mock_pre, \
         patch.object(tmp_module, "record_rejection", new_callable=AsyncMock) as mock_rej, \
         patch("scraper.telethon_moderator_pipeline.async_session_factory") as mock_factory, \
         patch("scraper.telethon_moderator_pipeline.QueueManager") as mock_qm:

        mock_factory.return_value.__aenter__.return_value = mock_session
        # Simulate pre_check returning invalid
        mock_pre.return_value = (False, [{"field": "title", "code": "invalid_title", "message": "Xato nom"}])

        with patch("app.application.series.series_service.SeriesService.create_series") as mock_create_series:
            # Call run_single_series with patched search/topic methods to reach creation
            with patch.object(pipeline, "_create_topic", new_callable=AsyncMock, return_value=777), \
                 patch.object(pipeline, "safe_click", new_callable=AsyncMock, return_value=(True, 0)):

                # We can test pre_check directly via run_single_series or a helper
                meta = {
                    "title": "Test Serial",
                    "year": 2024,
                    "description": "Juda qisqa",
                    "poster_url": "http://example.com/poster.jpg",
                    "category_ids": [1],
                    "genres": "Drama"
                }
                # If pre_check fails, create_series must NOT be called
                # and record_rejection must be called
                res = await pipeline._validate_and_pre_check(
                    session=mock_session,
                    kind="series",
                    title="Test Serial",
                    meta=meta,
                    item=mock_item
                )
                assert res is False
                assert mock_pre.called
                assert mock_rej.called
                assert not mock_create_series.called
