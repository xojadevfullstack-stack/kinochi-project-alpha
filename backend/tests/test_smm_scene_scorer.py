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


@pytest.mark.asyncio
async def test_find_viral_scene_target_from_srt_stremio():
    from scraper.smm_scene_finder import find_viral_scene_target

    sample_srt = (
        "1\n00:02:10,000 --> 00:02:14,000\nQuiet breakfast talk.\n\n"
        "2\n00:53:40,000 --> 00:53:45,000\nBring me his head!\n\n"
        "3\n00:55:10,000 --> 00:55:15,000\nEnd credits music.\n"
    )
    mock_pick = {
        "start_sec": 3180,
        "peak_sec": 3222,
        "visual_cue": "Ned Stark kneeling at Baelor sept",
        "reason_uz": "Eng mashhur burilish sahnasi",
    }
    with (
        patch("scraper.smm_scene_finder.fetch_imdb_id", new=AsyncMock(return_value="tt0944947")),
        patch("scraper.smm_scene_finder.fetch_stremio_srt", new=AsyncMock(return_value=sample_srt)),
        patch("scraper.smm_scene_finder._ask_gemini_scene_timecode", new=AsyncMock(return_value=mock_pick)),
    ):
        target = await find_viral_scene_target(
            tmdb_id=1399,
            title="Game of Thrones",
            content_type="tv",
            season_number=1,
            episode_number=9,
        )

    assert target is not None
    assert target["peak_sec"] == 3222.0
    assert target["srt_end_sec"] == pytest.approx(3315.0)
    assert "Ned Stark" in target["visual_cue"]


@pytest.mark.asyncio
async def test_select_best_scene_start_compares_candidates_by_excitement_and_cue_match(tmp_path):
    ffmpeg = resolve_ffmpeg_bin()
    src = tmp_path / "compare_src.mp4"
    subprocess.run(
        [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=24:d=7",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=7",
            "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
            str(src),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Candidate 0 is clean but boring (excitement=3, cue_match=2); Candidate 1 is peak climax (excitement=9, cue_match=10)
    side_effects = [
        {"is_clean": True, "has_ad_banner": False, "is_nsfw_or_gore": False, "is_credits": False, "excitement_score": 3, "cue_match": 2, "blur_boxes": [], "vision_used": True, "reason": "Boring"},
        {"is_clean": True, "has_ad_banner": False, "is_nsfw_or_gore": False, "is_credits": False, "excitement_score": 9, "cue_match": 10, "blur_boxes": [], "vision_used": True, "reason": "Climax twist"},
        {"is_clean": True, "has_ad_banner": False, "is_nsfw_or_gore": False, "is_credits": False, "excitement_score": 4, "cue_match": 3, "blur_boxes": [], "vision_used": True, "reason": "Outro"},
    ]
    with patch("scraper.smm_scene_scorer.check_frames_for_ads_or_nsfw", new=AsyncMock(side_effect=side_effects)):
        res = await select_best_scene_start(
            str(src),
            clip_duration=2.0,
            check_vision=True,
            visual_cue="Dramatic betrayal",
            compare_candidates=3,
        )

    assert res["reason"] == "Climax twist"
    assert res["start_sec"] > 0.0


def test_measure_audio_db_enforces_timeout_and_recovers(tmp_path):
    from scraper.smm_scene_scorer import _measure_audio_db

    seen_kwargs = {}

    def fake_run(cmd, **kwargs):
        seen_kwargs.update(kwargs)
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=kwargs.get("timeout", 15))

    with patch("scraper.smm_scene_scorer.subprocess.run", side_effect=fake_run):
        mean_db, max_db = _measure_audio_db("ffmpeg", str(tmp_path / "x.mp4"), 100.0, 15.0)

    assert "timeout" in seen_kwargs and seen_kwargs["timeout"] <= 20
    assert (mean_db, max_db) == (-90.0, -90.0)


def test_parse_scene_vision_recovers_corner_box_from_reason_and_keeps_small_watermark():
    # Case 1: Model explicitly mentions bottom-right watermark in reason but forgot blur_boxes
    contradictory = (
        '{"is_clean": true, "has_ad_banner": false, "is_nsfw_or_gore": false, "is_credits": false, '
        '"excitement_score": 4, "blur_boxes": [], '
        '"reason": "Contains a watermark at the bottom right corner (Kinochilar) which can be blurred."}'
    )
    res1 = parse_scene_vision_response(contradictory)
    assert len(res1["blur_boxes"]) == 1
    b1 = res1["blur_boxes"][0]
    assert b1["x"] >= 0.75 and b1["y"] >= 0.78 and b1["x"] + b1["w"] >= 0.95

    # Case 2: Negated watermark phrase must NOT synthesize fake blur boxes
    clean_neg = '{"is_clean": true, "has_ad_banner": false, "blur_boxes": [], "reason": "Clean frame, no watermark or ads."}'
    assert parse_scene_vision_response(clean_neg)["blur_boxes"] == []

    # Case 3: Small 3% tall corner watermark on ultrawide 2.4:1 frame & tight bottom-right box pad inward cleanly
    tiny = '{"is_clean": true, "blur_boxes": [{"x": 0.86, "y": 0.92, "w": 0.12, "h": 0.032, "kind": "watermark"}], "reason": "WM"}'
    res3 = parse_scene_vision_response(tiny)
    assert len(res3["blur_boxes"]) == 1
    assert res3["blur_boxes"][0]["x"] <= 0.825
    assert res3["blur_boxes"][0]["y"] <= 0.885
    assert res3["blur_boxes"][0]["h"] >= 0.08


@pytest.mark.asyncio
async def test_select_best_scene_start_aggregates_watermark_boxes_across_candidates(tmp_path):
    ffmpeg = resolve_ffmpeg_bin()
    src = tmp_path / "agg_wm.mp4"
    subprocess.run(
        [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=24:d=7",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=7",
            "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
            str(src),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    wm_box = {"x": 0.82, "y": 0.85, "w": 0.17, "h": 0.12, "kind": "watermark"}
    side_effects = [
        {"is_clean": True, "has_ad_banner": False, "is_nsfw_or_gore": False, "is_credits": False, "excitement_score": 4, "cue_match": 4, "blur_boxes": [wm_box], "vision_used": True, "reason": "Bright corner"},
        {"is_clean": True, "has_ad_banner": False, "is_nsfw_or_gore": False, "is_credits": False, "excitement_score": 9, "cue_match": 9, "blur_boxes": [], "vision_used": True, "reason": "Dark winner"},
        {"is_clean": True, "has_ad_banner": False, "is_nsfw_or_gore": False, "is_credits": False, "excitement_score": 5, "cue_match": 5, "blur_boxes": [], "vision_used": True, "reason": "Third"},
    ]
    with patch("scraper.smm_scene_scorer.check_frames_for_ads_or_nsfw", new=AsyncMock(side_effect=side_effects)):
        res = await select_best_scene_start(str(src), clip_duration=2.0, check_vision=True, visual_cue="Hero", compare_candidates=3)

    assert res["reason"] == "Dark winner"
    assert len(res["blur_boxes"]) == 1
    assert res["blur_boxes"][0]["x"] == pytest.approx(0.82)


@pytest.mark.asyncio
async def test_find_viral_scene_target_caps_ratio_away_from_end_credits():
    from scraper.smm_scene_finder import find_viral_scene_target

    sample_srt = (
        "1\n00:01:00,000 --> 00:01:05,000\nIntro talk.\n\n"
        "2\n00:46:30,000 --> 00:46:35,000\nThe Lannisters send their regards.\n\n"
        "3\n00:50:20,000 --> 00:50:25,000\nFinal scream before black screen.\n"
    )
    # Gemini picks peak right at the end of SRT (3025s == srt_end_sec), which previously overshot into end credits
    mock_pick = {"start_sec": 2980, "peak_sec": 3025, "visual_cue": "Red Wedding finale", "reason_uz": "Kulminatsiya"}
    with (
        patch("scraper.smm_scene_finder.fetch_imdb_id", new=AsyncMock(return_value="tt2178784")),
        patch("scraper.smm_scene_finder.fetch_stremio_srt", new=AsyncMock(return_value=sample_srt)),
        patch("scraper.smm_scene_finder._ask_gemini_scene_timecode", new=AsyncMock(return_value=mock_pick)),
    ):
        target = await find_viral_scene_target(tmdb_id=1399, title="Game of Thrones", content_type="tv", season_number=3, episode_number=9)

    assert target is not None
    assert target["target_ratio"] <= 0.91
    assert target["peak_sec"] < 3025.0


@pytest.mark.asyncio
async def test_select_best_scene_start_marks_all_credits_fallback(tmp_path):
    ffmpeg = resolve_ffmpeg_bin()
    src = tmp_path / "credits_only.mp4"
    subprocess.run(
        [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", "color=c=black:s=640x360:d=5",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=5",
            "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac",
            str(src),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    credits_res = {
        "is_clean": False, "has_ad_banner": False, "is_nsfw_or_gore": False,
        "is_credits": True, "excitement_score": 1, "cue_match": 1, "blur_boxes": [], "vision_used": True, "reason": "End credits",
    }
    with patch("scraper.smm_scene_scorer.check_frames_for_ads_or_nsfw", new=AsyncMock(return_value=credits_res)):
        res = await select_best_scene_start(str(src), clip_duration=2.0, check_vision=True)

    assert res.get("is_credits") is True


@pytest.mark.asyncio
async def test_scene_finder_generates_spoiler_free_uzbek_hook_and_fallback():
    from scraper.smm_scene_finder import fallback_hook_for_genres, find_viral_scene_target, sanitize_hook_text

    # 1. Strips emoji/hashtags and prevents leaking movie title
    assert sanitize_hook_text("😱 #Interstellar eshik ortida nima bor?!", movie_title="Interstellar") == ""
    clean = sanitize_hook_text("Bu eshik ortida nima bor edi?! 😱 #kino", movie_title="Ouk Strit")
    assert clean == "Bu eshik ortida nima bor edi?!"

    # 2. Genre-based fallback produces punchy Uzbek hooks
    assert "oxir" in fallback_hook_for_genres("Triller, Sirli").lower() or "kut" in fallback_hook_for_genres("Triller, Sirli").lower()
    assert fallback_hook_for_genres(None)

    # 3. find_viral_scene_target returns hook_uz and yt_title_uz from Gemini
    srt = "1\n00:10:00,000 --> 00:10:05,000\nOpen the door!\n\n2\n00:25:00,000 --> 00:25:05,000\nNo way!\n\n3\n00:40:00,000 --> 00:40:05,000\nRun!\n\n"
    fake_pick = {
        "start_sec": 1480,
        "peak_sec": 1500,
        "visual_cue": "Hero opens secret vault",
        "reason_uz": "Kutilmagan burilish",
        "hook_uz": "U eshikni ochgach hammasi o'zgardi!",
        "yt_title_uz": "Bu eshik ortida nima bor edi?",
    }
    with (
        patch("scraper.smm_scene_finder.fetch_imdb_id", new=AsyncMock(return_value="tt1234567")),
        patch("scraper.smm_scene_finder.fetch_stremio_srt", new=AsyncMock(return_value=srt)),
        patch("scraper.smm_scene_finder._ask_gemini_scene_timecode", new=AsyncMock(return_value=fake_pick)),
    ):
        hint = await find_viral_scene_target(tmdb_id=999, title="Secret Vault")

    assert hint is not None
    assert hint["hook_uz"] == "U eshikni ochgach hammasi o'zgardi!"
    assert hint["yt_title_uz"] == "Bu eshik ortida nima bor edi?"


@pytest.mark.asyncio
async def test_find_viral_scene_target_centers_anchor_near_climax_and_allows_late_act():
    from scraper.smm_scene_finder import compress_srt_for_llm, find_viral_scene_target, parse_srt_blocks

    # Finer SRT digest resolution (<75s buckets for standard ~45m episode)
    ep_srt = (
        "1\n00:01:00,000 --> 00:01:05,000\nStart.\n\n"
        "2\n00:01:40,000 --> 00:01:45,000\nSecond beat.\n\n"
        "3\n00:36:15,000 --> 00:36:20,000\nPut the knife down!\n\n"
        "4\n00:46:50,000 --> 00:46:58,000\nOutro.\n"
    )
    digest = compress_srt_for_llm(parse_srt_blocks(ep_srt))
    assert "[100s " in digest or "[90s " in digest

    # Breaking Bad S05E14 (peak=2175s, srt_end=2818s): anchor should sit ~30-45s before peak, not 120s early!
    bb_pick = {"peak_sec": 2175, "backup_peak_sec": 1200, "visual_cue": "Skyler knife confrontation", "reason_uz": "To'qnashuv"}
    with (
        patch("scraper.smm_scene_finder.fetch_imdb_id", new=AsyncMock(return_value="tt2301451")),
        patch("scraper.smm_scene_finder.fetch_stremio_srt", new=AsyncMock(return_value=ep_srt)),
        patch("scraper.smm_scene_finder._ask_gemini_scene_timecode", new=AsyncMock(return_value=bb_pick)),
    ):
        bb = await find_viral_scene_target(tmdb_id=1396, title="Breaking Bad", content_type="tv", season_number=5, episode_number=14)

    assert bb is not None
    anchor_sec = bb["target_ratio"] * bb["srt_end_sec"]
    assert 2125.0 <= anchor_sec <= 2150.0
    assert bb["backup_ratio"] == pytest.approx(round((1200.0 - 35.0) / bb["srt_end_sec"], 4), abs=0.01)

    # Late-act climax like Endgame Snap (9000 / 10153 = 88.6%) must NOT be throttled down to 0.84
    long_srt = "1\n00:02:00,000 --> 00:02:05,000\nIntro\n\n2\n02:30:00,000 --> 02:30:05,000\nI am Iron Man\n\n3\n02:49:10,000 --> 02:49:13,000\nCredits\n"
    eg_pick = {"peak_sec": 9000, "visual_cue": "Iron Man snap", "reason_uz": "Yakun"}
    with (
        patch("scraper.smm_scene_finder.fetch_imdb_id", new=AsyncMock(return_value="tt4154796")),
        patch("scraper.smm_scene_finder.fetch_stremio_srt", new=AsyncMock(return_value=long_srt)),
        patch("scraper.smm_scene_finder._ask_gemini_scene_timecode", new=AsyncMock(return_value=eg_pick)),
    ):
        eg = await find_viral_scene_target(tmdb_id=299534, title="Avengers: Endgame", content_type="movie")

    assert eg is not None
    assert 0.86 <= eg["target_ratio"] <= 0.91


