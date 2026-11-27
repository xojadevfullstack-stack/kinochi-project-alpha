from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from PIL import Image

from scraper.smm_rubric_engine import (
    build_rubric_ass,
    compute_subject_focus_x,
    create_rubric_smm_clip,
    render_rubric_cover_png,
    render_rubric_hud_png,
    render_rubric_outro_png,
)


def _sample_jpg_bytes(w: int = 320, h: int = 180) -> bytes:
    from io import BytesIO

    buf = BytesIO()
    Image.new("RGB", (w, h), (35, 55, 85)).save(buf, format="JPEG")
    return buf.getvalue()


def test_render_rubric_covers_and_hud_outro_pngs(tmp_path: Path):
    poster = _sample_jpg_bytes(200, 300)
    backdrop = _sample_jpg_bytes(480, 270)

    for rubric in ("yangiliklar", "bilasizmi", "tavsiya", "kadr_ortida"):
        cov = tmp_path / f"cover_{rubric}.jpg"
        hud = tmp_path / f"hud_{rubric}.png"
        outro = tmp_path / f"outro_{rubric}.png"

        render_rubric_cover_png(
            rubric=rubric,
            title="Muqaddima",
            year=2010,
            imdb_rating=8.4,
            movie_code="1012",
            headline="MIYANGIZNI PORTLATADIGAN TRILLER!",
            poster_bytes=poster,
            backdrop_bytes=backdrop,
            out_path=str(cov),
            size=(720, 1280),
        )
        render_rubric_hud_png(rubric=rubric, title="Muqaddima", year=2010, imdb_rating=8.4, out_path=str(hud), size=(720, 1280))
        render_rubric_outro_png(rubric=rubric, title="Muqaddima", year=2010, imdb_rating=8.4, movie_code="1012", out_path=str(outro), size=(720, 1280))

        assert cov.exists() and Image.open(cov).size == (720, 1280)
        assert hud.exists() and Image.open(hud).size == (720, 1280)
        assert outro.exists() and Image.open(outro).size == (720, 1280)


def test_build_rubric_ass_writes_soft_red_active_word_and_margin430(tmp_path: Path):
    ass_path = tmp_path / "rubric.ass"
    build_rubric_ass([(0.20, 2.00, 2.25, "Muqaddima filmida Dom Kobb")], str(ass_path))
    txt = ass_path.read_text(encoding="utf-8")
    assert "430" in txt
    assert "&H1409E5&" in txt
    assert "MUQADDIMA" in txt


def test_compute_subject_focus_x_detects_offcenter_detail(tmp_path: Path):
    # Create high-contrast detail strictly on the left third (x ~ 0.25)
    img = np.zeros((270, 480, 3), dtype=np.uint8)
    img[60:210, 80:160] = 240
    img[80:190, 95:145] = 20
    fp = tmp_path / "left_subject.jpg"
    Image.fromarray(img).save(fp)
    fx = compute_subject_focus_x(str(fp))
    assert 0.15 <= fx <= 0.45


@pytest.mark.asyncio
async def test_create_rubric_smm_clip_uses_single_take_cyrillic_tts_and_renders(tmp_path: Path):
    src = tmp_path / "movie.mp4"
    src.write_bytes(b"fake")
    out = tmp_path / "clip_99.mp4"
    fake_pcm = (np.ones(24000 * 6, dtype=np.int16) * 2000).tobytes()
    script_payload = {
        "headline": "MIYANGIZNI PORTLATADIGAN TRILLER!",
        "segments": [
            "Muqaddima filmida Dom Kobb tush paytida ma'lumot o'g'irlaydi.",
            "Endi esa u inson ongiga yangi g'oya joylashtirishi kerak.",
        ],
    }

    with (
        patch("scraper.smm_rubric_engine.probe_video_duration", return_value=2400.0),
        patch("scraper.smm_rubric_engine.generate_rubric_script_uz", new=AsyncMock(return_value=script_payload)),
        patch("scraper.smm_rubric_engine.synthesize_single_take_tts", new=AsyncMock(return_value=fake_pcm)) as mock_tts,
        patch("scraper.smm_rubric_engine.render_rubric_reels_mp4", return_value=str(out)) as mock_render,
    ):
        res = await create_rubric_smm_clip(
            video_path=str(src),
            output_path=str(out),
            rubric="tavsiya",
            title="Muqaddima",
            year=2010,
            imdb_rating=8.4,
            movie_code="1012",
            description="Dom Kobb tush ichidan sir oladi.",
            poster_bytes=_sample_jpg_bytes(200, 300),
            backdrop_bytes=_sample_jpg_bytes(480, 270),
            low_ram=True,
        )

    assert res["output_path"] == str(out)
    assert res["rubric"] == "tavsiya"
    assert res["hook_text"] == "MIYANGIZNI PORTLATADIGAN TRILLER!"
    tts_input = mock_tts.call_args.args[0]
    assert "ў" in tts_input
    assert "ўн, ўн икки" in tts_input.lower()
    assert mock_render.call_args.kwargs["low_ram"] is True


def test_render_rubric_reels_mp4_real_ffmpeg_smoke(tmp_path: Path):
    import subprocess
    import wave
    from scraper.smm_clipper import resolve_ffmpeg_bin
    from scraper.smm_rubric_engine import render_rubric_reels_mp4

    ffmpeg = resolve_ffmpeg_bin()
    src_mp4 = tmp_path / "src.mp4"
    subprocess.run(
        [ffmpeg, "-y", "-f", "lavfi", "-i", "testsrc=size=640x360:rate=24:duration=4", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(src_mp4)],
        check=True, capture_output=True, timeout=30,
    )
    wav_p = tmp_path / "voice.wav"
    with wave.open(str(wav_p), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes((np.ones(24000 * 3, dtype=np.int16) * 1200).tobytes())

    cov, hud, outro = tmp_path / "cov.jpg", tmp_path / "hud.png", tmp_path / "out.png"
    render_rubric_cover_png("yangiliklar", "Yulduzlar sari", 2026, 8.1, "3955", "PREMYERA TAYYOR", _sample_jpg_bytes(200, 300), _sample_jpg_bytes(480, 270), str(cov), size=(720, 1280))
    render_rubric_hud_png("yangiliklar", "Yulduzlar sari", 2026, 8.1, str(hud), size=(720, 1280))
    render_rubric_outro_png("yangiliklar", "Yulduzlar sari", 2026, 8.1, "3955", str(outro), size=(720, 1280))

    out_mp4 = tmp_path / "final.mp4"
    render_rubric_reels_mp4(
        video_path=str(src_mp4),
        windows=[(0.1, 1.5), (1.8, 1.6)],
        clauses=[(0.1, 1.3, 1.4, "Premyera tayyor."), (1.5, 2.9, 3.0, "Kod: 39 55.")],
        voice_wav=str(wav_p),
        cover_jpg=str(cov),
        hud_png=str(hud),
        outro_png=str(outro),
        narration_end=1.45,
        output_path=str(out_mp4),
        low_ram=True,
    )
    assert out_mp4.exists() and out_mp4.stat().st_size > 10000
    probe = subprocess.run([ffmpeg, "-i", str(out_mp4)], capture_output=True, text=True).stderr
    assert "720x1280" in probe and "SAR 1:1" in probe and "48000 Hz, stereo" in probe


def test_render_rubric_reels_mp4_passes_fontsdir_for_linux(tmp_path: Path):
    from scraper.smm_rubric_engine import render_rubric_reels_mp4

    calls = []

    def _fake_run(cmd, **kwargs):
        calls.append(cmd)
        if "-frames:v" in cmd:
            Path(cmd[-1]).write_bytes(_sample_jpg_bytes(480, 270))
        else:
            Path(cmd[-1]).write_bytes(b"mp4")
        return MagicMock(returncode=0)

    cov, hud, outro, wav = tmp_path / "c.jpg", tmp_path / "h.png", tmp_path / "o.png", tmp_path / "v.wav"
    for f in (cov, hud, outro, wav):
        f.write_bytes(b"x")
    out_mp4 = tmp_path / "out.mp4"

    with patch("scraper.smm_rubric_engine.subprocess.run", side_effect=_fake_run):
        render_rubric_reels_mp4(
            video_path=str(tmp_path / "src.mp4"),
            windows=[(1.0, 1.5), (3.0, 2.0)],
            clauses=[(0.1, 1.2, 1.3, "Salom."), (1.5, 2.5, 2.6, "Kod.")],
            voice_wav=str(wav),
            cover_jpg=str(cov),
            hud_png=str(hud),
            outro_png=str(outro),
            narration_end=1.4,
            output_path=str(out_mp4),
            low_ram=True,
        )

    final_cmd = " ".join(str(x) for x in calls[-1])
    assert "fontsdir=" in final_cmd


@pytest.mark.asyncio
async def test_create_rubric_smm_clip_extracts_backdrop_from_video_when_none(tmp_path: Path):
    src = tmp_path / "movie.mp4"
    src.write_bytes(b"fake")
    out = tmp_path / "clip_98.mp4"
    fake_pcm = (np.ones(24000 * 5, dtype=np.int16) * 2000).tobytes()
    script_payload = {"headline": "YANGILIK", "segments": ["Premyera kutilmoqda."]}

    def _fake_extract(video_path: str, ts_sec: float) -> bytes:
        return _sample_jpg_bytes(640, 360)

    with (
        patch("scraper.smm_rubric_engine.probe_video_duration", return_value=1200.0),
        patch("scraper.smm_rubric_engine.generate_rubric_script_uz", new=AsyncMock(return_value=script_payload)),
        patch("scraper.smm_rubric_engine.synthesize_single_take_tts", new=AsyncMock(return_value=fake_pcm)),
        patch("scraper.smm_rubric_engine.extract_video_frame_bytes", side_effect=_fake_extract) as mock_ext,
        patch("scraper.smm_rubric_engine.render_rubric_cover_png") as mock_cov,
        patch("scraper.smm_rubric_engine.render_rubric_reels_mp4", return_value=str(out)),
    ):
        await create_rubric_smm_clip(
            video_path=str(src),
            output_path=str(out),
            rubric="yangiliklar",
            title="Test",
            year=2026,
            imdb_rating=8.2,
            movie_code="3968",
            poster_bytes=_sample_jpg_bytes(200, 300),
            backdrop_bytes=None,
            low_ram=True,
        )

    mock_ext.assert_called_once()
    assert mock_cov.call_args.args[7] is not None
