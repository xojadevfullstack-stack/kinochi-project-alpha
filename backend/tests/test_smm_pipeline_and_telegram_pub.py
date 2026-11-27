import json
import os
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

    hook_cap = build_movie_caption(
        movie_code="5064",
        imdb_rating=8.4,
        genres="Triller",
        hook_text="Bu sahnani ko'rib hayratda qolasiz!",
    )
    assert "Bu sahnani ko'rib hayratda qolasiz!" in hook_cap
    assert "#kinokod" in hook_cap



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


@pytest.mark.asyncio
async def test_create_smart_smm_clip_builds_poster_cover_when_available_and_falls_back(tmp_path):
    from io import BytesIO
    from PIL import Image

    buf = BytesIO()
    Image.new("RGB", (200, 300), color=(180, 40, 40)).save(buf, format="JPEG")
    out_path = str(tmp_path / "cover_pipe.mp4")

    async def fake_download(client, msg, dest_path, target_ratio=0.35, chunk_mb=None):
        with open(dest_path, "wb") as f:
            f.write(b"raw")
        return dest_path, 1200.0

    seen_cover_exists = []

    def fake_render(**kwargs):
        cp = kwargs.get("cover_image_path")
        seen_cover_exists.append(bool(cp and os.path.exists(cp)))
        return out_path

    with (
        patch("scraper.smm_pipeline.download_sparse_clip_source", side_effect=fake_download),
        patch("scraper.smm_pipeline.select_best_scene_start", new=AsyncMock(return_value={"start_sec": 420.0, "has_ad_banner": False, "blur_boxes": []})),
        patch("scraper.smm_pipeline._fetch_poster_bytes", new=AsyncMock(return_value=buf.getvalue())),
        patch("scraper.smm_pipeline.render_vertical_clip", side_effect=fake_render),
    ):
        await create_smart_smm_clip(
            client=MagicMock(),
            storage_msg=MagicMock(),
            output_path=out_path,
            movie_code="1014",
            imdb_rating=8.2,
            poster_url="https://image.tmdb.org/t/p/w500/test.jpg",
        )
    assert seen_cover_exists == [True]

    with (
        patch("scraper.smm_pipeline.download_sparse_clip_source", side_effect=fake_download),
        patch("scraper.smm_pipeline.select_best_scene_start", new=AsyncMock(return_value={"start_sec": 420.0, "has_ad_banner": False, "blur_boxes": []})),
        patch("scraper.smm_pipeline._fetch_poster_bytes", new=AsyncMock(return_value=None)),
        patch("scraper.smm_pipeline.render_vertical_clip", side_effect=fake_render) as mr2,
    ):
        await create_smart_smm_clip(
            client=MagicMock(),
            storage_msg=MagicMock(),
            output_path=out_path,
            movie_code="1014",
            poster_url="https://image.tmdb.org/t/p/w500/missing.jpg",
        )
    assert mr2.call_args.kwargs.get("cover_image_path") is None


@pytest.mark.asyncio
async def test_create_smart_smm_clip_clamps_scan_window_inside_sparse_chunk_ceiling(tmp_path):
    out_path = str(tmp_path / "bounded.mp4")

    async def fake_download(client, msg, dest_path, target_ratio=0.35, chunk_mb=None):
        with open(dest_path, "wb") as f:
            f.write(b"raw")
        return dest_path, 3047.0

    # Target ratio clamped at 0.84 while peak_sec sits at 3008.2/3053.2 (~98.5%): scan must NOT overshoot past downloaded headroom!
    mock_target = {"peak_sec": 3008.222, "srt_end_sec": 3053.222, "target_ratio": 0.84, "visual_cue": "Feast betrayal"}
    with (
        patch("scraper.smm_pipeline.find_viral_scene_target", new=AsyncMock(return_value=mock_target)),
        patch("scraper.smm_pipeline.download_sparse_clip_source", side_effect=fake_download),
        patch("scraper.smm_pipeline.select_best_scene_start", new=AsyncMock(return_value={"start_sec": 2580.0, "has_ad_banner": False, "blur_boxes": []})) as mock_sel,
        patch("scraper.smm_pipeline.render_vertical_clip", return_value=out_path),
    ):
        await create_smart_smm_clip(
            client=MagicMock(),
            storage_msg=MagicMock(),
            output_path=out_path,
            movie_code="1119",
            duration_sec=45.0,
            tmdb_id=1399,
            content_type="tv",
            season_number=3,
            episode_number=9,
        )

    chunk_floor = 3047.0 * 0.84
    assert mock_sel.call_args.kwargs["scan_start_sec"] >= chunk_floor
    assert mock_sel.call_args.kwargs["scan_end_sec"] <= chunk_floor + 45.0 + 40.0


@pytest.mark.asyncio
async def test_create_smart_smm_clip_passes_and_returns_hook_text(tmp_path):
    out_path = str(tmp_path / "hook_pipe.mp4")

    async def fake_download(client, msg, dest_path, target_ratio=0.35, chunk_mb=None):
        with open(dest_path, "wb") as f:
            f.write(b"raw")
        return dest_path, 1200.0

    fake_hint = {
        "peak_sec": 600.0,
        "srt_end_sec": 1200.0,
        "target_ratio": 0.44,
        "visual_cue": "Explosion",
        "hook_uz": "U eshikni ochgach hamma hayratda qoldi!",
        "yt_title_uz": "Bu sahnani oxirigacha ko'ring",
    }
    with (
        patch("scraper.smm_pipeline.find_viral_scene_target", new=AsyncMock(return_value=fake_hint)),
        patch("scraper.smm_pipeline.download_sparse_clip_source", side_effect=fake_download),
        patch("scraper.smm_pipeline.select_best_scene_start", new=AsyncMock(return_value={"start_sec": 530.0, "has_ad_banner": False, "blur_boxes": []})),
        patch("scraper.smm_pipeline.render_vertical_clip", return_value=out_path) as mr,
    ):
        meta = await create_smart_smm_clip(
            client=MagicMock(),
            storage_msg=MagicMock(),
            output_path=out_path,
            movie_code="1014",
            tmdb_id=299534,
            original_title="Avengers: Endgame",
            genres="Triller, Fantastika",
        )

    assert meta["hook_text"] == "U eshikni ochgach hamma hayratda qoldi!"
    assert mr.call_args.kwargs["hook_text"] == "U eshikni ochgach hamma hayratda qoldi!"


@pytest.mark.asyncio
async def test_create_smart_smm_clip_scan_window_wraps_peak_and_uses_backup_on_credits(tmp_path):
    out_path = str(tmp_path / "climax_wrap.mp4")

    async def fake_download(client, msg, dest_path, target_ratio=0.35, chunk_mb=None):
        with open(dest_path, "wb") as f:
            f.write(b"raw")
        return dest_path, 2818.0

    # Peak at 2175s with ~35s lead-in anchor (0.7594) -> scan window MUST cover mapped_peak=2175s directly
    bb_hint = {
        "peak_sec": 2175.0,
        "srt_end_sec": 2818.0,
        "target_ratio": round((2175.0 - 35.0) / 2818.0, 4),
        "backup_ratio": 0.42,
        "visual_cue": "Knife standoff",
    }
    with (
        patch("scraper.smm_pipeline.find_viral_scene_target", new=AsyncMock(return_value=bb_hint)),
        patch("scraper.smm_pipeline.download_sparse_clip_source", side_effect=fake_download),
        patch("scraper.smm_pipeline.select_best_scene_start", new=AsyncMock(return_value={"start_sec": 2162.0, "has_ad_banner": False, "blur_boxes": []})) as mock_sel,
        patch("scraper.smm_pipeline.render_vertical_clip", return_value=out_path),
    ):
        await create_smart_smm_clip(
            client=MagicMock(),
            storage_msg=MagicMock(),
            output_path=out_path,
            movie_code="1272",
            duration_sec=28.0,
            tmdb_id=1396,
            content_type="tv",
            season_number=5,
            episode_number=14,
        )

    assert mock_sel.call_args.kwargs["scan_start_sec"] <= 2175.0 <= mock_sel.call_args.kwargs["scan_end_sec"]
    assert mock_sel.call_args.kwargs["compare_candidates"] >= 3

    # When late climax hits end credits, retry should use backup_ratio (0.42) instead of blind 0.50
    seen_ratios = []

    async def fake_dl_retry(client, msg, dest_path, target_ratio=0.35, chunk_mb=None):
        seen_ratios.append(target_ratio)
        with open(dest_path, "wb") as f:
            f.write(b"raw")
        return dest_path, 2818.0

    late_hint = {"peak_sec": 2650.0, "srt_end_sec": 2818.0, "target_ratio": 0.90, "backup_ratio": 0.42, "visual_cue": "Shootout"}
    sel_side_effects = [
        {"start_sec": 2550.0, "is_credits": True, "has_ad_banner": False, "blur_boxes": []},
        {"start_sec": 1190.0, "is_credits": False, "has_ad_banner": False, "blur_boxes": []},
    ]
    with (
        patch("scraper.smm_pipeline.find_viral_scene_target", new=AsyncMock(return_value=late_hint)),
        patch("scraper.smm_pipeline.download_sparse_clip_source", side_effect=fake_dl_retry),
        patch("scraper.smm_pipeline.select_best_scene_start", new=AsyncMock(side_effect=sel_side_effects)),
        patch("scraper.smm_pipeline.render_vertical_clip", return_value=out_path),
    ):
        await create_smart_smm_clip(
            client=MagicMock(),
            storage_msg=MagicMock(),
            output_path=out_path,
            movie_code="1272",
            duration_sec=28.0,
            tmdb_id=1396,
        )

    assert seen_ratios == [pytest.approx(0.90), pytest.approx(0.42)]


@pytest.mark.asyncio
async def test_send_admin_alert_rate_limits_duplicate_keys(monkeypatch):
    from scraper.smm_publishers.telegram_pub import _ALERT_COOLDOWN, send_admin_alert

    _ALERT_COOLDOWN.clear()
    monkeypatch.setenv("BOT_TOKEN", "123:abc")
    monkeypatch.setenv("ADMIN_TELEGRAM_ID", "1990156236")
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"ok": True}
    client = AsyncMock()
    client.__aenter__.return_value = client
    client.post = AsyncMock(return_value=resp)

    with patch("scraper.smm_publishers.telegram_pub.httpx.AsyncClient", return_value=client):
        ok1 = await send_admin_alert("pub_err:youtube", "YouTube HTTP 400", cooldown_sec=3600)
        ok2 = await send_admin_alert("pub_err:youtube", "YouTube HTTP 400", cooldown_sec=3600)

    assert ok1 is True
    assert ok2 is False
    assert client.post.call_count == 1



@pytest.mark.asyncio
async def test_fetch_poster_bytes_reads_full_tg_proxy_url_directly_from_telegram():
    from scraper.smm_pipeline import _fetch_poster_bytes

    with (
        patch(
            "app.infrastructure.telegram.telegram_client.telegram_client.download_file_bytes",
            new=AsyncMock(return_value=(b"jpeg-v7-cover", "image/jpeg")),
        ) as mock_tg,
        patch("httpx.AsyncClient.get") as mock_http,
    ):
        data = await _fetch_poster_bytes(
            "https://kinochi-project-alpha-9g6j.onrender.com/api/v1/posters/tg/AgAC_V7_COVER"
        )

    assert data == b"jpeg-v7-cover"
    mock_tg.assert_awaited_once_with("AgAC_V7_COVER")
    mock_http.assert_not_called()



