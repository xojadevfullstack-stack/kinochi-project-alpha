"""Tests for Slice 2: TMDb textless poster lookup, Vision layout analysis, OpenCV cleanup, and Pillow render."""

import io
from unittest.mock import AsyncMock, patch
import pytest
import numpy as np
from PIL import Image


def _make_sample_jpeg(width: int = 500, height: int = 750, color=(20, 40, 75)) -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_tmdb_get_textless_poster_prefers_null_language():
    from app.infrastructure.external.tmdb_client import tmdb_client

    payload = {
        "posters": [
            {"file_path": "/en_only.jpg", "iso_639_1": "en", "vote_average": 9.9, "width": 1000, "height": 1500},
            {"file_path": "/clean_low.jpg", "iso_639_1": None, "vote_average": 5.0, "width": 500, "height": 750},
            {"file_path": "/clean_best.jpg", "iso_639_1": None, "vote_average": 9.2, "width": 1000, "height": 1500},
        ]
    }
    with (
        patch("app.infrastructure.external.tmdb_client.get_cache", new=AsyncMock(return_value=None)),
        patch("app.infrastructure.external.tmdb_client.set_cache", new=AsyncMock(return_value=True)),
        patch.object(tmdb_client, "_request_with_retry", new=AsyncMock(return_value=payload)),
    ):
        url = await tmdb_client.get_textless_poster(tmdb_id=299534, content_type="movie")

    assert url == "https://image.tmdb.org/t/p/w500/clean_best.jpg"


def test_render_uzbek_title_on_poster_preserves_dimensions_and_renders_cleanly():
    from app.infrastructure.external.poster_localizer import render_uzbek_title_on_poster

    raw_bytes = _make_sample_jpeg(500, 750, color=(18, 28, 52))
    out_bytes = render_uzbek_title_on_poster(
        image_bytes=raw_bytes,
        title="QASOSKORLAR: INTIHO",
        style={
            "placement": "bottom",
            "font_style": "epic",
            "primary_color": "#E5B84B",
            "secondary_color": "#FFFFFF",
            "title_box": [780, 80, 920, 920],
        },
        remove_existing_text=True,
    )

    out_img = Image.open(io.BytesIO(out_bytes))
    assert out_img.size == (500, 750)
    assert out_img.format == "JPEG"
    # Verify bottom title region changed while top sky stayed intact
    assert out_img.getpixel((250, 50))[:2] == (18, 28)
    assert out_bytes != raw_bytes


@pytest.mark.asyncio
async def test_localize_poster_prefers_textless_and_uploads():
    from app.infrastructure.external.poster_localizer import localize_poster_and_upload

    raw_bytes = _make_sample_jpeg(500, 750)

    with (
        patch(
            "app.infrastructure.external.poster_localizer.tmdb_client.get_textless_poster",
            new=AsyncMock(return_value="https://image.tmdb.org/t/p/w500/clean_textless.jpg"),
        ),
        patch(
            "app.infrastructure.external.poster_localizer._download_image_bytes",
            new=AsyncMock(return_value=raw_bytes),
        ),
        patch(
            "app.infrastructure.external.poster_localizer.analyze_poster_style",
            new=AsyncMock(
                return_value={
                    "placement": "bottom",
                    "font_style": "bold",
                    "primary_color": "#FFFFFF",
                    "secondary_color": "#E50914",
                    "title_box": None,
                }
            ),
        ),
        patch(
            "app.infrastructure.external.poster_localizer.upload_poster_to_telegram",
            new=AsyncMock(return_value="https://api.example.com/api/v1/posters/tg/AgAC_NEW_UZ_POSTER"),
        ) as mock_upload,
    ):
        result_url = await localize_poster_and_upload(
            title="O'rgimchak odam: Uyga yo'l yo'q",
            tmdb_id=634649,
            content_type="movie",
            manual_poster_url="https://image.tmdb.org/t/p/w500/original_en.jpg",
            code="3957",
            topic_chat_id=-100123,
            topic_id=88,
        )

    assert result_url == "https://api.example.com/api/v1/posters/tg/AgAC_NEW_UZ_POSTER"
    mock_upload.assert_awaited_once()
    assert mock_upload.call_args.kwargs["topic_id"] == 88


@pytest.mark.asyncio
async def test_localize_poster_manual_url_inpaints_existing_title():
    from app.infrastructure.external.poster_localizer import localize_poster_and_upload

    raw_bytes = _make_sample_jpeg(500, 750, color=(15, 35, 60))

    with (
        patch(
            "app.infrastructure.external.poster_localizer._download_image_bytes",
            new=AsyncMock(return_value=raw_bytes),
        ),
        patch(
            "app.infrastructure.external.poster_localizer.analyze_poster_style",
            new=AsyncMock(
                return_value={
                    "placement": "top",
                    "font_style": "bold",
                    "primary_color": "#E31C19",
                    "secondary_color": "#FFFFFF",
                    "title_box": [60, 50, 180, 950],
                }
            ),
        ),
        patch(
            "app.infrastructure.external.poster_localizer.upload_poster_to_telegram",
            new=AsyncMock(return_value="https://api.example.com/api/v1/posters/tg/AgAC_MANUAL_UZ"),
        ),
    ):
        result_url = await localize_poster_and_upload(
            title="Muqaddima",
            tmdb_id=None,
            content_type="movie",
            manual_poster_url="https://example.com/inception_en.jpg",
            code="1010",
        )

    assert result_url == "https://api.example.com/api/v1/posters/tg/AgAC_MANUAL_UZ"


@pytest.mark.asyncio
async def test_localize_poster_analyzes_original_poster_for_style_when_textless_exists():
    from app.infrastructure.external.poster_localizer import localize_poster_and_upload

    textless_bytes = _make_sample_jpeg(500, 750, color=(120, 120, 120))
    original_bytes = _make_sample_jpeg(500, 750, color=(200, 110, 40))

    async def _fake_dl(url: str):
        return textless_bytes if "clean_textless" in url else original_bytes

    with (
        patch(
            "app.infrastructure.external.poster_localizer.tmdb_client.get_textless_poster",
            new=AsyncMock(return_value="https://image.tmdb.org/t/p/w500/clean_textless.jpg"),
        ),
        patch(
            "app.infrastructure.external.poster_localizer._download_image_bytes",
            side_effect=_fake_dl,
        ),
        patch(
            "app.infrastructure.external.poster_localizer.analyze_poster_style",
            new=AsyncMock(
                return_value={
                    "placement": "top",
                    "y_ratio": 0.045,
                    "font_style": "bold",
                    "primary_color": "#F97316",
                    "secondary_color": "#F97316",
                    "needs_backdrop": False,
                    "title_box": [40, 120, 150, 880],
                }
            ),
        ) as mock_analyze,
        patch(
            "app.infrastructure.external.poster_localizer.render_uzbek_title_on_poster",
            return_value=b"rendered-jpg",
        ) as mock_render,
        patch(
            "app.infrastructure.external.poster_localizer.upload_poster_to_telegram",
            new=AsyncMock(return_value="https://api.example.com/api/v1/posters/tg/AgAC_ORANGE_TOP"),
        ),
    ):
        res = await localize_poster_and_upload(
            title="Xolms va Vatson",
            tmdb_id=426563,
            content_type="movie",
            manual_poster_url="https://image.tmdb.org/t/p/w500/orEUlKndjV1rEcWqXbbjegjfv97.jpg",
            code="ANE487",
        )

    assert res == "https://api.example.com/api/v1/posters/tg/AgAC_ORANGE_TOP"
    assert mock_analyze.await_args.args[0] == original_bytes
    assert mock_render.call_args.kwargs["image_bytes"] == textless_bytes


def test_render_uzbek_title_on_poster_preserves_top_y_ratio_orange_color_without_dark_mud():
    from app.infrastructure.external.poster_localizer import render_uzbek_title_on_poster

    raw_bytes = _make_sample_jpeg(500, 750, color=(150, 155, 160))
    out_bytes = render_uzbek_title_on_poster(
        image_bytes=raw_bytes,
        title="Xolms va Vatson",
        style={
            "placement": "top",
            "y_ratio": 0.045,
            "font_style": "bold",
            "primary_color": "#F97316",
            "secondary_color": "#F97316",
            "needs_backdrop": False,
            "title_box": [40, 120, 150, 880],
        },
        remove_existing_text=False,
    )
    out_img = Image.open(io.BytesIO(out_bytes))
    # Top sky outside title should remain bright gray (not darkened by a heavy black gradient)
    corner = out_img.getpixel((10, 10))
    assert corner[0] >= 135 and corner[1] >= 140
    # Bottom region should stay completely untouched gray
    bottom = out_img.getpixel((250, 700))
    assert bottom[0] >= 140 and bottom[1] >= 145
    # Orange title pixels should appear inside top band (around y=40..120), NOT red #E50914
    top_band = [out_img.getpixel((x, y)) for x in range(120, 380, 4) for y in range(30, 110, 2)]
    assert any(r > 200 and 70 <= g <= 160 and b < 80 for (r, g, b) in top_band)


@pytest.mark.asyncio
async def test_localize_poster_uses_cloudflare_on_manual_url_first_without_textless_swap():
    from app.infrastructure.external import poster_localizer

    orig_bytes = _make_sample_jpeg(500, 750, color=(40, 80, 120))
    cf_out_bytes = _make_sample_jpeg(500, 750, color=(42, 82, 122))

    with (
        patch.object(poster_localizer.settings, "CLOUDFLARE_ACCOUNT_ID", "cf_acc_123"),
        patch.object(poster_localizer.settings, "CLOUDFLARE_API_TOKEN", "cf_tok_123"),
        patch.object(poster_localizer.tmdb_client, "get_textless_poster", new=AsyncMock()) as mock_textless,
        patch.object(poster_localizer, "_download_image_bytes", new=AsyncMock(return_value=orig_bytes)) as mock_dl,
        patch.object(
            poster_localizer,
            "analyze_poster_style",
            new=AsyncMock(
                return_value={
                    "placement": "bottom",
                    "y_ratio": 0.7,
                    "font_style": "bold",
                    "primary_color": "#D0D8E0",
                    "secondary_color": "#708090",
                    "needs_backdrop": False,
                    "title_box": [700, 60, 920, 940],
                    "style_brief": "3D beveled metallic silver chrome blocky italic letters at bottom",
                }
            ),
        ),
        patch.object(
            poster_localizer,
            "edit_poster_with_cloudflare",
            new=AsyncMock(return_value=cf_out_bytes),
        ) as mock_cf,
        patch.object(
            poster_localizer,
            "upload_poster_to_telegram",
            new=AsyncMock(return_value="https://api.example.com/api/v1/posters/tg/AgAC_CF_EXACT"),
        ) as mock_upload,
    ):
        url = await poster_localizer.localize_poster_and_upload(
            title="Ertangi kun afsonalari",
            tmdb_id=62643,
            content_type="tv",
            manual_poster_url="https://image.tmdb.org/t/p/w500/qNgAcg4gNYbZ9mySLB9ZX4ehZb6.jpg",
        )

    assert url == "https://api.example.com/api/v1/posters/tg/AgAC_CF_EXACT"
    mock_textless.assert_not_called()
    mock_dl.assert_awaited_once_with("https://image.tmdb.org/t/p/w500/qNgAcg4gNYbZ9mySLB9ZX4ehZb6.jpg")
    assert mock_cf.await_args.args[0] == orig_bytes
    assert mock_upload.await_args.kwargs["photo_bytes"] == cf_out_bytes


@pytest.mark.asyncio
async def test_edit_poster_with_cloudflare_retries_4b_on_ocr_fail_and_falls_back_when_flagged():
    import base64
    from unittest.mock import MagicMock
    from app.infrastructure.external import poster_localizer

    orig_bytes = _make_sample_jpeg(500, 750)
    png_b64 = base64.b64encode(_make_sample_jpeg(512, 768)).decode("ascii")

    resp_ok = MagicMock(status_code=200, headers={"content-type": "application/json"})
    resp_ok.json.return_value = {"result": {"image": png_b64}}
    resp_flagged = MagicMock(status_code=400, headers={"content-type": "application/json"}, text='{"code":3030}')

    # Scenario 1: 9b fails OCR -> retries 4b -> passes OCR
    with (
        patch.object(poster_localizer.settings, "CLOUDFLARE_ACCOUNT_ID", "cf_acc"),
        patch.object(poster_localizer.settings, "CLOUDFLARE_API_TOKEN", "cf_tok"),
        patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=[resp_ok, resp_ok])),
        patch.object(poster_localizer, "verify_localized_poster_ocr", new=AsyncMock(side_effect=[False, True])),
    ):
        out = await poster_localizer.edit_poster_with_cloudflare(
            orig_bytes,
            title="Ertangi kun afsonalari",
            style={"placement": "bottom", "style_brief": "3D metallic"},
        )
    assert out is not None
    assert Image.open(io.BytesIO(out)).size == (500, 750)

    # Scenario 2: both flagged (code 3030) -> returns None so Pillow fallback takes over
    with (
        patch.object(poster_localizer.settings, "CLOUDFLARE_ACCOUNT_ID", "cf_acc"),
        patch.object(poster_localizer.settings, "CLOUDFLARE_API_TOKEN", "cf_tok"),
        patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=[resp_flagged, resp_flagged])),
    ):
        out_none = await poster_localizer.edit_poster_with_cloudflare(
            orig_bytes,
            title="Agentlar",
            style={"placement": "bottom", "style_brief": "chrome"},
        )
    assert out_none is None


@pytest.mark.asyncio
async def test_edit_poster_with_cloudflare_prefers_4b_first_and_stops_on_429():
    import base64
    from unittest.mock import MagicMock
    from app.infrastructure.external import poster_localizer

    assert poster_localizer._CF_IMAGE_EDIT_MODELS[0].endswith("flux-2-klein-4b")
    assert poster_localizer._CF_IMAGE_EDIT_MODELS[1].endswith("flux-2-klein-9b")

    orig_bytes = _make_sample_jpeg(500, 750)
    png_b64 = base64.b64encode(_make_sample_jpeg(512, 768)).decode("ascii")
    resp_ok = MagicMock(status_code=200, headers={"content-type": "application/json"})
    resp_ok.json.return_value = {"result": {"image": png_b64}}
    resp_429 = MagicMock(status_code=429, headers={"content-type": "application/json"}, text='{"code":4006}')

    with (
        patch.object(poster_localizer.settings, "CLOUDFLARE_ACCOUNT_ID", "cf_acc"),
        patch.object(poster_localizer.settings, "CLOUDFLARE_API_TOKEN", "cf_tok"),
        patch("httpx.AsyncClient.post", new=AsyncMock(return_value=resp_ok)) as mock_post,
        patch.object(poster_localizer, "verify_localized_poster_ocr", new=AsyncMock(return_value=True)),
    ):
        out = await poster_localizer.edit_poster_with_cloudflare(
            orig_bytes,
            title="Qochgan Yer",
            style={"placement": "bottom", "style_brief": "flat white condensed"},
        )
    assert out is not None
    assert mock_post.await_count == 1
    assert mock_post.await_args.args[0].endswith("flux-2-klein-4b")
    assert "Exact word count: 2" in mock_post.await_args.kwargs["data"]["prompt"]

    # 429 daily quota exhausted stops immediately without burning a second call on 9b
    with (
        patch.object(poster_localizer.settings, "CLOUDFLARE_ACCOUNT_ID", "cf_acc"),
        patch.object(poster_localizer.settings, "CLOUDFLARE_API_TOKEN", "cf_tok"),
        patch("httpx.AsyncClient.post", new=AsyncMock(return_value=resp_429)) as mock_post_429,
    ):
        out_429 = await poster_localizer.edit_poster_with_cloudflare(
            orig_bytes,
            title="Shogun",
            style={"placement": "bottom"},
        )
    assert out_429 is None
    assert mock_post_429.await_count == 1


@pytest.mark.asyncio
async def test_analyze_poster_style_extracts_motifs_line_layout_and_badges():
    from app.infrastructure.external import poster_localizer

    orig_bytes = _make_sample_jpeg(500, 750)
    mock_payload = {
        "placement": "bottom",
        "y_ratio": 0.72,
        "font_style": "bold",
        "primary_color": "#FACC15",
        "secondary_color": "#DC2626",
        "needs_backdrop": False,
        "title_box": [680, 120, 890, 860],
        "style_brief": "Tilted bold yellow sans top lines paired with red handwritten brush script bottom lines.",
        "title_motifs": "golden scales of justice emblem beside the title",
        "line_layout": ["YAXSHISI SOULGA", "QO'NG'IROQ QILING"],
        "badges_to_remove": ["bottom 8.6 AMC badge", "none"],
    }
    with patch.object(
        poster_localizer,
        "_call_gemini_vision_json",
        new=AsyncMock(return_value=mock_payload),
    ):
        style = await poster_localizer.analyze_poster_style(
            orig_bytes,
            title="Yaxshisi Soulga Qo'ng'iroq Qiling",
        )

    assert style["title_motifs"] == "golden scales of justice emblem beside the title"
    assert style["line_layout"] == ["YAXSHISI SOULGA", "QO'NG'IROQ QILING"]
    assert style["badges_to_remove"] == ["bottom 8.6 AMC badge"]


@pytest.mark.asyncio
async def test_edit_poster_with_cloudflare_prompt_preserves_motifs_and_removes_badges():
    import base64
    from unittest.mock import MagicMock
    from app.infrastructure.external import poster_localizer

    orig_bytes = _make_sample_jpeg(500, 750)
    png_b64 = base64.b64encode(_make_sample_jpeg(512, 768)).decode("ascii")
    resp_ok = MagicMock(status_code=200, headers={"content-type": "application/json"})
    resp_ok.json.return_value = {"result": {"image": png_b64}}

    rich_style = {
        "placement": "bottom",
        "style_brief": "Tilted yellow sans + red brush script",
        "title_motifs": "golden scales of justice emblem beside the title",
        "line_layout": ["YAXSHISI SOULGA", "QO'NG'IROQ QILING"],
        "badges_to_remove": ["bottom 8.6 AMC badge"],
    }
    with (
        patch.object(poster_localizer.settings, "CLOUDFLARE_ACCOUNT_ID", "cf_acc"),
        patch.object(poster_localizer.settings, "CLOUDFLARE_API_TOKEN", "cf_tok"),
        patch("httpx.AsyncClient.post", new=AsyncMock(return_value=resp_ok)) as mock_post,
        patch.object(poster_localizer, "verify_localized_poster_ocr", new=AsyncMock(return_value=True)),
    ):
        out = await poster_localizer.edit_poster_with_cloudflare(
            orig_bytes,
            title="Yaxshisi Soulga Qo'ng'iroq Qiling",
            style=rich_style,
        )

    assert out is not None
    sent_prompt = mock_post.await_args.kwargs["data"]["prompt"]
    assert "Exact word count: 4" in sent_prompt
    assert "golden scales of justice emblem beside the title" in sent_prompt
    assert "YAXSHISI SOULGA / QO'NG'IROQ QILING" in sent_prompt
    assert "bottom 8.6 AMC badge" in sent_prompt
    assert "apostrophe" in sent_prompt.lower()


@pytest.mark.asyncio
async def test_edit_poster_with_cloudflare_blocks_9b_by_default_and_retries_4b():
    import base64
    from unittest.mock import MagicMock
    from app.infrastructure.external import poster_localizer

    orig_bytes = _make_sample_jpeg(500, 750)
    png_b64 = base64.b64encode(_make_sample_jpeg(512, 768)).decode("ascii")
    resp_ok = MagicMock(status_code=200, headers={"content-type": "application/json"})
    resp_ok.json.return_value = {"result": {"image": png_b64}}

    assert getattr(poster_localizer.settings, "CLOUDFLARE_ENABLE_9B", False) is False
    with (
        patch.object(poster_localizer.settings, "CLOUDFLARE_ACCOUNT_ID", "cf_acc"),
        patch.object(poster_localizer.settings, "CLOUDFLARE_API_TOKEN", "cf_tok"),
        patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=[resp_ok, resp_ok])) as mock_post,
        patch.object(poster_localizer, "verify_localized_poster_ocr", new=AsyncMock(side_effect=[False, True])),
    ):
        out = await poster_localizer.edit_poster_with_cloudflare(
            orig_bytes,
            title="Taxtlar o'yini",
            style={"placement": "bottom"},
        )

    assert out is not None
    assert mock_post.await_count == 2
    assert all(call.args[0].endswith("flux-2-klein-4b") for call in mock_post.await_args_list)


@pytest.mark.asyncio
async def test_tmdb_get_textless_poster_matches_reference_twin_and_rejects_unrelated():
    from app.infrastructure.external.tmdb_client import tmdb_client

    ref_img = Image.new("RGB", (92, 138), (30, 80, 140))
    ref_buf = io.BytesIO()
    ref_img.save(ref_buf, format="JPEG")
    ref_bytes = ref_buf.getvalue()

    twin_img = Image.new("RGB", (92, 138), (32, 82, 142))
    twin_buf = io.BytesIO()
    twin_img.save(twin_buf, format="JPEG")

    other_img = Image.new("RGB", (92, 138), (220, 40, 20))
    other_buf = io.BytesIO()
    other_img.save(other_buf, format="JPEG")

    payload = {
        "posters": [
            {"file_path": "/unrelated_high_vote.jpg", "iso_639_1": None, "vote_average": 10.0, "width": 1000, "height": 1500},
            {"file_path": "/exact_twin.jpg", "iso_639_1": None, "vote_average": 1.0, "width": 1000, "height": 1500},
        ]
    }

    async def fake_get(url, *args, **kwargs):
        from unittest.mock import MagicMock
        r = MagicMock(status_code=200)
        r.content = twin_buf.getvalue() if "exact_twin" in url else other_buf.getvalue()
        return r

    with (
        patch("app.infrastructure.external.tmdb_client.get_cache", new=AsyncMock(return_value=None)),
        patch("app.infrastructure.external.tmdb_client.set_cache", new=AsyncMock(return_value=True)),
        patch.object(tmdb_client, "_request_with_retry", new=AsyncMock(return_value=payload)),
        patch("httpx.AsyncClient.get", side_effect=fake_get),
    ):
        url = await tmdb_client.get_textless_poster(
            tmdb_id=671,
            content_type="movie",
            reference_bytes=ref_bytes,
            placement="top",
        )
    assert url == "https://image.tmdb.org/t/p/w500/exact_twin.jpg"


@pytest.mark.asyncio
async def test_localize_poster_cleans_mislabeled_tmdb_textless_poster():
    from app.infrastructure.external import poster_localizer

    mislabeled_bytes = _make_sample_jpeg(500, 750, color=(20, 15, 15))
    with (
        patch.object(poster_localizer.settings, "CLOUDFLARE_ACCOUNT_ID", ""),
        patch.object(poster_localizer.settings, "CLOUDFLARE_API_TOKEN", ""),
        patch.object(
            poster_localizer.tmdb_client,
            "get_textless_poster",
            new=AsyncMock(return_value="https://image.tmdb.org/t/p/w500/mislabeled_siccin.jpg"),
        ),
        patch.object(poster_localizer, "_download_image_bytes", new=AsyncMock(return_value=mislabeled_bytes)),
        patch.object(
            poster_localizer,
            "analyze_poster_style",
            new=AsyncMock(
                return_value={
                    "placement": "bottom",
                    "y_ratio": 0.78,
                    "font_style": "serif",
                    "bevel_style": "chiseled",
                    "primary_color": "#D4CBB8",
                    "secondary_color": "#8E8472",
                    "accent_color": "#DC2626",
                    "needs_backdrop": False,
                    "title_box": [780, 180, 910, 820],
                    "extra_boxes": [[20, 40, 65, 960]],
                }
            ),
        ),
        patch.object(poster_localizer, "render_uzbek_title_on_poster", return_value=b"clean-sijjin") as mock_render,
        patch.object(
            poster_localizer,
            "upload_poster_to_telegram",
            new=AsyncMock(return_value="https://api.example.com/api/v1/posters/tg/AgAC_SIJJIN8"),
        ),
    ):
        url = await poster_localizer.localize_poster_and_upload(
            title="Sijjin 8",
            tmdb_id=1315706,
            content_type="movie",
        )

    assert url == "https://api.example.com/api/v1/posters/tg/AgAC_SIJJIN8"
    assert mock_render.call_args.kwargs["remove_existing_text"] is True


def test_render_v5_gothic_chiseled_rim_and_accent_number():
    from app.infrastructure.external.poster_localizer import render_uzbek_title_on_poster

    raw_bytes = _make_sample_jpeg(500, 750, color=(10, 12, 18))
    out_bytes = render_uzbek_title_on_poster(
        image_bytes=raw_bytes,
        title="Sijjin 8",
        style={
            "placement": "bottom",
            "y_ratio": 0.79,
            "font_style": "gothic",
            "bevel_style": "chiseled",
            "primary_color": "#D9D2C5",
            "secondary_color": "#7D7465",
            "accent_color": "#DC2626",
            "rim_color": "#1A1410",
            "needs_backdrop": False,
            "title_box": [790, 180, 910, 820],
        },
        remove_existing_text=True,
    )
    out_img = Image.open(io.BytesIO(out_bytes))
    assert out_img.size == (500, 750)
    # Check red pixels exist on the right side for the '8' accent color
    right_band = [out_img.getpixel((x, y)) for x in range(280, 430, 3) for y in range(580, 690, 3)]
    assert any(r > 160 and g < 70 and b < 70 for (r, g, b) in right_band)


def test_v6_letter_spacing_and_sleek_box_height():
    from app.infrastructure.external.poster_localizer import _build_main_title_mask

    mask_tight, *_ = _build_main_title_mask(
        1000, 1500, "SHOGUN", "epic", [910, 180, 975, 920], 910, False, letter_spacing="tight", font_weight="regular"
    )
    mask_wide, _, _, tw_wide, th_wide, _ = _build_main_title_mask(
        1000, 1500, "SHOGUN", "epic", [910, 180, 975, 920], 910, False, letter_spacing="ultra_wide", font_weight="regular"
    )
    bbox_tight = mask_tight.getbbox()
    bbox_wide = mask_wide.getbbox()
    assert bbox_tight is not None and bbox_wide is not None
    # Ultra-wide tracking spans noticeably wider while staying sleek inside ~6.5% height box (not inflated to 8%+)
    assert (bbox_wide[2] - bbox_wide[0]) > (bbox_tight[2] - bbox_tight[0]) * 1.15
    assert th_wide <= int(1500 * 0.068)


def test_v6_skips_similar_rim_and_preserves_rich_metallic_purple():
    from app.infrastructure.external.poster_localizer import _should_apply_rim, render_uzbek_title_on_poster

    assert _should_apply_rim((243, 228, 196), (209, 194, 151), (179, 159, 113)) is False
    assert _should_apply_rim((216, 172, 74), (106, 76, 230), (41, 21, 115)) is True

    raw_bytes = _make_sample_jpeg(500, 750, color=(8, 8, 14))
    out_bytes = render_uzbek_title_on_poster(
        image_bytes=raw_bytes,
        title="Qasoskorlar: Intiho",
        style={
            "placement": "bottom",
            "y_ratio": 0.74,
            "font_style": "blockbuster",
            "bevel_style": "metallic",
            "primary_color": "#6A4CE6",
            "secondary_color": "#291573",
            "rim_color": "#D8AC4A",
            "needs_backdrop": False,
            "title_box": [735, 160, 885, 840],
        },
        remove_existing_text=False,
    )
    out_img = Image.open(io.BytesIO(out_bytes))
    band = [out_img.getpixel((x, y)) for x in range(100, 400, 4) for y in range(555, 655, 4)]
    purple_pixels = [px for px in band if px[2] > 110 and px[2] > px[1] + 35 and px[0] < 160]
    assert len(purple_pixels) > 25, "Rich royal purple must not wash out into pastel grey/blue"


def test_v6_line_layout_splits_subtitle_without_colon_and_preserves_high_y_ratio():
    from app.infrastructure.external.poster_localizer import _split_title_and_subtitle

    main, subs = _split_title_and_subtitle(
        "Qasoskorlar 4 Intiho",
        {"line_layout": ["QASOSKORLAR 4", "INTIHO"]},
    )
    assert main.upper() == "QASOSKORLAR 4"
    assert subs == ["INTIHO"]

    # Even if LLM line_layout omits the split, `<Title> <Num> <Subtitle>` splits cleanly
    main_det, subs_det = _split_title_and_subtitle(
        "Qasoskorlar 4 Intiho",
        {"line_layout": ["QASOSKORLAR 4 INTIHO"]},
    )
    assert main_det.upper() == "QASOSKORLAR 4"
    assert subs_det == ["INTIHO"]


@pytest.mark.asyncio
async def test_v6_analyze_poster_style_clears_title_box_when_no_visible_title():
    from app.infrastructure.external import poster_localizer

    mock_json = {
        "has_visible_title": False,
        "placement": "bottom",
        "y_ratio": 0.85,
        "font_style": "epic",
        "title_box": [850, 120, 950, 880],
    }
    with patch.object(
        poster_localizer, "_call_gemini_vision_json", new=AsyncMock(return_value=mock_json)
    ):
        st = await poster_localizer.analyze_poster_style(_make_sample_jpeg(500, 750), "Shogun")
    assert st["title_box"] is None


@pytest.mark.asyncio
async def test_verify_ocr_rejects_cyrillic_or_mismatched_detected_title():
    from app.infrastructure.external import poster_localizer

    cyrillic_resp = {
        "detected_title": "ШОГУН",
        "spelling_exact": True,
        "no_duplicate_words": True,
        "scene_intact": True,
    }
    with patch.object(
        poster_localizer, "_call_gemini_vision_json", new=AsyncMock(return_value=cyrillic_resp)
    ):
        ok = await poster_localizer.verify_localized_poster_ocr(_make_sample_jpeg(100, 150), "Shogun")
    assert ok is False

    latin_resp = {
        "detected_title": "SHOGUN",
        "latin_script": True,
        "spelling_exact": True,
        "no_duplicate_words": True,
        "scene_intact": True,
    }
    with patch.object(
        poster_localizer, "_call_gemini_vision_json", new=AsyncMock(return_value=latin_resp)
    ):
        ok_latin = await poster_localizer.verify_localized_poster_ocr(_make_sample_jpeg(100, 150), "Shogun")
    assert ok_latin is True


def test_v7_force_center_and_box_fill_tracking():
    from app.infrastructure.external.poster_localizer import _build_main_title_mask

    _, x_sh, _, tw_sh, _, _ = _build_main_title_mask(
        1000,
        1500,
        "SHOGUN",
        "epic",
        [910, 196, 975, 924],
        910,
        False,
        letter_spacing="ultra_wide",
        font_weight="regular",
        force_center=True,
    )
    center_x = x_sh + tw_sh / 2
    assert abs(center_x - 500) <= 6

    _, _, _, tw_inst, th_inst, _ = _build_main_title_mask(
        1000,
        1500,
        "INSTITUT",
        "modern",
        [765, 64, 842, 938],
        765,
        False,
        letter_spacing="wide",
        font_weight="regular",
        force_center=True,
    )
    assert tw_inst >= 700, "Wide-tracked short title must expand tracking to fill wide title_box"
    assert th_inst <= 125


def test_v7_italic_shear_and_cloudflare_scene_guard():
    import numpy as np
    from app.infrastructure.external.poster_localizer import (
        _build_main_title_mask,
        _is_scene_preserved_outside_title,
    )

    mask_it, _, y_it, _, th_it, _ = _build_main_title_mask(
        1000,
        1500,
        "IIII",
        "blockbuster",
        [735, 100, 890, 900],
        735,
        False,
        is_italic=True,
    )
    arr = np.asarray(mask_it)
    top_xs = np.where(arr[y_it : y_it + max(4, th_it // 4), :] > 128)[1]
    bot_xs = np.where(arr[y_it + (th_it * 3) // 4 : y_it + th_it, :] > 128)[1]
    assert len(top_xs) > 0 and len(bot_xs) > 0
    assert float(top_xs.mean()) > float(bot_xs.mean()) + 4.0

    orig = _make_sample_jpeg(200, 300, color=(20, 40, 80))
    same = _make_sample_jpeg(200, 300, color=(20, 40, 80))
    warped = _make_sample_jpeg(200, 300, color=(150, 90, 30))
    assert _is_scene_preserved_outside_title(orig, same, [750, 100, 900, 900]) is True
    assert _is_scene_preserved_outside_title(orig, warped, [750, 100, 900, 900]) is False


def test_v7_normalizes_uzbek_unicode_apostrophes_to_ascii():
    from app.infrastructure.external.poster_localizer import _sanitize_font_text

    assert _sanitize_font_text("Taxtlar o\u02bbyini") == "Taxtlar o'yini"
    assert _sanitize_font_text("So\u2018nggi o\u02bcg\u2019ri") == "So'nggi o'g'ri"


@pytest.mark.asyncio
async def test_verify_ocr_fails_closed_when_empty_or_none():
    from app.infrastructure.external import poster_localizer

    with patch.object(poster_localizer, "_call_gemini_vision_json", new=AsyncMock(return_value=None)):
        assert await poster_localizer.verify_localized_poster_ocr(_make_sample_jpeg(100, 150), "Taxtlar o'yini") is False
    with patch.object(
        poster_localizer,
        "_call_gemini_vision_json",
        new=AsyncMock(return_value={"detected_title": "", "spelling_exact": True}),
    ):
        assert await poster_localizer.verify_localized_poster_ocr(_make_sample_jpeg(100, 150), "Taxtlar o'yini") is False


def test_v8_clean_display_title_and_stacked_equal_multiline():
    from app.infrastructure.external.poster_localizer import (
        _build_main_title_mask,
        _clean_poster_display_title,
        _split_title_and_subtitle,
    )

    assert _clean_poster_display_title("Yakkaxon daraja oshirish (Solo Leveling)") == "Yakkaxon daraja oshirish"
    main, subs = _split_title_and_subtitle(
        "Mashaqqatlar sari",
        {"title_stack_mode": "stacked_equal", "line_layout": ["MASHAQQATLAR", "SARI"]},
    )
    assert main == "MASHAQQATLAR\nSARI"
    assert subs == []

    mask_hi, _, _, tw, th, rstr = _build_main_title_mask(
        1000, 1500, main, "modern", [670, 220, 900, 780], 502, False
    )
    assert "\n" in rstr
    assert mask_hi.getbbox() is not None and th >= 140


def test_v8_stroke_inpaint_preserves_background_between_letters():
    import numpy as np
    from PIL import ImageDraw
    from app.infrastructure.external.poster_localizer import _inpaint_boxes

    # Textured blue-green background with crisp white letters inside a huge box [400..800]
    img = Image.new("RGB", (400, 600), (18, 88, 128))
    arr = np.asarray(img).copy()
    arr[250:480, 30:370, 1] += 25
    img = Image.fromarray(arr)
    before = np.asarray(img).copy()
    draw = ImageDraw.Draw(img)
    draw.text((80, 310), "SEAL", fill=(255, 255, 255))

    cleaned = _inpaint_boxes(img, [[400, 50, 800, 950]])
    after = np.asarray(cleaned)
    roi_before = before[245:475, 25:375]
    roi_after = after[245:475, 25:375]
    preserved_ratio = float(np.mean(np.max(np.abs(roi_before.astype(int) - roi_after.astype(int)), axis=2) <= 4))
    assert preserved_ratio >= 0.45, "Stroke-masked inpaint must not destroy intact background into an X smear"


@pytest.mark.asyncio
async def test_v8_cleans_mislabeled_textless_even_when_manual_url_present():
    from app.infrastructure.external import poster_localizer

    orig_bytes = _make_sample_jpeg(500, 750, color=(40, 20, 20))
    mislabeled_tl_bytes = _make_sample_jpeg(500, 750, color=(20, 15, 15))
    orig_style = {
        "placement": "bottom",
        "y_ratio": 0.75,
        "font_style": "gothic",
        "bevel_style": "chiseled",
        "primary_color": "#D4CBB8",
        "secondary_color": "#8E8472",
        "title_box": [720, 140, 890, 860],
        "extra_boxes": [],
    }

    async def fake_dl(url):
        return mislabeled_tl_bytes if "null_with_text" in url else orig_bytes

    with (
        patch.object(poster_localizer.settings, "CLOUDFLARE_ACCOUNT_ID", ""),
        patch.object(poster_localizer.settings, "CLOUDFLARE_API_TOKEN", ""),
        patch.object(
            poster_localizer.tmdb_client,
            "get_textless_poster",
            new=AsyncMock(return_value="https://image.tmdb.org/t/p/w500/null_with_text.jpg"),
        ),
        patch.object(poster_localizer, "_download_image_bytes", side_effect=fake_dl),
        patch.object(poster_localizer, "analyze_poster_style", new=AsyncMock(return_value=orig_style)),
        patch.object(
            poster_localizer,
            "_detect_residual_text_boxes",
            new=AsyncMock(return_value=[[700, 150, 910, 850], [10, 50, 70, 950]]),
        ),
        patch.object(poster_localizer, "render_uzbek_title_on_poster", return_value=b"cleaned") as mock_render,
        patch.object(
            poster_localizer,
            "upload_poster_to_telegram",
            new=AsyncMock(return_value="https://api.example.com/api/v1/posters/tg/AgAC_CLEANED"),
        ),
    ):
        url = await poster_localizer.localize_poster_and_upload(
            title="Sijjin 8",
            tmdb_id=1315706,
            content_type="movie",
            manual_poster_url="https://image.tmdb.org/t/p/w500/orig_tr.jpg",
        )

    assert url == "https://api.example.com/api/v1/posters/tg/AgAC_CLEANED"
    assert mock_render.call_args.kwargs["remove_existing_text"] is True
    assert [700, 150, 910, 850] in mock_render.call_args.kwargs["style"]["extra_boxes"]
    assert [10, 50, 70, 950] in mock_render.call_args.kwargs["style"]["extra_boxes"]


@pytest.mark.asyncio
async def test_v8_giant_cartoon_logo_falls_back_to_clean_tmdb_art():
    from app.infrastructure.external import poster_localizer

    orig_bytes = _make_sample_jpeg(500, 750, color=(20, 80, 120))
    clean_alt_bytes = _make_sample_jpeg(500, 750, color=(90, 170, 220))
    orig_style = {
        "placement": "bottom",
        "y_ratio": 0.43,
        "font_style": "cartoon",
        "bevel_style": "metallic",
        "primary_color": "#FFFFFF",
        "secondary_color": "#FF33CC",
        "rim_color": "#2A0860",
        "title_stack_mode": "stacked_equal",
        "line_layout": ["SUV MUSHUKLARI", "JAMOASI"],
        "title_box": [430, 40, 780, 960],
        "extra_boxes": [],
    }
    alt_space_style = {
        **orig_style,
        "placement": "top",
        "y_ratio": 0.06,
        "title_box": None,
        "needs_backdrop": False,
    }

    async def fake_dl(url):
        return clean_alt_bytes if "clean_alt" in url else orig_bytes

    with (
        patch.object(poster_localizer.settings, "CLOUDFLARE_ACCOUNT_ID", ""),
        patch.object(poster_localizer.settings, "CLOUDFLARE_API_TOKEN", ""),
        patch.object(
            poster_localizer.tmdb_client,
            "get_textless_poster",
            new=AsyncMock(side_effect=[None, "https://image.tmdb.org/t/p/w500/clean_alt.jpg"]),
        ) as mock_tl,
        patch.object(poster_localizer, "_download_image_bytes", side_effect=fake_dl),
        patch.object(poster_localizer, "analyze_poster_style", new=AsyncMock(side_effect=[orig_style, alt_space_style])),
        patch.object(poster_localizer, "_detect_residual_text_boxes", new=AsyncMock(return_value=[])),
        patch.object(poster_localizer, "render_uzbek_title_on_poster", return_value=b"rendered-alt") as mock_render,
        patch.object(
            poster_localizer,
            "upload_poster_to_telegram",
            new=AsyncMock(return_value="https://api.example.com/api/v1/posters/tg/AgAC_SEAL_CLEAN"),
        ),
    ):
        url = await poster_localizer.localize_poster_and_upload(
            title="Suv mushuklari jamoasi",
            tmdb_id=823610,
            content_type="movie",
            manual_poster_url="https://image.tmdb.org/t/p/w500/orig_seal.jpg",
        )

    assert url == "https://api.example.com/api/v1/posters/tg/AgAC_SEAL_CLEAN"
    assert mock_tl.await_count == 2
    assert mock_tl.await_args_list[1].kwargs["reference_bytes"] is None
    assert mock_render.call_args.kwargs["image_bytes"] == clean_alt_bytes
    assert mock_render.call_args.kwargs["remove_existing_text"] is False
    assert mock_render.call_args.kwargs["style"]["placement"] == "top"


def test_v9_vertical_rotated_title_mask():
    from app.infrastructure.external.poster_localizer import _build_main_title_mask

    mask_hi, x_hi, y_hi, tw, th, _ = _build_main_title_mask(
        1000, 1500, "LEGION", "modern", [37, 44, 574, 157], 37, True, letter_spacing="wide", force_center=False
    )
    # Tall narrow box [37..574, 44..157] must render vertically down the left edge (th > tw * 2)
    assert th > tw * 2
    assert x_hi < 200
    assert mask_hi.getbbox() is not None


def test_v9_wraps_long_single_line_title_for_readability():
    from app.infrastructure.external.poster_localizer import _split_title_and_subtitle

    main, subs = _split_title_and_subtitle(
        "Yakkaxon daraja oshirish (Solo Leveling)",
        {"title_stack_mode": "single", "title_box": [850, 100, 910, 900]},
    )
    assert "\n" in main
    assert main == "YAKKAXON\nDARAJA OSHIRISH"
    assert subs == []


def test_v9_periodic_tile_renders_green_element_squares():
    from app.infrastructure.external.poster_localizer import render_uzbek_title_on_poster

    raw_bytes = _make_sample_jpeg(500, 750, color=(15, 22, 12))
    out_bytes = render_uzbek_title_on_poster(
        image_bytes=raw_bytes,
        title="Mashaqqatlar sari",
        style={
            "placement": "bottom",
            "y_ratio": 0.68,
            "font_style": "modern",
            "bevel_style": "flat",
            "primary_color": "#FFFFFF",
            "secondary_color": "#E5EFE8",
            "title_stack_mode": "stacked_equal",
            "badge_motif": "periodic_tile",
            "line_layout": ["MASHAQQATLAR", "SARI"],
            "title_box": [680, 230, 920, 770],
            "needs_backdrop": False,
        },
        remove_existing_text=False,
    )
    out_img = Image.open(io.BytesIO(out_bytes))
    band = [out_img.getpixel((x, y)) for x in range(80, 380, 3) for y in range(500, 700, 3)]
    emerald_pixels = [px for px in band if px[1] > px[0] + 25 and px[1] > px[2] + 15 and px[1] >= 70]
    assert len(emerald_pixels) > 30, "Periodic tile motif must draw emerald green chemical squares"


def test_spray_stencil_renders_upright_with_bottom_drips_only():
    from app.infrastructure.external.poster_localizer import render_uzbek_title_on_poster

    raw_bytes = _make_sample_jpeg(500, 750, color=(20, 32, 38))
    out_bytes = render_uzbek_title_on_poster(
        image_bytes=raw_bytes,
        title="Yigitlar",
        style={
            "placement": "bottom",
            "y_ratio": 0.612,
            "font_style": "blockbuster",
            "font_weight": "heavy",
            "letter_spacing": "tight",
            "title_stack_mode": "stacked_equal",
            "is_italic": False,
            "bevel_style": "flat",
            "texture_style": "weathered",
            "primary_color": "#F0F0F0",
            "secondary_color": "#D0D0D0",
            "needs_backdrop": False,
            "title_box": [612, 98, 924, 888],
            "style_brief": "Heavy stencil spray-painted lettering with dripping paint.",
            "title_motifs": "Spray-paint drips extending from the bottom edges.",
        },
        remove_existing_text=False,
    )
    out_img = Image.open(io.BytesIO(out_bytes)).convert("RGB")
    arr = np.asarray(out_img)
    white = (arr[:, :, 0] > 200) & (arr[:, :, 1] > 200) & (arr[:, :, 2] > 200)
    ys, xs = np.where(white)
    assert len(xs) > 500
    # Lowered anchor sits strictly below 65% height (avoiding character boots above) and centered horizontally
    assert int(ys.min()) >= int(750 * 0.65)
    assert abs(((xs.min() + xs.max()) / 2.0) - 250.0) <= 4.0


@pytest.mark.asyncio
async def test_quality_gate_blocks_low_score_poster_before_upload(monkeypatch):
    from app.infrastructure.external import poster_localizer

    uploaded_calls = []

    async def fake_upload(**kwargs):
        uploaded_calls.append(kwargs)
        return "https://kinochi.example/tg/should_not_upload"

    async def fake_download(url):
        return _make_sample_jpeg(400, 600, color=(25, 35, 55))

    async def fake_analyze(img, title):
        return {"placement": "bottom", "y_ratio": 0.78, "font_style": "modern", "title_box": [780, 100, 900, 900]}

    async def fake_textless(*args, **kwargs):
        return None

    async def fake_vision_json(prompt, image_bytes, max_tokens=256):
        return {"score": 4, "overlap_face": True, "broken_text": False, "reason": "Overlaps character face"}

    monkeypatch.setattr(poster_localizer.tmdb_client, "get_textless_poster", fake_textless)
    monkeypatch.setattr(poster_localizer, "_download_image_bytes", fake_download)
    monkeypatch.setattr(poster_localizer, "analyze_poster_style", fake_analyze)
    monkeypatch.setattr(poster_localizer, "upload_poster_to_telegram", fake_upload)
    monkeypatch.setattr(poster_localizer, "_call_gemini_vision_json", fake_vision_json)
    monkeypatch.setattr(poster_localizer.settings, "CLOUDFLARE_ACCOUNT_ID", "")

    res = await poster_localizer.localize_poster_and_upload(
        title="Test Film",
        tmdb_id=999,
        content_type="movie",
        manual_poster_url="https://image.tmdb.org/t/p/w500/sample.jpg",
    )
    assert res is None
    assert uploaded_calls == []


def test_split_around_center_leaves_middle_subject_unobstructed():
    from app.infrastructure.external.poster_localizer import render_uzbek_title_on_poster

    raw_bytes = _make_sample_jpeg(500, 750, color=(45, 35, 65))
    out_bytes = render_uzbek_title_on_poster(
        image_bytes=raw_bytes,
        title="Jodugarlar Jangi",
        style={
            "placement": "bottom",
            "layout_mode": "split_around_center",
            "font_style": "gothic",
            "bevel_style": "flat",
            "primary_color": "#111111",
            "secondary_color": "#111111",
            "rim_color": "#EAE068",
            "title_box": [430, 100, 535, 900],
            "needs_backdrop": False,
        },
        remove_existing_text=False,
    )
    out_img = Image.open(io.BytesIO(out_bytes)).convert("RGB")
    arr = np.asarray(out_img)
    # Central column (x=220..280) at y=300..420 must stay clean (no yellow stroke pixels in center gap)
    center_band = arr[300:420, 225:275]
    yellow_center = (center_band[:, :, 0] > 180) & (center_band[:, :, 1] > 170) & (center_band[:, :, 2] < 130)
    assert int(np.sum(yellow_center)) == 0
    # Left and right flanking zones must contain yellow outline pixels
    left_band = arr[300:420, 30:195]
    right_band = arr[300:420, 305:470]
    assert int(np.sum((left_band[:, :, 0] > 180) & (left_band[:, :, 1] > 170) & (left_band[:, :, 2] < 130))) > 25
    assert int(np.sum((right_band[:, :, 0] > 180) & (right_band[:, :, 1] > 170) & (right_band[:, :, 2] < 130))) > 25


@pytest.mark.asyncio
async def test_emblem_inner_skips_textless_swap_to_preserve_emblem(monkeypatch):
    from app.infrastructure.external import poster_localizer

    textless_called = []

    async def fake_textless(*args, **kwargs):
        textless_called.append(True)
        return "https://image.tmdb.org/t/p/w500/empty_bg.jpg"

    async def fake_download(url):
        return _make_sample_jpeg(400, 600, color=(200, 30, 30))

    async def fake_analyze(img, title):
        return {
            "placement": "bottom",
            "layout_mode": "emblem_inner",
            "font_style": "ornate",
            "bevel_style": "flat",
            "primary_color": "#111111",
            "title_box": [560, 330, 760, 670],
            "needs_backdrop": False,
        }

    async def fake_upload(**kwargs):
        return "https://kinochi.example/tg/emblem_ok"

    async def fake_quality(img_bytes, title):
        return True

    monkeypatch.setattr(poster_localizer.tmdb_client, "get_textless_poster", fake_textless)
    monkeypatch.setattr(poster_localizer, "_download_image_bytes", fake_download)
    monkeypatch.setattr(poster_localizer, "analyze_poster_style", fake_analyze)
    monkeypatch.setattr(poster_localizer, "upload_poster_to_telegram", fake_upload)
    monkeypatch.setattr(poster_localizer, "_verify_rendered_poster_quality", fake_quality)
    monkeypatch.setattr(poster_localizer.settings, "CLOUDFLARE_ACCOUNT_ID", "")

    res = await poster_localizer.localize_poster_and_upload(
        title="Iblislar qotili",
        tmdb_id=85937,
        content_type="tv",
        manual_poster_url="https://image.tmdb.org/t/p/w500/emblem_orig.jpg",
    )
    assert res == "https://kinochi.example/tg/emblem_ok"
    assert textless_called == [], "emblem_inner must keep original poster emblem instead of fetching textless"





@pytest.mark.asyncio
async def test_v9_vertical_title_does_not_trigger_giant_logo_fallback(monkeypatch):
    from app.infrastructure.external import poster_localizer

    calls = []

    async def fake_get_textless(tmdb_id, content_type="movie", reference_bytes=None, placement="bottom"):
        calls.append(reference_bytes is not None)
        return None

    orig_bytes = _make_sample_jpeg(400, 600, color=(150, 240, 190))

    async def fake_download(url):
        return orig_bytes

    async def fake_analyze(img_bytes, title):
        return {
            "placement": "top",
            "y_ratio": 0.03,
            "font_style": "modern",
            "bevel_style": "flat",
            "title_box": [36, 44, 574, 157],
            "needs_backdrop": False,
        }

    uploaded = {}

    async def fake_upload(**kwargs):
        uploaded["bytes"] = kwargs["photo_bytes"]
        return "https://kinochi.example/api/v1/posters/tg/vertical_ok"

    monkeypatch.setattr(poster_localizer.tmdb_client, "get_textless_poster", fake_get_textless)
    monkeypatch.setattr(poster_localizer, "_download_image_bytes", fake_download)
    monkeypatch.setattr(poster_localizer, "analyze_poster_style", fake_analyze)
    monkeypatch.setattr(poster_localizer, "upload_poster_to_telegram", fake_upload)
    monkeypatch.setattr(poster_localizer.settings, "CLOUDFLARE_ACCOUNT_ID", "")

    res = await poster_localizer.localize_poster_and_upload(
        title="Legion",
        tmdb_id=67195,
        content_type="tv",
        manual_poster_url="https://image.tmdb.org/t/p/w500/xhJtYVTsdXQCIlB5hAXkMCPUG9y.jpg",
    )
    assert res == "https://kinochi.example/api/v1/posters/tg/vertical_ok"
    assert calls == [True], "Tall vertical title must keep original poster and skip unreferenced alt fallback"


def test_periodic_tile_line2_is_centered_symmetrically():
    from app.infrastructure.external.poster_localizer import render_uzbek_title_on_poster

    raw_bytes = _make_sample_jpeg(500, 750, color=(15, 22, 12))
    out_bytes = render_uzbek_title_on_poster(
        image_bytes=raw_bytes,
        title="Mashaqqatlar sari",
        style={
            "placement": "bottom",
            "y_ratio": 0.68,
            "font_style": "modern",
            "bevel_style": "flat",
            "primary_color": "#FFFFFF",
            "secondary_color": "#E5EFE8",
            "title_stack_mode": "stacked_equal",
            "badge_motif": "periodic_tile",
            "line_layout": ["MASHAQQATLAR", "SARI"],
            "title_box": [680, 230, 920, 770],
            "needs_backdrop": False,
        },
        remove_existing_text=False,
    )
    out_img = Image.open(io.BytesIO(out_bytes)).convert("RGB")
    arr = np.asarray(out_img)
    white = (arr[:, :, 0] > 210) & (arr[:, :, 1] > 210) & (arr[:, :, 2] > 210)
    ys, xs = np.where(white)
    mid_y = (ys.min() + ys.max()) // 2
    bot_xs = xs[ys >= mid_y + 5]
    assert len(bot_xs) > 10
    center_err = abs(((bot_xs.min() + bot_xs.max()) / 2.0) - 250.0)
    assert center_err <= 8.0, f"Periodic tile line 2 shifted off-center by {center_err:.1f}px"


def test_near_center_jittered_box_snaps_to_exact_horizontal_center():
    from app.infrastructure.external.poster_localizer import _build_main_title_mask

    # Jittered box [820, 120, 910, 740] has box_center_norm = 0.43 (within 0.14 tolerance)
    mask_hi, x_hi, _y_hi, target_w, _target_h, _ = _build_main_title_mask(
        1000,
        1500,
        "YAKKAXON\nDARAJA OSHIRISH",
        "modern",
        [820, 120, 910, 740],
        1230,
        False,
        force_center=False,
    )
    bbox = mask_hi.getbbox()
    assert bbox is not None
    actual_center = (bbox[0] + bbox[2]) / 2.0
    assert abs(actual_center - 500.0) <= 2.0


