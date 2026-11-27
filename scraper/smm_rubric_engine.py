"""Automated 4-Rubric Golden Standard Video & Cover Pipeline (Render 512MB-safe)."""
from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import tempfile
from typing import Any, Dict, List, Optional, Tuple

import httpx
import numpy as np
from PIL import Image

from scraper.smm_clipper import resolve_ffmpeg_bin
from scraper.smm_facts_clipper import align_clauses_to_pauses, compute_movie_sample_windows, normalize_tts_wav, probe_video_duration, read_wav_pcm
from scraper.smm_rubric_planner import digits_to_uz_2plus2_spoken, lat_to_uz_cyrillic_tts
from scraper.smm_rubric_visuals import build_rubric_ass, render_rubric_cover_png, render_rubric_hud_png, render_rubric_outro_png

_SCRIPT_MODELS = ("gemini-flash-lite-latest", "gemini-3.8-flash", "gemini-3.5-flash")
_TTS_MODELS = ("gemini-3.1-flash-tts-preview", "gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts", "gemini-2.5-flash-preview-tts")


def compute_subject_focus_x(frame_path: str) -> float:
    """Estimate horizontal subject focus (0.25..0.75) using Haar faces or horizontal gradient energy."""
    try:
        import cv2  # type: ignore

        img = cv2.imread(frame_path)
        if img is not None:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape
            xml = os.path.join(getattr(cv2.data, "haarcascades", ""), "haarcascade_frontalface_default.xml")
            if xml and os.path.exists(xml):
                faces = cv2.CascadeClassifier(xml).detectMultiScale(gray, 1.15, 4, minSize=(max(20, w // 18), max(20, h // 18)))
                if len(faces):
                    x, _, fw, _ = max(faces, key=lambda b: b[2] * b[3])
                    return max(0.25, min(0.75, float(x + fw * 0.5) / float(max(1, w))))
    except Exception:
        pass

    arr = np.asarray(Image.open(frame_path).convert("L"), dtype=np.float32)
    gx = np.abs(np.diff(arr, axis=1, prepend=arr[:, :1]))
    gy = np.abs(np.diff(arr, axis=0, prepend=arr[:1, :]))
    h_rows = arr.shape[0]
    row_w = np.ones((h_rows, 1), dtype=np.float32)
    row_w[: int(h_rows * 0.68), :] = 1.6
    col_energy = ((gx + gy) * row_w).sum(axis=0)
    tot = float(col_energy.sum())
    if tot <= 1e-6:
        return 0.50
    xs = np.arange(arr.shape[1], dtype=np.float32) / float(max(1, arr.shape[1] - 1))
    cx = float((col_energy * xs).sum() / tot)
    return max(0.25, min(0.75, cx))


def extract_video_frame_bytes(video_path: str, ts_sec: float) -> Optional[bytes]:
    """Extract a crisp JPEG frame at ts_sec from video_path for rubric cover backdrops."""
    ffmpeg = resolve_ffmpeg_bin()
    with tempfile.TemporaryDirectory() as td:
        out_jpg = os.path.join(td, "backdrop.jpg")
        try:
            subprocess.run(
                [ffmpeg, "-y", "-ss", f"{max(0.0, ts_sec):.2f}", "-i", video_path, "-frames:v", "1", "-q:v", "2", out_jpg],
                capture_output=True,
                timeout=30,
            )
            if os.path.exists(out_jpg) and os.path.getsize(out_jpg) > 512:
                with open(out_jpg, "rb") as f:
                    return f.read()
        except Exception:
            pass
    return None


async def generate_rubric_script_uz(
    rubric: str,
    title: str,
    year: Optional[int],
    imdb_rating: Optional[float],
    description: Optional[str],
    genres: Optional[str],
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate grounded Uzbek rubric voiceover script strictly from real DB metadata."""
    key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY sozlanmagan")
    fact_prompt = (
        f"MediaPlus SMM uchun '{title}' ({year or ''}) haqida '{rubric}' rubrikasida o'zbek tilida JSON qaytar.\n"
        f"FAKAT quyidagi real ma'lumotlarga tayan (aslo soxta fakt, mukofot yoki raqam to'qima):\n"
        f"- Sarlavha: {title}\n- Yil: {year or ''}\n- IMDb: {imdb_rating or ''}\n- Janr: {genres or ''}\n"
        f"- Tavsif: {(description or '')[:550]}\n"
        "JSON formati: {\"headline\":\"5 so'zgacha sarlavha\",\"segments\":[\"4 ta qisqa tabiiy o'zbekcha jumla\"]}"
    )
    async with httpx.AsyncClient(timeout=30.0) as client:
        for model in _SCRIPT_MODELS:
            r = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
                json={"contents": [{"parts": [{"text": fact_prompt}]}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0.45}},
            )
            if r.status_code == 200:
                raw = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                m = re.search(r"(\{[\s\S]*\})", raw)
                try:
                    obj = json.loads(m.group(1) if m else raw)
                    segs = [str(s).strip() for s in (obj.get("segments") or []) if str(s).strip()]
                    if segs:
                        return {"headline": str(obj.get("headline") or title)[:70], "segments": segs[:5]}
                except Exception:
                    continue
    raise RuntimeError("Gemini rubric script yaratilmadi")


async def synthesize_single_take_tts(text_cyrillic: str, api_key: Optional[str] = None, voice: str = "Charon") -> bytes:
    """Synthesize full narration + CTA in one single Gemini TTS call for seamless timbre."""
    key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY sozlanmagan")
    import base64

    async with httpx.AsyncClient(timeout=60.0) as client:
        for model in _TTS_MODELS:
            r = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
                json={
                    "contents": [{"parts": [{"text": text_cyrillic}]}],
                    "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}},
                },
            )
            if r.status_code == 200:
                return base64.b64decode(r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
    raise RuntimeError("Gemini TTS audio yaratilmadi")


def render_rubric_reels_mp4(
    video_path: str,
    windows: List[Tuple[float, float]],
    clauses: List[Tuple[float, float, float, str]],
    voice_wav: str,
    cover_jpg: str,
    hud_png: str,
    outro_png: str,
    narration_end: float,
    output_path: str,
    low_ram: bool = True,
) -> str:
    """Render 9:16 Golden Standard video sequentially using <512MB RAM via ffmpeg concat + single overlay pass."""
    ffmpeg = resolve_ffmpeg_bin()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    w, h = (720, 1280) if low_ram else (1080, 1920)
    enc = ["-threads", "1", "-filter_threads", "1", "-filter_complex_threads", "1", "-preset", "ultrafast", "-crf", "23"] if low_ram else ["-preset", "medium", "-crf", "17"]

    with tempfile.TemporaryDirectory() as td:
        ass_path = os.path.join(td, "subs.ass")
        build_rubric_ass(clauses, ass_path)
        seg_files = []
        for idx, (st, dur) in enumerate(windows):
            probe_jpg = os.path.join(td, f"p_{idx}.jpg")
            subprocess.run([ffmpeg, "-y", "-ss", f"{st + dur * 0.5:.2f}", "-i", video_path, "-frames:v", "1", "-vf", "scale=480:270", probe_jpg], capture_output=True, timeout=30)
            fx = compute_subject_focus_x(probe_jpg) if os.path.exists(probe_jpg) else 0.50
            is_outro = idx == len(windows) - 1
            blur_f = ",gblur=sigma=24,eq=contrast=1.04:brightness=-0.22" if is_outro else ",unsharp=5:5:0.4:3:3:0.0,eq=contrast=1.07:saturation=1.10"
            vf = f"crop=min(iw\\,ih*0.78):ih:(iw-ow)*{fx:.2f}:0,scale={w}:-2:flags=lanczos,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1{blur_f},fps=24,format=yuv420p"
            seg = os.path.join(td, f"seg_{idx:02d}.mp4")
            subprocess.run([ffmpeg, "-y", "-ss", f"{st:.2f}", "-t", f"{dur:.2f}", "-i", video_path, "-an", "-vf", vf, "-r", "24", "-c:v", "libx264", *enc, seg], capture_output=True, check=True, timeout=90)
            seg_files.append(seg)

        vlist = os.path.join(td, "list.txt")
        with open(vlist, "w", encoding="utf-8") as f:
            f.writelines(f"file '{p.replace(chr(92), '/')}'\n" for p in seg_files)
        merged = os.path.join(td, "merged.mp4")
        subprocess.run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", vlist, "-c", "copy", merged], capture_output=True, check=True, timeout=60)

        ass_esc = ass_path.replace("\\", "/").replace(":", "\\:")
        fonts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "app", "assets", "fonts")
        fonts_opt = f":fontsdir='{fonts_dir.replace(chr(92), '/').replace(':', chr(92) + ':')}'" if os.path.isdir(fonts_dir) else ""
        fc = (
            f"[0:v][2:v]overlay=0:0:enable='lt(t,{narration_end:.3f})'[vhud];"
            f"[vhud][3:v]overlay=0:0:enable='gte(t,{narration_end:.3f})'[voutro];"
            f"[voutro]ass='{ass_esc}'{fonts_opt}[vsub];"
            f"[vsub][4:v]overlay=0:0:enable='lt(t,0.55)':eof_action=pass,setsar=1[vout]"
        )
        subprocess.run(
            [
                ffmpeg, "-y", "-i", merged, "-i", voice_wav, "-i", hud_png, "-i", outro_png,
                "-loop", "1", "-t", "0.60", "-i", cover_jpg,
                "-filter_complex", fc, "-map", "[vout]", "-map", "1:a", "-shortest",
                "-r", "24", "-ar", "48000", "-ac", "2", "-c:v", "libx264", *enc, "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", output_path,
            ],
            capture_output=True, check=True, timeout=float(os.getenv("SMM_RENDER_TIMEOUT_SEC", "360")),
        )
    return output_path


async def create_rubric_smm_clip(
    video_path: str, output_path: str, rubric: str, title: str,
    year: Optional[int], imdb_rating: Optional[float], movie_code: str,
    description: Optional[str] = None, genres: Optional[str] = None,
    poster_bytes: Optional[bytes] = None, backdrop_bytes: Optional[bytes] = None,
    low_ram: bool = True,
    sample_start_sec: Optional[float] = None,
    sample_span_sec: Optional[float] = None,
) -> Dict[str, Any]:
    """End-to-end Render-safe Golden Standard rubric generator returning output path & hook."""
    total_dur = probe_video_duration(video_path)
    script = await generate_rubric_script_uz(rubric, title, year, imdb_rating, description, genres)
    cta_lat = f"Filmni to'liq o'zbek tilida tomosha qilish uchun Telegram botimizga o'ting. Kod: {digits_to_uz_2plus2_spoken(movie_code)}."
    story_segs = [s.strip() for s in script["segments"] if s.strip()]
    full_cyr = lat_to_uz_cyrillic_tts(" ".join(story_segs) + " ... " + cta_lat)
    audio_bytes = await synthesize_single_take_tts(full_cyr)

    w, h = (720, 1280) if low_ram else (1080, 1920)
    with tempfile.TemporaryDirectory() as td:
        raw_wav, wav_p = os.path.join(td, "raw.wav"), os.path.join(td, "voice.wav")
        await asyncio.to_thread(normalize_tts_wav, audio_bytes, raw_wav, wav_p)
        pcm, sr = read_wav_pcm(wav_p)
        voice_dur = len(pcm) / float(max(1, sr))
        display_segs = story_segs + ["Filmni to'liq o'zbek tilida tomosha qilish uchun", "Telegram botimizga o'ting.", f"Kod: {movie_code[:2]} {movie_code[2:]}." if len(movie_code) == 4 else f"Kod: {movie_code}."]
        aligned = align_clauses_to_pauses(pcm, sr, display_segs)
        clauses = [(st, en, (aligned[i + 1][0] - 0.04) if i + 1 < len(aligned) else voice_dur + 0.3, txt) for i, (st, en, txt) in enumerate(aligned)]
        narration_end = clauses[len(story_segs) - 1][1] + 0.25 if len(clauses) > len(story_segs) else max(2.0, voice_dur - 5.0)
        story_cuts = max(4, min(9, int(narration_end / 2.4)))
        if sample_start_sec is not None and sample_span_sec is not None and sample_span_sec > 20.0:
            clip_s = narration_end / story_cuts
            step = max(clip_s, (sample_span_sec - 10.0) / max(1, story_cuts))
            windows = [(round(sample_start_sec + 2.0 + i * step, 2), round(clip_s, 2)) for i in range(story_cuts)]
            windows.append((round(sample_start_sec + max(3.0, sample_span_sec * 0.55), 2), round(max(4.5, voice_dur - narration_end + 0.6), 2)))
        else:
            windows = compute_movie_sample_windows(total_dur, count=story_cuts, clip_sec=narration_end / story_cuts)
            windows.append((round(total_dur * 0.45, 2), round(max(4.5, voice_dur - narration_end + 0.6), 2)))

        if backdrop_bytes is None and windows:
            still_ts = windows[min(1, len(windows) - 1)][0] + 0.5
            backdrop_bytes = await asyncio.to_thread(extract_video_frame_bytes, video_path, still_ts)

        cov, hud, outro = os.path.join(td, "cov.jpg"), os.path.join(td, "hud.png"), os.path.join(td, "out.png")
        render_rubric_cover_png(rubric, title, year, imdb_rating, movie_code, script["headline"], poster_bytes, backdrop_bytes, cov, size=(w, h))
        render_rubric_hud_png(rubric, title, year, imdb_rating, hud, size=(w, h))
        render_rubric_outro_png(rubric, title, year, imdb_rating, movie_code, outro, size=(w, h))
        await asyncio.to_thread(render_rubric_reels_mp4, video_path, windows, clauses, wav_p, cov, hud, outro, narration_end, output_path, low_ram=low_ram)

    return {"output_path": output_path, "rubric": rubric, "hook_text": script["headline"], "duration_sec": round(voice_dur + 0.4, 2), "narration_end": round(narration_end, 2)}
