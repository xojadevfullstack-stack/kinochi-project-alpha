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
