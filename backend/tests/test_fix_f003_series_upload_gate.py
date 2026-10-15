import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


@pytest.mark.asyncio
async def test_upload_episode_video_final_check_and_promote():
    """F-003 regression test: upload_episode_video must invoke final_check and promote_to_published."""
    from app.api.v1.series import upload_episode_video
    from app.infrastructure.db.models.series import SeriesModel

    mock_service = AsyncMock()
    mock_ep = MagicMock()
    mock_ep.id = 1
    mock_ep.code = "ep_1_code"
    mock_service.get_episode_by_id.return_value = mock_ep

    mock_ep_detail = MagicMock()
    mock_ep_detail.series_id = 99
    mock_ep_detail.series_title = "Test Serial"
    mock_ep_detail.season_number = 1
    mock_ep_detail.episode_number = 1
    mock_ep_detail.title = "1-qism"
    mock_ep_detail.display_code = "ep_99_1"
    mock_service.get_episode_detail_by_code.return_value = mock_ep_detail

    mock_series = MagicMock()
    mock_series.id = 99
    mock_series.title = "Test Serial"
    mock_series.release_year = 2024
    mock_series.publish_status = "pending"
    mock_service.get_series_by_id.return_value = mock_series

    mock_created_trans = MagicMock()
    mock_service.add_episode_translation.return_value = mock_created_trans

    mock_file = MagicMock()
    mock_file.filename = "episode_1.mp4"
    mock_file.content_type = "video/mp4"
    mock_file.read = AsyncMock(side_effect=[b"video_content", b""])

    mock_db_session = AsyncMock()
    mock_series_model = MagicMock(spec=SeriesModel)
    mock_series_model.id = 99
    mock_series_model.title = "Test Serial"
    mock_series_model.publish_status = "pending"
    mock_db_session.get.return_value = mock_series_model

    with patch("app.api.v1.series.telegram_client.send_video_to_storage", new_callable=AsyncMock, return_value=("file_abc_123", 456)), \
         patch("app.api.v1.series.final_check", return_value=(True, [])) as mock_final_check, \
         patch("app.api.v1.series.promote_to_published", new_callable=AsyncMock) as mock_promote, \
         patch("app.api.v1.series.async_session_factory") as mock_session_factory, \
         patch("app.api.v1.series.job_manager.create_job", new_callable=AsyncMock, return_value="job_123"), \
         patch("app.api.v1.series.job_manager.set_processing", new_callable=AsyncMock), \
         patch("app.api.v1.series.job_manager.set_progress", new_callable=AsyncMock), \
         patch("app.api.v1.series.job_manager.set_done", new_callable=AsyncMock), \
         patch("app.api.v1.series.job_manager.cleanup_old_jobs", new_callable=AsyncMock), \
         patch("aiofiles.open") as mock_aiofiles:

        mock_session_factory.return_value.__aenter__.return_value = mock_db_session

        mock_aio_file = AsyncMock()
        mock_aiofiles.return_value.__aenter__.return_value = mock_aio_file

        # Call endpoint
        mock_req = MagicMock()
        resp = await upload_episode_video(
            episode_id=1,
            request=mock_req,
            file=mock_file,
            language="O'zbekcha",
            service=mock_service
        )

        assert resp.job_id is not None

        # Give background task a moment to execute
        import asyncio
        await asyncio.sleep(0.1)

        # Assert final_check was called
        assert mock_final_check.called, "final_check must be called after episode video upload"
        # Assert promote_to_published was called
        assert mock_promote.called, "promote_to_published must be called to publish parent series"
