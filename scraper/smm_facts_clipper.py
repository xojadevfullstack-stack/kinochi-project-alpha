"""Automated 'Bilasizmi?' Cinema Facts Reels Builder (Level 2 Slice 1, Render-safe)."""
from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import subprocess
import tempfile
import wave
from typing import Any, Dict, List, Optional, Tuple

import httpx
import numpy as np

from scraper.smm_clipper import resolve_ffmpeg_bin, resolve_font_file

_SCRIPT_MODELS = ("gemini-flash-lite-latest", "gemini-3.8-flash", "gemini-3.5-flash")
_TTS_MODELS = ("gemini-3.8-flash-lite-tts", "gemini-2.5-flash-preview-tts", "gemini-3.8-flash-tts")
_ASSETS_FONT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "app", "assets", "fonts", "Montserrat-Bold.ttf")


def parse_facts_script_json(raw_text: str, fallback_title: str = "", fallback_year: Optional[int] = None) -> Dict[str, Any]:
    """Extract and validate structured Bilasizmi script JSON."""
    cleaned = (raw_text or "").strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned) or re.search(r"(\{[\s\S]*\})", cleaned)
    if m:
        cleaned = m.group(1).strip()
    try:
        data = json.loads(cleaned)
        if not isinstance(data, dict):
            raise ValueError("Expected JSON object")
        segs = [s for s in (data.get("segments") or []) if isinstance(s, dict) and str(s.get("text") or "").strip()]
        return {"title": str(data.get("title") or fallback_title), "year": data.get("year") or fallback_year, "badge": str(data.get("badge") or "BILASIZMI?"), "segments": segs}
    except Exception:
        return {"title": fallback_title, "year": fallback_year, "badge": "BILASIZMI?", "segments": []}


def compute_movie_sample_windows(total_duration_sec: float, count: int = 8, clip_sec: float = 3.0) -> List[Tuple[float, float]]:
    """Pick evenly spaced clean clip windows avoiding intro (0-12%) and credits (86-100%)."""
    if total_duration_sec <= 0 or count <= 0 or clip_sec <= 0:
        raise ValueError("total_duration_sec, count, and clip_sec must be positive")
    start_bound = total_duration_sec * 0.12
    end_bound = max(start_bound + clip_sec, total_duration_sec * 0.86 - clip_sec)
    if count == 1:
        return [(round(start_bound, 2), round(min(clip_sec, total_duration_sec - start_bound), 2))]
    step = (end_bound - start_bound) / max(1, count - 1)
    return [(round(start_bound + i * step, 2), round(clip_sec, 2)) for i in range(count)]


def align_clauses_to_pauses(pcm: np.ndarray, sr: int, texts: List[str]) -> List[Tuple[float, float, str]]:
    """Align spoken sentences deterministically to real RMS silence pauses in TTS audio."""
    clean_texts = [t.strip() for t in texts if (t or "").strip()]
    dur = len(pcm) / float(sr) if sr > 0 else 0.0
    if not clean_texts or dur <= 0:
        return []
    hop = max(1, int(0.02 * sr))
    rms = np.array([float(np.sqrt(np.mean(pcm[i : i + hop] ** 2))) for i in range(0, max(1, len(pcm) - hop), hop)])
    gaps, in_gap, g_start = [], False, 0.0
    for idx, silent in enumerate(rms < 0.015):
        t = idx * 0.02
        if silent and not in_gap:
            in_gap, g_start = True, t
        elif not silent and in_gap:
            in_gap = False
            if t - g_start >= 0.16 and g_start > 0.2 and t < dur - 0.2:
                gaps.append((g_start, t))
    needed = len(clean_texts) - 1
    chosen = sorted(sorted(gaps, key=lambda g: g[1] - g[0], reverse=True)[:needed], key=lambda g: g[0])
    if len(chosen) < needed:
        total_c = sum(max(2, len(t)) for t in clean_texts)
        cur, out = 0.0, []
        for t in clean_texts:
            d = dur * (max(2, len(t)) / total_c)
            out.append((round(cur, 2), round(min(dur, cur + d), 2), t))
            cur += d
        return out
    bounds = [0.0] + [g[0] for g in chosen] + [dur]
    starts = [0.0] + [g[1] for g in chosen]
    return [(round(starts[i], 2), round(bounds[i + 1], 2), clean_texts[i]) for i in range(len(clean_texts))]


def _ass_ts(sec: float) -> str:
    sec = max(0.0, sec)
    return f"{int(sec // 3600)}:{int((sec % 3600) // 60):02d}:{sec % 60:05.2f}"


def build_facts_ass_subtitles(clauses: List[Tuple[float, float, str]], out_ass: str) -> None:
    """Write 1080x1920 ASS karaoke subtitles with Cinematic Red active-word highlight."""
    header = (
        "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "Style: Default,Montserrat,62,&H00FFFFFF,&H001409E5,&H00080A10,&HA0000000,1,0,0,0,100,100,0,0,1,5,3,2,65,65,340,1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    lines = [header]
    for st, en, text in clauses:
        words = text.split()
        if not words:
            continue
        dur, tot_c = max(0.3, en - st), sum(max(2, len(w)) for w in words)
        cur = st
        for chunk in [words[i : i + 3] for i in range(0, len(words), 3)]:
            c_c = sum(max(2, len(w)) for w in chunk)
            c_dur = dur * (c_c / tot_c)
            wt = cur
            for idx, w in enumerate(chunk):
                we = min(en, wt + c_dur * (max(2, len(w)) / c_c))
                parts = [r"{\c&H2424FF&\fscx109\fscy109}" + cw.upper() + r"{\c&HFFFFFF&\fscx100\fscy100}" if j == idx else cw.upper() for j, cw in enumerate(chunk)]
                lines.append(f"Dialogue: 0,{_ass_ts(wt)},{_ass_ts(we)},Default,,0,0,0,,{' '.join(parts)}\n")
                wt = we
            cur += c_dur
    with open(out_ass, "w", encoding="utf-8") as f:
        f.writelines(lines)


def probe_video_duration(video_path: str) -> float:
    """Read video duration in seconds via FFmpeg stderr."""
    proc = subprocess.run([resolve_ffmpeg_bin(), "-i", video_path], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20)
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", proc.stderr or "")
    if not m:
        raise RuntimeError("Video duration topilmadi")
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def read_wav_pcm(wav_path: str) -> Tuple[np.ndarray, int]:
    """Load mono/stereo 16-bit WAV into normalized float32 numpy array."""
    with wave.open(wav_path, "rb") as w:
        sr, ch, frames = w.getframerate(), w.getnchannels(), w.getnframes()
        pcm = np.frombuffer(w.readframes(frames), dtype=np.int16).astype(np.float32) / 32768.0
    return (pcm.reshape(-1, ch).mean(axis=1) if ch > 1 else pcm), sr


async def generate_facts_script(title: str, year: Optional[int] = None, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Generate Hook-driven Uzbek 'Bilasizmi?' cinema facts JSON via Gemini."""
    key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY sozlanmagan")
    prompt = f"'{title} ({year or ''})' filmi haqida 'BILASIZMI?' formatida 4 ta haqiqiy fakt va 1 ta yakuniy savoldan iborat 85-105 so'zli o'zbekcha diktor ssenariy JSON qaytar: {{\"title\":\"{title}\",\"year\":{year or 'null'},\"badge\":\"BILASIZMI?\",\"segments\":[{{\"text\":\"...\",\"callout\":\"...\"}}]}}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        for model in _SCRIPT_MODELS:
            r = await client.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}", json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0.65}})
            if r.status_code == 200:
                raw = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                parsed = parse_facts_script_json(raw, fallback_title=title, fallback_year=year)
                if parsed["segments"]:
                    return parsed
    raise RuntimeError("Gemini facts script yaratilmadi")


async def synthesize_uzbek_tts(text: str, api_key: Optional[str] = None, voice: str = "Charon") -> bytes:
    """Synthesize continuous Uzbek voiceover via Gemini TTS with 429 fallback."""
    key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY sozlanmagan")
    async with httpx.AsyncClient(timeout=60.0) as client:
        for model in _TTS_MODELS:
            r = await client.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}", json={"contents": [{"parts": [{"text": text}]}], "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}})
            if r.status_code == 200:
                return base64.b64decode(r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
    raise RuntimeError("Gemini TTS audio yaratilmadi")


def render_facts_vertical_mp4(video_path: str, windows: List[Tuple[float, float]], voice_wav: str, ass_path: str, title: str, movie_code: str, output_path: str, low_ram: bool = True) -> str:
    """Cut multiple movie scenes into 9:16 montage with subtitles, HUD and audio mix."""
    ffmpeg = resolve_ffmpeg_bin()
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    w, h = (720, 1280) if low_ram else (1080, 1920)
    enc = ["-threads", "1", "-filter_threads", "1", "-filter_complex_threads", "1", "-preset", "ultrafast", "-crf", "26"] if low_ram else ["-preset", "veryfast", "-crf", "22"]
    font = resolve_font_file(_ASSETS_FONT if os.path.exists(_ASSETS_FONT) else None)
    fopt = f"fontfile='{font.replace(chr(92), '/').replace(':', chr(92) + ':')}':" if font else ""
    with tempfile.TemporaryDirectory() as td:
        segs = []
        for idx, (st, dur) in enumerate(windows):
            seg = os.path.join(td, f"s_{idx}.mp4")
            subprocess.run([ffmpeg, "-y", "-ss", f"{st:.2f}", "-t", f"{dur:.2f}", "-i", video_path, "-an", "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},eq=contrast=1.06:brightness=-0.03", "-r", "30", "-c:v", "libx264", *enc, "-pix_fmt", "yuv420p", seg], capture_output=True, check=True, timeout=90)
            segs.append(seg)
        vlist = os.path.join(td, "list.txt")
        with open(vlist, "w", encoding="utf-8") as f:
            f.writelines(f"file '{p.replace(chr(92), '/')}'\n" for p in segs)
        merged = os.path.join(td, "merged.mp4")
        subprocess.run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", vlist, "-c", "copy", merged], capture_output=True, check=True, timeout=60)
        ass_esc = ass_path.replace("\\", "/").replace(":", "\\:")
        vf = f"[0:v]ass='{ass_esc}',drawtext={fopt}text='BILASIZMI?  •  #{movie_code}':fontsize={28 if low_ram else 42}:fontcolor=white:box=1:boxcolor=#E50914@0.92:boxborderw=12:x=(w-text_w)/2:y={70 if low_ram else 110}[vout]"
        subprocess.run([ffmpeg, "-y", "-i", merged, "-i", voice_wav, "-filter_complex", vf, "-map", "[vout]", "-map", "1:a", "-shortest", "-c:v", "libx264", *enc, "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", output_path], capture_output=True, check=True, timeout=float(os.getenv("SMM_RENDER_TIMEOUT_SEC", "240")))
    return output_path


def normalize_tts_wav(audio_bytes: bytes, raw_path: str, out_wav: str) -> str:
    """Normalize raw Gemini TTS PCM/RIFF bytes into 24kHz mono 16-bit WAV."""
    with open(raw_path, "wb") as f:
        f.write(audio_bytes)
    in_fmt = [] if audio_bytes[:4] == b"RIFF" else ["-f", "s16le", "-ar", "24000", "-ac", "1"]
    subprocess.run([resolve_ffmpeg_bin(), "-y", *in_fmt, "-i", raw_path, "-ar", "24000", "-ac", "1", out_wav], capture_output=True, check=True, timeout=60)
    return out_wav


async def create_facts_clip_from_video(video_path: str, output_path: str, title: str, year: Optional[int] = None, movie_code: str = "", low_ram: bool = True) -> Dict[str, Any]:
    """End-to-end Level 2 'Bilasizmi?' generator from a real local movie file."""
    total_dur = probe_video_duration(video_path)
    script = await generate_facts_script(title=title, year=year)
    texts = [s["text"].strip() for s in script["segments"]]
    audio_bytes = await synthesize_uzbek_tts(" ".join(texts))
    with tempfile.TemporaryDirectory() as td:
        raw_wav, wav_p, ass_p = os.path.join(td, "raw.wav"), os.path.join(td, "voice.wav"), os.path.join(td, "subs.ass")
        await asyncio.to_thread(normalize_tts_wav, audio_bytes, raw_wav, wav_p)
        pcm, sr = read_wav_pcm(wav_p)
        clauses = align_clauses_to_pauses(pcm, sr, texts)
        build_facts_ass_subtitles(clauses, ass_p)
        cut_count = max(6, min(10, int((len(pcm) / max(1, sr)) / 3.2)))
        windows = compute_movie_sample_windows(total_dur, count=cut_count, clip_sec=max(2.5, (len(pcm) / max(1, sr)) / cut_count + 0.1))
        await asyncio.to_thread(render_facts_vertical_mp4, video_path=video_path, windows=windows, voice_wav=wav_p, ass_path=ass_p, title=script["title"], movie_code=movie_code, output_path=output_path, low_ram=low_ram)
    return {"output_path": output_path, "cuts_count": len(windows), "title": script["title"]}
