import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import os
import sys

# Ensure scraper is importable
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


@pytest.mark.asyncio
async def test_ingest_pusu_enforces_gate_and_no_asosiy():
    """F-001 regression test: scraper/ingest_pusu.py must use admission_gate and never use 'Asosiy'."""
    from scraper.ingest_pusu import ingest_single_episode

    mock_client = AsyncMock()
    mock_src_msg = MagicMock()
    mock_src_msg.media = MagicMock()
    mock_client.get_messages.return_value = mock_src_msg

    mock_topic_msg = MagicMock()
    mock_topic_msg.id = 101
    mock_storage_msg = MagicMock()
    mock_storage_msg.id = 202
    mock_storage_msg.media = MagicMock()
    mock_client.send_file.side_effect = [mock_topic_msg, mock_storage_msg]

    mock_session = AsyncMock()
    # 1. Existing check returns None
    mock_res_existing = MagicMock()
    mock_res_existing.scalar.return_value = None
    mock_session.execute.return_value = mock_res_existing

    # Mock SeriesService and Repository
    mock_created_ep = MagicMock()
    mock_created_ep.id = 555

    with patch("scraper.ingest_pusu.async_session_factory") as mock_factory, \
         patch("scraper.ingest_pusu.pack_bot_file_id", return_value="bot_file_123"), \
         patch("scraper.ingest_pusu.final_check") as mock_final_check, \
         patch("scraper.ingest_pusu.pre_check") as mock_pre_check, \
         patch("app.application.series.series_service.SeriesService.create_episode", return_value=mock_created_ep), \
         patch("app.infrastructure.db.repositories.series_repository.SeriesRepository.add_episode_translation") as mock_add_trans:

        mock_factory.return_value.__aenter__.return_value = mock_session
        mock_pre_check.return_value = (True, [])
        mock_final_check.return_value = (True, [])

        success = await ingest_single_episode(
            client=mock_client,
            season_id=1,
            season_num=1,
            ep_num=1,
            source_ch="test_ch",
            source_msg_id=12,
            topic_id=999
        )

        assert success is True
        # Verify pre_check was called
        assert mock_pre_check.called
        # Verify final_check was called
        assert mock_final_check.called
        # Verify language is NOT 'Asosiy'
        _, kwargs = mock_add_trans.call_args
        if not kwargs and len(mock_add_trans.call_args[0]) >= 2:
            lang_arg = mock_add_trans.call_args[0][1]
        else:
            lang_arg = kwargs.get("language")
        assert lang_arg != "Asosiy"
        assert lang_arg in ("O'zbekcha", "O'zbek tilida", "uz")
