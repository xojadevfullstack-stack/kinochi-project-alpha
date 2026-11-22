import os
import subprocess
import pytest

from scraper.smm_clipper import (
    compute_clip_window,
    escape_drawtext,
    build_cinematic_filter_complex,
    find_mp4_chunk_offset_for_ratio,
    resolve_ffmpeg_bin,
    render_vertical_clip,
)


def test_compute_clip_window_avoids_intro_and_outro():
    start, dur = compute_clip_window(total_duration_sec=5400.0, duration_sec=45.0, ratio=0.35)
    assert start >= 5400.0 * 0.15
    assert start + dur <= 5400.0 * 0.85
    assert dur == 45.0


def test_compute_clip_window_explicit_start_and_short_video_clamp():
    start, dur = compute_clip_window(total_duration_sec=30.0, duration_sec=45.0, start_sec=10.0)
    assert start == 10.0
    assert dur == 20.0


def test_compute_clip_window_invalid_raises():
    with pytest.raises(ValueError):
        compute_clip_window(total_duration_sec=0.0, duration_sec=45.0)
    with pytest.raises(ValueError):
        compute_clip_window(total_duration_sec=120.0, duration_sec=0.0)
    with pytest.raises(ValueError):
        compute_clip_window(total_duration_sec=120.0, duration_sec=30.0, start_sec=-5.0)


def test_escape_drawtext_handles_colons_quotes_and_percent():
    escaped = escape_drawtext("Otamga: Qasida '2014' 100%")
    assert "\\:" in escaped
    assert "%%" in escaped
    assert "'" not in escaped or "\\'" in escaped


def test_build_cinematic_filter_complex_hides_movie_title_and_uses_mediaplusbot():
    vf, af = build_cinematic_filter_complex(
        title="Otamga qasida",
        movie_code="889",
        imdb_rating=8.4,
        year=2014,
        copyright_shield=True,
    )
    assert "scale=1080:1920" in vf
    assert "boxblur=" in vf
    assert "#E50914" in vf
    assert "889" in vf
    assert "8.4" in vf
    assert "OTAMGA" not in vf
    assert "Otamga" not in vf
    assert "2014" not in vf
    assert "Mediaplusbot" in vf or "MEDIAPLUSBOT" in vf
    assert "@MediaPlusOfficialBot" in vf
    assert "atempo=1.02" in af
    # Bottom CTA must stay above 9:16 Reels/Shorts/TikTok bottom danger zone
    import re
    box_m = re.search(r"drawbox=x=\d+:y=(\d+):", vf)
    bot_m = re.search(r"Telegram bot.*?y=(\d+):", vf)
    assert box_m and int(box_m.group(1)) <= 1400
    assert bot_m and int(bot_m.group(1)) <= 1540


def test_render_vertical_clip_creates_1080x1920_mp4(tmp_path):
    ffmpeg = resolve_ffmpeg_bin()
    src = tmp_path / "sample_16x9.mp4"
    out = tmp_path / "clip_9x16.mp4"

    # Generate 3-second synthetic 1280x720 video with sine audio
    subprocess.run(
        [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", "testsrc=duration=3:size=1280x720:rate=24",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
            "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
            str(src),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    result_path = render_vertical_clip(
        input_path=str(src),
        output_path=str(out),
        title="Otamga qasida",
        movie_code="889",
        start_sec=0.0,
        duration_sec=2.0,
        imdb_rating=8.4,
        year=2014,
    )
    assert os.path.exists(result_path)
    assert os.path.getsize(result_path) > 10_000

    import cv2
    cap = cv2.VideoCapture(result_path)
    assert cap.isOpened()
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    assert (width, height) == (1080, 1920)


def test_find_mp4_chunk_offset_for_ratio_parses_stco():
    import struct

    offsets = [1000, 2000, 5000, 9000, 15000]
    stco_box = b"\x00\x00\x00\x24stco\x00\x00\x00\x00" + struct.pack(">I", len(offsets)) + struct.pack(f">{len(offsets)}I", *offsets)
    fake_moov = b"\x00\x00\x00\x30moov" + stco_box
    assert find_mp4_chunk_offset_for_ratio(fake_moov, 0.0) == 1000
    assert find_mp4_chunk_offset_for_ratio(fake_moov, 0.4) == 5000
    assert find_mp4_chunk_offset_for_ratio(fake_moov, 0.8) == 15000
    assert find_mp4_chunk_offset_for_ratio(b"no moov here", 0.35) is None


def test_build_cinematic_filter_complex_adds_watermark_and_ad_blur():
    vf, _ = build_cinematic_filter_complex(
        movie_code="5064",
        blur_watermark=True,
        blur_bottom_ad=True,
    )
    assert "crop=iw*0.22:ih*0.14" in vf
    assert "crop=iw*0.56:ih*0.22" in vf
    assert vf.count("boxblur=") >= 3


def test_render_vertical_clip_with_watermark_and_ad_blur(tmp_path):
    ffmpeg = resolve_ffmpeg_bin()
    src = tmp_path / "sample_ad.mp4"
    out = tmp_path / "out_blurred.mp4"
    subprocess.run(
        [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", "testsrc2=duration=2:size=1280x720:rate=24",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
            "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
            str(src),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    res = render_vertical_clip(
        str(src), str(out), movie_code="5064",
        start_sec=0.0, duration_sec=1.5,
        blur_watermark=True, blur_bottom_ad=True,
    )
    assert os.path.exists(res) and os.path.getsize(res) > 10_000


def test_low_ram_720p_profile_builds_270x480_blur_and_renders_720x1280(tmp_path):
    vf, _ = build_cinematic_filter_complex(movie_code="5064", imdb_rating=7.5, low_ram=True)
    assert "scale=270:480" in vf
    assert "scale=720:1280" in vf
    assert "drawbox=x=80:y=912:w=560:h=78" in vf

    ffmpeg = resolve_ffmpeg_bin()
    src = tmp_path / "sample_lowram.mp4"
    out = tmp_path / "out_720p.mp4"
    subprocess.run(
        [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", "testsrc=duration=2:size=1280x720:rate=24",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
            "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
            str(src),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    res = render_vertical_clip(
        str(src), str(out), movie_code="5064",
        start_sec=0.0, duration_sec=1.5, low_ram=True,
    )
    import cv2
    cap = cv2.VideoCapture(res)
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    assert (w, h) == (720, 1280)
