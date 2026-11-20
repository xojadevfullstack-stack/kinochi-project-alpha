import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scraper.smm_pipeline import create_smart_smm_clip
from scraper.smm_publishers.telegram_pub import (
    TelegramChannelPublisher,
    build_movie_caption,
)


def test_build_movie_caption_hides_title_and_includes_code_and_bot():
    caption = build_movie_caption(movie_code="5064", imdb_rating=8.4, genres="Fantastika, Jangari")
    assert "#5064" in caption or "5064" in caption
    assert "@kinochi_mvp_bot" in caption
    assert "8.4" in caption
    assert "#kino" in caption


@pytest.mark.asyncio
async def test_telegram_publisher_sends_video_with_deep_link_button(tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"fake-mp4-data")

    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {"ok": True, "result": {"message_id": 991}}

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.post.return_value = mock_resp

    pub = TelegramChannelPublisher(bot_token="123:ABC", channel_id="@test_kinochi", bot_username="@kinochi_mvp_bot")
    with patch("scraper.smm_publishers.telegram_pub.httpx.AsyncClient", return_value=mock_client):
        res = await pub.publish(str(video), caption="Test caption", movie_code="5064")

    assert res.success is True
    assert res.platform == "telegram"
    assert res.post_id == "991"
    call_kwargs = mock_client.post.call_args.kwargs
    markup = json.loads(call_kwargs["data"]["reply_markup"])
    btn_url = markup["inline_keyboard"][0][0]["url"]
    assert btn_url == "https://t.me/kinochi_mvp_bot?start=5064"


@pytest.mark.asyncio
async def test_telegram_publisher_handles_missing_config_and_api_error(tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"fake")

    pub_empty = TelegramChannelPublisher(bot_token="", channel_id="")
    res_empty = await pub_empty.publish(str(video), caption="x", movie_code="1")
    assert res_empty.success is False
    assert res_empty.error

    mock_resp = MagicMock(status_code=400, text="Bad Request: chat not found")
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.post.return_value = mock_resp

    pub = TelegramChannelPublisher(bot_token="123:ABC", channel_id="@bad")
    with patch("scraper.smm_publishers.telegram_pub.httpx.AsyncClient", return_value=mock_client):
        res_err = await pub.publish(str(video), caption="x", movie_code="1")
    assert res_err.success is False
    assert "400" in (res_err.error or "")


@pytest.mark.asyncio
async def test_create_smart_smm_clip_auto_enables_ad_blur_and_cleans_raw(tmp_path):
    out_path = str(tmp_path / "final.mp4")

    async def fake_download(client, msg, dest_path, target_ratio=0.35, chunk_mb=30):
        with open(dest_path, "wb") as f:
            f.write(b"raw")
        return dest_path, 2000.0

    mock_score = {
        "start_sec": 705.0,
        "score": 88.0,
        "mean_volume_db": -18.0,
        "has_ad_banner": True,
        "reason": "Mostbet banner",
    }

    with (
        patch("scraper.smm_pipeline.download_sparse_clip_source", side_effect=fake_download),
        patch("scraper.smm_pipeline.select_best_scene_start", new=AsyncMock(return_value=mock_score)),
        patch("scraper.smm_pipeline.render_vertical_clip", return_value=out_path) as mock_render,
    ):
        meta = await create_smart_smm_clip(
            client=MagicMock(),
            storage_msg=MagicMock(),
            output_path=out_path,
            movie_code="5064",
            imdb_rating=8.4,
        )

    assert meta["output_path"] == out_path
    assert meta["blur_bottom_ad"] is True
    assert meta["start_sec"] == 705.0
    assert mock_render.call_args.kwargs["blur_bottom_ad"] is True
    assert mock_render.call_args.kwargs["blur_watermark"] is True
