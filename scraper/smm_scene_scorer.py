"""Smart Scene Scorer & Gemini Vision Ad/NSFW Filter for SMM Clips (Slice 1.5)."""
from __future__ import annotations

import base64
import json
import os
import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple

import cv2
import httpx
import numpy as np

from scraper.smm_clipper import resolve_ffmpeg_bin
from scraper.video_verifier import is_frame_valid


def parse_volumedetect_output(stderr_text: str) -> Tuple[float, float]:
    """Parse FFmpeg volumedetect stderr for (mean_volume_db, max_volume_db)."""
    mean_m = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", stderr_text or "")
    max_m = re.search(r"max_volume:\s*([-\d.]+)\s*dB", stderr_text or "")
    return (float(mean_m.group(1)) if mean_m else -90.0), (float(max_m.group(1)) if max_m else -90.0)


def parse_scene_vision_response(raw_text: str) -> Dict[str, Any]:
    """Parse Gemini Vision scene safety JSON with graceful clean fallback."""
    cleaned = (raw_text or "").strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned) or re.search(r"(\{[\s\S]*\})", cleaned)
    if m:
        cleaned = m.group(1).strip()
    try:
        data = json.loads(cleaned)
        if not isinstance(data, dict):
            raise ValueError("Expected JSON object")
        has_ad = bool(data.get("has_ad_banner", False))
        is_nsfw = bool(data.get("is_nsfw_or_gore", False))
        is_credits = bool(data.get("is_credits", False))
        is_clean = bool(data.get("is_clean", not (has_ad or is_nsfw or is_credits)))
        return {
            "is_clean": is_clean,
            "has_ad_banner": has_ad,
            "is_nsfw_or_gore": is_nsfw,
            "is_credits": is_credits,
            "excitement_score": int(data.get("excitement_score", 5)),
            "reason": str(data.get("reason", "")),
        }
    except Exception:
        return {"is_clean": True, "has_ad_banner": False, "is_nsfw_or_gore": False, "is_credits": False, "excitement_score": 5, "reason": "Fallback clean"}


def _measure_audio_db(ffmpeg: str, video_path: str, start_sec: float, probe_dur: float) -> Tuple[float, float]:
    cmd = [ffmpeg, "-ss", f"{start_sec:.2f}", "-t", f"{probe_dur:.2f}", "-i", video_path, "-vn", "-af", "volumedetect", "-f", "null", "-"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return parse_volumedetect_output(proc.stderr)


def _sample_window_visuals(video_path: str, start_sec: float, duration_sec: float) -> Tuple[float, List[str]]:
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    if fps <= 0 or fps > 120:
        fps = 24.0
    valid_count, motion_sum, frames_b64 = 0, 0.0, []
    prev_gray: Optional[np.ndarray] = None

    for offset_ratio in (0.2, 0.5, 0.8):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int((start_sec + duration_sec * offset_ratio) * fps))
        ret, frame = cap.read()
        if not ret or frame is None:
            continue
        if is_frame_valid(frame, min_brightness=20.0, min_laplacian_var=15.0):
            valid_count += 1
        gray = cv2.cvtColor(cv2.resize(frame, (320, 180)), cv2.COLOR_BGR2GRAY)
        if prev_gray is not None:
            motion_sum += float(np.mean(cv2.absdiff(prev_gray, gray)))
        prev_gray = gray
        if len(frames_b64) < 2:
            small = cv2.resize(frame, (640, int(frame.shape[0] * (640 / max(1, frame.shape[1])))))
            ok, buf = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if ok:
                frames_b64.append(base64.b64encode(buf).decode("utf-8"))
    cap.release()
    visual_score = valid_count * 25.0 + min(25.0, motion_sum)
    return visual_score, frames_b64


async def check_frames_for_ads_or_nsfw(frames_b64: List[str], api_key: Optional[str] = None) -> Dict[str, Any]:
    """Ask Gemini Flash Lite if frames contain gambling banners (Mostbet/1xBet), credits, or NSFW."""
    key = (api_key or os.getenv("GEMINI_API_KEY") or "").strip()
    if not key or not frames_b64:
        return {"is_clean": True, "has_ad_banner": False, "is_nsfw_or_gore": False, "is_credits": False, "excitement_score": 5, "reason": "Vision skipped"}

    prompt = (
        "Inspect these movie frames for social media (Reels/Shorts) safety. "
        "Detect gambling/betting overlay ads (Mostbet, 1xBet, Melbet, Pin-Up, Linebet), end credits, or 18+ nudity/gore. "
        'Return STRICT JSON: {"is_clean": bool, "has_ad_banner": bool, "is_nsfw_or_gore": bool, "is_credits": bool, "excitement_score": 1-10, "reason": "short"}'
    )
    parts: List[Dict[str, Any]] = [{"text": prompt}] + [{"inline_data": {"mime_type": "image/jpeg", "data": b}} for b in frames_b64[:2]]
    for model in ("gemini-flash-lite-latest", "gemini-flash-latest", "gemini-3.5-flash-lite"):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json={"contents": [{"parts": parts}]})
            if resp.status_code == 200:
                text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                return parse_scene_vision_response(text)
        except Exception:
            continue
    return {"is_clean": True, "has_ad_banner": False, "is_nsfw_or_gore": False, "is_credits": False, "excitement_score": 5, "reason": "Vision API fallback"}


async def select_best_scene_start(
    video_path: str,
    clip_duration: float = 45.0,
    scan_start_sec: float = 0.0,
    scan_end_sec: Optional[float] = None,
    check_vision: bool = True,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Score candidate windows by visual quality, motion, audio RMS, and Gemini Vision ad filter."""
    ffmpeg = resolve_ffmpeg_bin()
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    total_dur = (cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps) if fps > 0 else 0.0
    cap.release()

    end_limit = min(total_dur, scan_end_sec) if scan_end_sec else total_dur
    usable_span = max(0.0, end_limit - scan_start_sec - clip_duration)
    step = max(1.0, usable_span / 4.0) if usable_span > 0 else 1.0
    candidates: List[Dict[str, Any]] = []

    curr = scan_start_sec
    while curr <= scan_start_sec + usable_span + 0.01 and len(candidates) < 6:
        vis_score, frames_b64 = _sample_window_visuals(video_path, curr, clip_duration)
        mean_db, _ = _measure_audio_db(ffmpeg, video_path, curr, min(clip_duration, 10.0))
        audio_score = max(0.0, min(50.0, (mean_db + 60.0)))
        candidates.append({"start_sec": round(curr, 2), "score": round(vis_score + audio_score, 2), "mean_volume_db": mean_db, "frames": frames_b64})
        curr += step

    candidates.sort(key=lambda c: c["score"], reverse=True)
    for cand in candidates:
        if not check_vision:
            return {"start_sec": cand["start_sec"], "score": cand["score"], "mean_volume_db": cand["mean_volume_db"], "has_ad_banner": False, "reason": "Audio+Visual top score"}
        v_res = await check_frames_for_ads_or_nsfw(cand["frames"], api_key=api_key)
        if v_res["is_clean"]:
            return {"start_sec": cand["start_sec"], "score": cand["score"] + v_res["excitement_score"] * 3, "mean_volume_db": cand["mean_volume_db"], "has_ad_banner": False, "reason": v_res["reason"]}

    top = candidates[0] if candidates else {"start_sec": round(scan_start_sec, 2), "score": 0.0, "mean_volume_db": -90.0}
    return {"start_sec": top["start_sec"], "score": top["score"], "mean_volume_db": top["mean_volume_db"], "has_ad_banner": True, "reason": "Fallback top window"}
