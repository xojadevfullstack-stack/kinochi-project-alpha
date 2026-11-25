import subprocess
from unittest.mock import AsyncMock, patch

import pytest

from scraper.smm_clipper import resolve_ffmpeg_bin
from scraper.smm_scene_scorer import (
    parse_scene_vision_response,
    parse_volumedetect_output,
    select_best_scene_start,
)


def test_parse_volumedetect_output_extracts_db():
    stderr = """
    [Parsed_volumedetect_0 @ 000] mean_volume: -19.4 dB
    [Parsed_volumedetect_0 @ 000] max_volume: -2.1 dB
    """
    mean_db, max_db = parse_volumedetect_output(stderr)
    assert mean_db == pytest.approx(-19.4)
    assert max_db == pytest.approx(-2.1)
    assert parse_volumedetect_output("no stats") == (-90.0, -90.0)


def test_parse_scene_vision_response_detects_ad_banner():
    raw = """```json
    {"is_clean": false, "has_ad_banner": true, "is_nsfw_or_gore": false,
     "is_credits": false, "excitement_score": 4, "reason": "Mostbet banner at bottom"}
    ```"""
    res = parse_scene_vision_response(raw)
    assert res["is_clean"] is False
    assert res["has_ad_banner"] is True
    assert res["excitement_score"] == 4

    fallback = parse_scene_vision_response("invalid garbage")
    assert fallback["is_clean"] is True


@pytest.mark.asyncio
async def test_select_best_scene_start_skips_dark_silent_intro(tmp_path):
    ffmpeg = resolve_ffmpeg_bin()
    src = tmp_path / "dark_then_bright.mp4"
    # 0-3s: black & silent; 3-7s: bright testsrc2 & 440Hz tone
    subprocess.run(
        [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", "color=c=black:s=640x360:d=3",
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo:d=3",
            "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=24:d=4",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=4",
            "-filter_complex", "[0:v][1:a][2:v][3:a]concat=n=2:v=1:a=1[v][a]",
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
            str(src),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    best = await select_best_scene_start(str(src), clip_duration=2.0, check_vision=False)
    assert best["start_sec"] >= 2.5
    assert best["mean_volume_db"] > -35.0


@pytest.mark.asyncio
async def test_select_best_scene_start_skips_vision_ad_banner(tmp_path):
    ffmpeg = resolve_ffmpeg_bin()
    src = tmp_path / "bright_all.mp4"
    subprocess.run(
        [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=24:d=6",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=6",
            "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
            str(src),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    side_effects = [
        {"is_clean": False, "has_ad_banner": True, "is_nsfw_or_gore": False, "is_credits": False, "excitement_score": 8, "reason": "Mostbet"},
        {"is_clean": True, "has_ad_banner": False, "is_nsfw_or_gore": False, "is_credits": False, "excitement_score": 8, "reason": "Clean action"},
    ]
    with patch("scraper.smm_scene_scorer.check_frames_for_ads_or_nsfw", new=AsyncMock(side_effect=side_effects)):
        best = await select_best_scene_start(str(src), clip_duration=2.0, check_vision=True)
        assert best["has_ad_banner"] is False
        assert best["reason"] == "Clean action"


def test_parse_scene_vision_response_clamps_dynamic_blur_boxes():
    raw = """```json
    {
      "is_clean": true,
      "has_ad_banner": false,
      "is_nsfw_or_gore": false,
      "is_credits": false,
      "excitement_score": 8,
      "blur_boxes": [
        {"x": 0.01, "y": 0.02, "w": 0.21, "h": 0.07, "kind": "watermark"},
        {"x": 0.85, "y": 0.90, "w": 0.40, "h": 0.25, "kind": "ad"},
        {"x": -0.5, "y": -0.5, "w": 0.01, "h": 0.01}
      ],
      "reason": "Asilmedia logo top-left"
    }
    ```"""
    res = parse_scene_vision_response(raw)
    assert res["vision_used"] is True
    boxes = res["blur_boxes"]
    assert len(boxes) == 2
    assert boxes[0]["x"] == pytest.approx(0.01)
    assert boxes[0]["w"] == pytest.approx(0.21)
    assert boxes[1]["x"] + boxes[1]["w"] <= 1.0
    assert boxes[1]["y"] + boxes[1]["h"] <= 1.0

    # Even if Gemini flags is_clean=false solely due to a watermark box, unsafe_scene is False so scene stays clean
    raw_wm_false = """{"is_clean": false, "has_ad_banner": false, "is_nsfw_or_gore": false, "is_credits": false,
      "blur_boxes": [{"x": 0.01, "y": 0.02, "w": 0.21, "h": 0.09, "kind": "watermark"}], "reason": "WM"}"""
    res_wm = parse_scene_vision_response(raw_wm_false)
    assert res_wm["is_clean"] is True
    assert len(res_wm["blur_boxes"]) == 1


@pytest.mark.asyncio
async def test_select_best_scene_start_uses_ffmpeg_frame_fallback_when_cv2_empty(tmp_path):
    ffmpeg = resolve_ffmpeg_bin()
    src = tmp_path / "fallback_src.mp4"
    subprocess.run(
        [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=24:d=4",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=4",
            "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
            str(src),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    seen_frames = []

    async def fake_vision(frames_b64, api_key=None):
        seen_frames.append(list(frames_b64))
        return {
            "is_clean": True, "has_ad_banner": False, "is_nsfw_or_gore": False,
            "is_credits": False, "excitement_score": 7, "blur_boxes": [], "vision_used": True, "reason": "OK",
        }

    with (
        patch("scraper.smm_scene_scorer._sample_window_visuals", return_value=(10.0, [])),
        patch("scraper.smm_scene_scorer.check_frames_for_ads_or_nsfw", side_effect=fake_vision),
    ):
        res = await select_best_scene_start(str(src), clip_duration=2.0, check_vision=True)

    assert res["vision_used"] is True
    assert len(seen_frames) >= 1 and len(seen_frames[0]) >= 1
