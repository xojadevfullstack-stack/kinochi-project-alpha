from pathlib import Path
from unittest.mock import AsyncMock, patch

import numpy as np
import pytest

from scraper.smm_facts_clipper import (
    align_clauses_to_pauses,
    build_facts_ass_subtitles,
    compute_movie_sample_windows,
    create_facts_clip_from_video,
    parse_facts_script_json,
)


def test_parse_facts_script_json_handles_fenced_json_and_invalid_input():
    raw = '```json\n{"title": "Interstellar", "year": 2014, "segments": [{"text": "Fakt bir.", "callout": "500 AKR"}]}\n```'
    parsed = parse_facts_script_json(raw, fallback_title="Interstellar", fallback_year=2014)
    assert parsed["title"] == "Interstellar"
    assert parsed["segments"][0]["callout"] == "500 AKR"

    bad = parse_facts_script_json("not json", fallback_title="Matritsa", fallback_year=1999)
    assert bad["title"] == "Matritsa"
    assert bad["year"] == 1999
    assert bad["segments"] == []


def test_compute_movie_sample_windows_avoids_intro_and_credits():
    windows = compute_movie_sample_windows(total_duration_sec=3600.0, count=8, clip_sec=3.0)
    assert len(windows) == 8
    assert all(dur == pytest.approx(3.0) for _, dur in windows)
    assert windows[0][0] >= 3600.0 * 0.12
    assert windows[-1][0] + windows[-1][1] <= 3600.0 * 0.86


def test_align_clauses_to_pauses_splits_text_across_detected_gaps():
    sr = 8000
    # 2.0s signal: [0..0.8 speech], [0.8..1.1 silence], [1.1..2.0 speech]
    pcm = np.zeros(int(2.0 * sr), dtype=np.float32)
    pcm[: int(0.8 * sr)] = 0.25
    pcm[int(1.1 * sr) :] = 0.25
    clauses = align_clauses_to_pauses(pcm, sr, ["Birinchi fakt.", "Ikkinchi fakt."])
    assert len(clauses) == 2
    assert clauses[0][0] == pytest.approx(0.0, abs=0.05)
    assert clauses[0][1] < clauses[1][0]
    assert clauses[1][1] == pytest.approx(2.0, abs=0.05)


def test_build_facts_ass_subtitles_writes_karaoke_events(tmp_path: Path):
    ass_file = tmp_path / "subs.ass"
    build_facts_ass_subtitles([(0.2, 2.2, "Nolan haqiqiy makka ekkan")], str(ass_file))
    content = ass_file.read_text(encoding="utf-8")
    assert "PlayResX: 1080" in content
    assert "Dialogue: 0," in content
    assert "HAQIQIY" in content


@pytest.mark.asyncio
async def test_create_facts_clip_from_video_cleans_temp_on_success(tmp_path: Path):
    src = tmp_path / "movie.mp4"
    src.write_bytes(b"fake-video")
    out = tmp_path / "out.mp4"
    script = {
        "title": "Interstellar",
        "year": 2014,
        "segments": [{"text": "Birinchi fakt.", "callout": "FAKT 1"}, {"text": "Ikkinchi fakt.", "callout": "FAKT 2"}],
    }

    # Valid 6-second raw PCM bytes (triggers s16le normalize path cleanly)
    fake_pcm = (np.ones(24000 * 6, dtype=np.int16) * 2000).tobytes()
    with (
        patch("scraper.smm_facts_clipper.probe_video_duration", return_value=1800.0),
        patch("scraper.smm_facts_clipper.generate_facts_script", new=AsyncMock(return_value=script)),
        patch("scraper.smm_facts_clipper.synthesize_uzbek_tts", new=AsyncMock(return_value=fake_pcm)),
        patch("scraper.smm_facts_clipper.render_facts_vertical_mp4", return_value=str(out)) as mock_render,
    ):
        res = await create_facts_clip_from_video(
            video_path=str(src),
            output_path=str(out),
            title="Interstellar",
            year=2014,
            movie_code="3957",
            low_ram=True,
        )

    assert res["output_path"] == str(out)
    assert res["cuts_count"] >= 2
    assert mock_render.call_args.kwargs["low_ram"] is True

