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
    assert "@MediaPlusOfficialBot" in caption
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


@pytest.mark.asyncio
async def test_send_admin_smm_preview_sends_buttons_in_semi_auto_and_plain_in_full_auto(tmp_path):
    from scraper.smm_publishers.telegram_pub import send_admin_smm_preview

    video = tmp_path / "clip_7.mp4"
    video.write_bytes(b"mp4-bytes")

    mock_resp = MagicMock(status_code=200)
    mock_resp.json.return_value = {"ok": True, "result": {"message_id": 55}}
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.post.return_value = mock_resp

    with patch("scraper.smm_publishers.telegram_pub.httpx.AsyncClient", return_value=mock_client):
        ok_semi = await send_admin_smm_preview(
            job_id=7,
            title="Ouk Strit",
            movie_code="3956",
            mode="SEMI_AUTO",
            video_path=str(video),
            caption="Test caption",
            admin_telegram_id="99887766",
            bot_token="123:BOT",
        )
        ok_auto = await send_admin_smm_preview(
            job_id=8,
            title="Matritsa",
            movie_code="1001",
            mode="FULL_AUTO",
            video_path=str(video),
            caption="Auto caption",
            admin_telegram_id="99887766",
            bot_token="123:BOT",
        )

    assert ok_semi is True and ok_auto is True
    semi_data = mock_client.post.call_args_list[0].kwargs["data"]
    assert semi_data["chat_id"] == "99887766"
    kb = json.loads(semi_data["reply_markup"])["inline_keyboard"]
    cb_datas = [btn.get("callback_data") for row in kb for btn in row]
    assert "smm_approve:7" in cb_datas
    assert "smm_publish:7" in cb_datas
    assert "smm_reject:7" in cb_datas

    auto_data = mock_client.post.call_args_list[1].kwargs["data"]
    assert auto_data["chat_id"] == "99887766"
    assert "reply_markup" not in auto_data


@pytest.mark.asyncio
async def test_create_smart_smm_clip_emits_progress_callbacks(tmp_path):
    out_path = str(tmp_path / "prog.mp4")
    events = []

    async def fake_download(client, msg, dest_path, target_ratio=0.35, chunk_mb=None):
        with open(dest_path, "wb") as f:
            f.write(b"raw")
        return dest_path, 1500.0

    async def on_prog(pct, stage):
        events.append((pct, stage))

    with (
        patch("scraper.smm_pipeline.download_sparse_clip_source", side_effect=fake_download),
        patch("scraper.smm_pipeline.select_best_scene_start", new=AsyncMock(return_value={"start_sec": 100.0, "has_ad_banner": False})),
        patch("scraper.smm_pipeline.render_vertical_clip", return_value=out_path),
    ):
        await create_smart_smm_clip(
            client=MagicMock(),
            storage_msg=MagicMock(),
            output_path=out_path,
            movie_code="3956",
            progress_cb=on_prog,
        )

    pcts = [p for p, _ in events]
    assert pcts == [15, 45, 70, 95]


@pytest.mark.asyncio
async def test_create_smart_smm_clip_avoids_legacy_dual_corner_blur_when_vision_enabled(tmp_path):
    out_path = str(tmp_path / "no_dual.mp4")

    async def fake_download(client, msg, dest_path, target_ratio=0.35, chunk_mb=None):
        with open(dest_path, "wb") as f:
            f.write(b"raw")
        return dest_path, 1500.0

    with (
        patch("scraper.smm_pipeline.download_sparse_clip_source", side_effect=fake_download),
        patch(
            "scraper.smm_pipeline.select_best_scene_start",
            new=AsyncMock(return_value={"start_sec": 120.0, "has_ad_banner": False, "vision_used": False, "blur_boxes": []}),
        ),
        patch("scraper.smm_pipeline.render_vertical_clip", return_value=out_path) as mock_render,
    ):
        await create_smart_smm_clip(
            client=MagicMock(),
            storage_msg=MagicMock(),
            output_path=out_path,
            movie_code="3957",
            check_vision=True,
        )

    assert mock_render.call_args.kwargs["blur_boxes"] == []


@pytest.mark.asyncio
async def test_create_smart_smm_clip_uses_srt_target_ratio_and_visual_cue(tmp_path):
    out_path = str(tmp_path / "targeted.mp4")
    seen = {}

    async def fake_download(client, msg, dest_path, target_ratio=0.35, chunk_mb=None):
        seen["target_ratio"] = target_ratio
        with open(dest_path, "wb") as f:
            f.write(b"raw")
        return dest_path, 3376.0

    mock_target = {
        "peak_sec": 3225.0,
        "srt_end_sec": 3318.2,
        "target_ratio": 0.9493,
        "visual_cue": "Ned Stark kneeling at Baelor sept",
        "reason_uz": "Kulminatsiya",
    }
    mock_score = {"start_sec": 3207.8, "has_ad_banner": False, "blur_boxes": [], "score": 280.0, "reason": "Matched"}

    with (
        patch("scraper.smm_pipeline.find_viral_scene_target", new=AsyncMock(return_value=mock_target)),
        patch("scraper.smm_pipeline.download_sparse_clip_source", side_effect=fake_download),
        patch("scraper.smm_pipeline.select_best_scene_start", new=AsyncMock(return_value=mock_score)) as mock_select,
        patch("scraper.smm_pipeline.render_vertical_clip", return_value=out_path),
    ):
        meta = await create_smart_smm_clip(
            client=MagicMock(),
            storage_msg=MagicMock(),
            output_path=out_path,
            movie_code="1099",
            tmdb_id=1399,
            original_title="Game of Thrones",
            content_type="tv",
            season_number=1,
            episode_number=9,
        )

    assert seen["target_ratio"] == pytest.approx(0.9493)
    assert mock_select.call_args.kwargs["visual_cue"] == "Ned Stark kneeling at Baelor sept"
    assert mock_select.call_args.kwargs["compare_candidates"] == 3
    assert mock_select.call_args.kwargs["scan_start_sec"] >= 3376.0 * 0.9493
    assert meta["start_sec"] == pytest.approx(3207.8)
