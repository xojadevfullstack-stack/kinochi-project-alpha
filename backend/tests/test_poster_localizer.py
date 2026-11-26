"""Tests for Slice 2: TMDb textless poster lookup, Vision layout analysis, OpenCV cleanup, and Pillow render."""

import io
from unittest.mock import AsyncMock, patch
import pytest
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



