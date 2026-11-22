import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

BOT_DIR = Path(__file__).resolve().parents[1]
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))


def test_format_episode_caption_prefers_short_code():
    from utils.episode_sender import format_episode_caption

    caption = format_episode_caption(
        {
            "series_title": "Qashqirlar makoni",
            "season_number": 1,
            "episode_number": 5,
            "code": "CmvacRvk",
            "short_code": "1091",
            "display_code": "S1-CH5",
            "series_id": 998,
        }
    )
    assert "<code>1091</code>" in caption
    assert "s_998" in caption


@pytest.mark.asyncio
async def test_bot_resolves_4digit_episode_short_code_directly():
    from utils.code_resolver import resolve_and_send_content

    bot = MagicMock()
    ep_payload = {
        "id": 55,
        "code": "CmvacRvk",
        "short_code": "1091",
        "series_id": 998,
        "series_title": "Qashqirlar makoni",
        "season_number": 1,
        "episode_number": 5,
        "translations": [{"telegram_file_id": "file_123"}],
    }

    with (
        patch("services.api_client.api_client.get_movie_by_code", new=AsyncMock(return_value=None)),
        patch("services.api_client.api_client.get_episode_by_code", new=AsyncMock(return_value=ep_payload)),
        patch("utils.code_resolver.send_episode_to_user", new=AsyncMock(return_value=True)) as mock_send_ep,
    ):
        ok = await resolve_and_send_content(bot, 777, "1091")

    assert ok is True
    mock_send_ep.assert_awaited_once_with(bot, 777, ep_payload)
