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


def test_dynamic_ai_blur_boxes_render_arbitrary_top_left_logo_safely(tmp_path):
    boxes = [{"x": 0.01, "y": 0.02, "w": 0.22, "h": 0.06, "kind": "watermark"}]
    vf, _ = build_cinematic_filter_complex(
        movie_code="3955",
        imdb_rating=8.1,
        low_ram=True,
        blur_watermark=True,
        blur_boxes=boxes,
    )
    assert "crop=iw*0.220:ih*0.060:iw*0.010:ih*0.020" in vf
    assert "crop=iw*0.22:ih*0.14:iw*0.77:ih*0.02" not in vf

    ffmpeg = resolve_ffmpeg_bin()
    src = tmp_path / "sample_topleft.mp4"
    out = tmp_path / "out_topleft_720p.mp4"
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
        str(src), str(out), movie_code="3955",
        start_sec=0.0, duration_sec=1.5, low_ram=True, blur_boxes=boxes,
    )
    assert os.path.exists(res) and os.path.getsize(res) > 10_000


def test_compute_sparse_chunk_mb_scales_for_large_1080p_movies():
    from scraper.smm_clipper import compute_sparse_chunk_mb

    # 1.75 GB 1080p ~94 min movie needs > 25 MB to cover 45s clip + 30s scan headroom
    scaled = compute_sparse_chunk_mb(
        total_size=1_754_000_000,
        total_duration=5636.0,
        clip_duration=45.0,
    )
    assert 45 <= scaled <= 65

    # Small / short 480p file respects safe minimum
    small = compute_sparse_chunk_mb(
        total_size=300_000_000,
        total_duration=5400.0,
        clip_duration=45.0,
    )
    assert small == 30


def test_compute_sparse_byte_range_covers_scan_plus_clip_tail_via_stco():
    import struct
    from scraper.smm_clipper import compute_sparse_byte_range

    # Synthetic moov stco with 100 entries spanning 0 .. 1.75 GB where dense tail jumps 55 MB across scan+clip
    offsets = [int(i * (1_754_000_000 / 100)) for i in range(100)]
    # Make index 36 (close to target+scan+clip) jump extra 20 MB to simulate VBR dense action scene
    for idx in range(36, 100):
        offsets[idx] += 20_000_000
    stco = b"stco\x00\x00\x00\x00" + struct.pack(">I", len(offsets)) + b"".join(struct.pack(">I", x) for x in offsets)

    mid_offset, mid_bytes = compute_sparse_byte_range(
        moov_source=stco,
        total_size=1_754_000_000,
        total_duration=5665.0,
        target_ratio=0.35,
    )
    assert mid_offset <= offsets[35]
    # Must cover past index 36 (+45s..90s VBR spike) with buffer
    assert mid_offset + mid_bytes >= offsets[36] + 1_000_000


def test_low_ram_decodes_input_once_caps_blur_zones_and_passes_timeout(monkeypatch, tmp_path):
    many_boxes = [
        {"x": 0.01, "y": 0.02, "w": 0.2, "h": 0.08, "kind": "watermark"},
        {"x": 0.77, "y": 0.02, "w": 0.2, "h": 0.08, "kind": "watermark"},
        {"x": 0.1, "y": 0.75, "w": 0.6, "h": 0.15, "kind": "ad"},
        {"x": 0.2, "y": 0.85, "w": 0.5, "h": 0.1, "kind": "ad"},
    ]
    vf, _ = build_cinematic_filter_complex(
        movie_code="3957",
        imdb_rating=4.3,
        low_ram=True,
        blur_watermark=True,
        blur_boxes=many_boxes,
    )
    assert vf.count("[0:v]") == 1
    assert "fps=24" in vf
    assert "split=2[fg0][bg_in]" in vf
    assert vf.count("boxblur=") <= 3

    captured = {}

    def _fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    render_vertical_clip(
        str(tmp_path / "in.mp4"),
        str(tmp_path / "out.mp4"),
        movie_code="3957",
        start_sec=0.0,
        duration_sec=10.0,
        low_ram=True,
    )
    assert "-preset" in captured["cmd"]
    assert captured["cmd"][captured["cmd"].index("-preset") + 1] == "ultrafast"
    assert captured["kwargs"].get("timeout", 0) >= 60


def test_render_vertical_clip_raises_clear_error_on_timeout(monkeypatch, tmp_path):
    def _timeout_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=kwargs.get("timeout", 240))

    monkeypatch.setattr(subprocess, "run", _timeout_run)
    with pytest.raises(RuntimeError, match="timed out"):
        render_vertical_clip(
            str(tmp_path / "in.mp4"),
            str(tmp_path / "out.mp4"),
            movie_code="3957",
            low_ram=True,
        )
