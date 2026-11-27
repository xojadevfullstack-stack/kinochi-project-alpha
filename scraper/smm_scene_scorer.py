"""Smart Scene Scorer & Gemini Vision Ad/NSFW Filter for SMM Clips (Slice 1.5)."""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import re
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover - optional when OpenCV shared libs are unavailable
    cv2 = None
import httpx
import numpy as np

from scraper.smm_clipper import resolve_ffmpeg_bin
from scraper.video_verifier import is_frame_valid

logger = logging.getLogger(__name__)
_MODEL_COOLDOWN_UNTIL: Dict[str, float] = {}
_CORNER_ROIS: Tuple[Tuple[str, Tuple[float, float, float, float], Dict[str, Any]], ...] = (
    ("top_left", (0.00, 0.00, 0.28, 0.20), {"x": 0.01, "y": 0.02, "w": 0.24, "h": 0.16, "kind": "watermark"}),
    ("top_right", (0.68, 0.00, 0.32, 0.20), {"x": 0.74, "y": 0.02, "w": 0.25, "h": 0.16, "kind": "watermark"}),
    ("bottom_left", (0.00, 0.72, 0.30, 0.28), {"x": 0.01, "y": 0.78, "w": 0.26, "h": 0.18, "kind": "watermark"}),
    ("bottom_right", (0.58, 0.70, 0.42, 0.30), {"x": 0.62, "y": 0.72, "w": 0.37, "h": 0.26, "kind": "watermark"}),
)


def detect_static_corner_watermarks(frames_b64: List[str], min_static_ratio: float = 0.014) -> List[Dict[str, Any]]:
    """Detect persistent static corner logos/watermarks across >=2 frames via OpenCV Canny intersection."""
    if cv2 is None or len(frames_b64) < 2:
        return []
    imgs = []
    for b64 in frames_b64[:3]:
        try:
            arr = np.frombuffer(base64.b64decode(b64), dtype=np.uint8)
            im = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if im is not None and im.size > 0:
                imgs.append(im)
        except Exception:
            continue
    if len(imgs) < 2:
        return []
    h, w = imgs[0].shape[:2]
    f1, f2 = imgs[0], imgs[-1]
    if f2.shape[:2] != (h, w):
        f2 = cv2.resize(f2, (w, h))
    boxes: List[Dict[str, Any]] = []
    for _, (rx, ry, rw, rh), box in _CORNER_ROIS:
        x0, y0, x1, y1 = int(rx * w), int(ry * h), int((rx + rw) * w), int((ry + rh) * h)
        if x1 <= x0 + 8 or y1 <= y0 + 8:
            continue
        g1 = cv2.cvtColor(f1[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
        g2 = cv2.cvtColor(f2[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
        e1 = cv2.Canny(g1, 60, 160) > 0
        e2 = cv2.Canny(g2, 60, 160) > 0
        if float(np.mean(e1 & e2)) >= min_static_ratio:
            boxes.append(dict(box))
    return boxes


def parse_volumedetect_output(stderr_text: str) -> Tuple[float, float]:
    """Parse FFmpeg volumedetect stderr for (mean_volume_db, max_volume_db)."""
    mean_m = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", stderr_text or "")
    max_m = re.search(r"max_volume:\s*([-\d.]+)\s*dB", stderr_text or "")
    return (float(mean_m.group(1)) if mean_m else -90.0), (float(max_m.group(1)) if max_m else -90.0)


def _sanitize_blur_boxes(raw_boxes: Any) -> List[Dict[str, Any]]:
    """Clamp Gemini Vision normalized blur boxes to safe foreground coordinates."""
    if not isinstance(raw_boxes, list):
        return []
    safe: List[Dict[str, Any]] = []
    for item in raw_boxes[:4]:
        if not isinstance(item, dict):
            continue
        try:
            x = max(0.0, min(0.95, float(item.get("x", 0.0))))
            y = max(0.0, min(0.95, float(item.get("y", 0.0))))
            w = float(item.get("w", 0.0))
            h = float(item.get("h", 0.0))
        except (TypeError, ValueError):
            continue
        if w < 0.025 or h < 0.025:
            continue
        kind = str(item.get("kind", "watermark"))[:16]
        if kind == "watermark" and (w < 0.10 or h < 0.06):
            pad_x, pad_y = max(0.015, (0.14 - w) / 2.0), max(0.015, (0.09 - h) / 2.0)
            x = max(0.0, x - (pad_x if x > 0.05 else 0.0))
            y = max(0.0, y - (pad_y if y > 0.05 else 0.0))
            w = max(w + 2 * pad_x, 0.14)
            h = max(h + 2 * pad_y, 0.09)
        if kind == "watermark" and (x >= 0.75 or y >= 0.75):
            if x >= 0.75:
                shift_x = min(x, 0.035)
                x -= shift_x
                w += shift_x + 0.01
            if y >= 0.75:
                shift_y = min(y, 0.035)
                y -= shift_y
                h += shift_y + 0.01
        w = min(w, 0.85, 1.0 - x)
        h = min(h, 0.45, 1.0 - y)
        if w < 0.04 or h < 0.04:
            continue
        safe.append({"x": round(x, 3), "y": round(y, 3), "w": round(w, 3), "h": round(h, 3), "kind": kind})
    return safe


def _infer_corner_watermark_boxes(reason: str) -> List[Dict[str, Any]]:
    """Recover corner watermark box when Vision mentions a visible logo in prose but leaves blur_boxes empty."""
    low = (reason or "").lower()
    if not low or re.search(r"\b(no|without|none|free of)\s+(?:any\s+|visible\s+|corner\s+|site\s+)?(watermark|logo|overlay)", low):
        return []
    if not re.search(r"(watermark|logo|kinochilar|asilmedia|uzmovi|aslanbe)", low):
        return []
    if re.search(r"(bottom|lower)[- ]right", low):
        return [{"x": 0.78, "y": 0.80, "w": 0.22, "h": 0.20, "kind": "watermark"}]
    if re.search(r"(bottom|lower)[- ]left", low):
        return [{"x": 0.0, "y": 0.80, "w": 0.22, "h": 0.20, "kind": "watermark"}]
    if re.search(r"(top|upper)[- ]right", low):
        return [{"x": 0.77, "y": 0.0, "w": 0.23, "h": 0.18, "kind": "watermark"}]
    if re.search(r"(top|upper)[- ]left", low):
        return [{"x": 0.0, "y": 0.0, "w": 0.24, "h": 0.18, "kind": "watermark"}]
    return []


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
        reason_str = str(data.get("reason", ""))
        boxes = _sanitize_blur_boxes(data.get("blur_boxes")) or _infer_corner_watermark_boxes(reason_str)
        unsafe_scene = has_ad or is_nsfw or is_credits
        # A corner source logo/watermark can be blurred out dynamically via blur_boxes without rejecting the scene
        is_clean = True if (not unsafe_scene and boxes) else bool(data.get("is_clean", not unsafe_scene))
        return {
            "is_clean": is_clean,
            "has_ad_banner": has_ad,
            "is_nsfw_or_gore": is_nsfw,
            "is_credits": is_credits,
            "excitement_score": int(data.get("excitement_score", 5)),
            "cue_match": int(data.get("cue_match", 5)),
            "blur_boxes": boxes,
            "vision_used": True,
            "reason": str(data.get("reason", "")),
        }
    except Exception:
        return {
            "is_clean": True, "has_ad_banner": False, "is_nsfw_or_gore": False,
            "is_credits": False, "excitement_score": 5, "cue_match": 5, "blur_boxes": [],
            "vision_used": False, "reason": "Fallback clean",
        }


def _measure_audio_db(ffmpeg: str, video_path: str, start_sec: float, probe_dur: float) -> Tuple[float, float]:
    cmd = [ffmpeg, "-ss", f"{start_sec:.2f}", "-t", f"{probe_dur:.2f}", "-i", video_path, "-vn", "-af", "volumedetect", "-f", "null", "-"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return parse_volumedetect_output(proc.stderr)
    except Exception as exc:
        logger.debug("Audio volumedetect timeout/skip at %.1fs: %s", start_sec, exc)
        return -90.0, -90.0


def _sample_window_visuals(video_path: str, start_sec: float, duration_sec: float) -> Tuple[float, List[str]]:
    if cv2 is None:
        return 10.0, []
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


def _extract_frames_ffmpeg_b64(ffmpeg: str, video_path: str, start_sec: float, duration_sec: float) -> List[str]:
    """Extract up to 2 JPEG frames via ffmpeg when OpenCV sparse seeking returns no frames."""
    frames: List[str] = []
    for offset_ratio in (0.25, 0.7):
        ts = max(0.0, float(start_sec) + max(1.0, float(duration_sec)) * offset_ratio)
        cmd = [
            ffmpeg, "-y", "-ss", f"{ts:.2f}", "-i", video_path,
            "-frames:v", "1", "-vf", "scale=640:-2", "-q:v", "4",
            "-f", "image2pipe", "-vcodec", "mjpeg", "-",
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, timeout=15)
            if proc.returncode == 0 and proc.stdout:
                frames.append(base64.b64encode(proc.stdout).decode("utf-8"))
        except Exception:
            continue
    return frames


async def check_frames_for_ads_or_nsfw(
    frames_b64: List[str],
    api_key: Optional[str] = None,
    visual_cue: Optional[str] = None,
) -> Dict[str, Any]:
    """Ask Gemini Vision to inspect safety, watermark boxes, excitement, and optional iconic cue match."""
    key = (api_key or os.getenv("GEMINI_API_KEY") or "").strip()
    if not key or not frames_b64:
        return {
            "is_clean": True, "has_ad_banner": False, "is_nsfw_or_gore": False,
            "is_credits": False, "excitement_score": 5, "cue_match": 5, "blur_boxes": [],
            "vision_used": False, "reason": "Vision skipped",
        }

    cue_note = f'Target iconic scene cue: "{visual_cue}". Rate cue_match (1-10) for how well frames match this scene. ' if visual_cue else ""
    prompt = (
        "Inspect these movie frames for social media (Reels/Shorts) safety, corner watermark/logo detection, and scene excitement. "
        f"{cue_note}"
        "1) Carefully check ALL FOUR CORNERS (top-left, top-right, bottom-left, bottom-right) — even dark or semi-transparent areas — for overlaid website/channel watermarks/logos "
        "(e.g. Kinochilar, ASILMEDIA.NET, UZMOVI, ASLANBE STUDIO, @channel) or betting ad banners (Mostbet, 1xBet, Melbet, Pin-Up, Linebet). "
        "2) CONSISTENCY RULE: Whenever ANY watermark/logo/ad is visible in ANY corner (even small or faint), you MUST include its normalized [0.0-1.0] box in blur_boxes with generous padding; NEVER mention a watermark/logo in reason while returning blur_boxes: []. Return [] ONLY if all four corners are genuinely clean. "
        "3) Set is_clean=true if there is no NSFW/gore, no end credits, and no gambling ad banner (corner site watermarks can be blurred safely). Ignore dialogue subtitles and normal movie props.\n"
        "4) Score excitement_score STRICTLY: 8-10 ONLY for gripping action, intense confrontation, shock reveal, or high emotion; 1-4 for calm walking, static dialogue, or slow buildup.\n"
        'Return STRICT JSON: {"is_clean": bool, "has_ad_banner": bool, "is_nsfw_or_gore": bool, "is_credits": bool, "excitement_score": 1-10, "cue_match": 1-10, "blur_boxes": [{"x": 0.0, "y": 0.0, "w": 0.2, "h": 0.1, "kind": "watermark"}], "reason": "short"}'
    )
    parts: List[Dict[str, Any]] = [{"text": prompt}] + [{"inline_data": {"mime_type": "image/jpeg", "data": b}} for b in frames_b64[:2]]
    payload = {"contents": [{"parts": parts}], "generationConfig": {"responseMimeType": "application/json"}}
    now_mono = time.monotonic()
    for model in ("gemini-3.1-flash-lite", "gemini-flash-lite-latest", "gemini-2.5-flash-lite", "gemini-3.5-flash-lite"):
        if _MODEL_COOLDOWN_UNTIL.get(model, 0.0) > now_mono:
            continue
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                parsed = parse_scene_vision_response(text)
                if parsed.get("vision_used"):
                    return parsed
                logger.warning("Gemini Vision %s unparseable JSON: %s", model, text[:180])
                continue
            logger.warning("Gemini Vision %s HTTP %s: %s", model, resp.status_code, resp.text[:180])
            if resp.status_code == 429:
                _MODEL_COOLDOWN_UNTIL[model] = now_mono + 120.0
            if resp.status_code in (401, 403):
                break
        except Exception as exc:
            logger.warning("Gemini Vision %s error: %s", model, type(exc).__name__)
            continue
    return {
        "is_clean": True, "has_ad_banner": False, "is_nsfw_or_gore": False,
        "is_credits": False, "excitement_score": 5, "blur_boxes": [],
        "vision_used": False, "reason": "Vision API fallback",
    }


async def select_best_scene_start(
    video_path: str,
    clip_duration: float = 45.0,
    scan_start_sec: float = 0.0,
    scan_end_sec: Optional[float] = None,
    check_vision: bool = True,
    api_key: Optional[str] = None,
    visual_cue: Optional[str] = None,
    compare_candidates: int = 1,
) -> Dict[str, Any]:
    """Score candidate windows by visual quality, motion, audio RMS, and Gemini Vision ad filter."""
    ffmpeg = resolve_ffmpeg_bin()
    total_dur = 0.0
    if cv2 is not None:
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
        vis_score, frames_b64 = await asyncio.to_thread(_sample_window_visuals, video_path, curr, clip_duration)
        mean_db, _ = await asyncio.to_thread(_measure_audio_db, ffmpeg, video_path, curr, min(clip_duration, 10.0))
        audio_score = max(0.0, min(50.0, (mean_db + 60.0)))
        candidates.append({"start_sec": round(curr, 2), "score": round(vis_score + audio_score, 2), "mean_volume_db": mean_db, "frames": frames_b64})
        curr += step

    candidates.sort(key=lambda c: c["score"], reverse=True)
    top_v_res: Optional[Dict[str, Any]] = None
    best_clean: Optional[Dict[str, Any]] = None
    merged_boxes: List[Dict[str, Any]] = []
    evaluated_clean = 0
    for idx, cand in enumerate(candidates):
        if not check_vision:
            return {"start_sec": cand["start_sec"], "score": cand["score"], "mean_volume_db": cand["mean_volume_db"], "has_ad_banner": False, "blur_boxes": [], "vision_used": False, "reason": "Audio+Visual top score"}
        frames = cand.get("frames") or []
        if not frames:
            frames = await asyncio.to_thread(_extract_frames_ffmpeg_b64, ffmpeg, video_path, cand["start_sec"], clip_duration)
        v_res = (
            await check_frames_for_ads_or_nsfw(frames, api_key=api_key, visual_cue=visual_cue)
            if visual_cue
            else await check_frames_for_ads_or_nsfw(frames, api_key=api_key)
        )
        if idx == 0:
            top_v_res = v_res
        if v_res["is_clean"]:
            cv_boxes = [] if v_res.get("vision_used") else detect_static_corner_watermarks(frames)
            for box in list(v_res.get("blur_boxes") or []) + cv_boxes:
                if not any(abs(box["x"] - b["x"]) < 0.12 and abs(box["y"] - b["y"]) < 0.12 for b in merged_boxes):
                    merged_boxes.append(box)
            scored_cand = {
                "start_sec": cand["start_sec"],
                "score": round(cand["score"] + int(v_res.get("excitement_score", 5)) * 12 + int(v_res.get("cue_match", 5)) * (16 if visual_cue else 0), 2),
                "mean_volume_db": cand["mean_volume_db"],
                "has_ad_banner": bool(v_res.get("has_ad_banner", False)),
                "blur_boxes": list(merged_boxes[:4]),
                "vision_used": bool(v_res.get("vision_used", False)),
                "reason": v_res["reason"],
            }
            if best_clean is None or scored_cand["score"] > best_clean["score"]:
                best_clean = scored_cand
            else:
                best_clean["blur_boxes"] = list(merged_boxes[:4])
            evaluated_clean += 1
            if evaluated_clean >= max(1, compare_candidates):
                break
    if best_clean is not None:
        return best_clean

    top = candidates[0] if candidates else {"start_sec": round(scan_start_sec, 2), "score": 0.0, "mean_volume_db": -90.0}
    top_v = top_v_res or {}
    return {
        "start_sec": top["start_sec"],
        "score": top["score"],
        "mean_volume_db": top["mean_volume_db"],
        "has_ad_banner": bool(top_v.get("has_ad_banner", True)),
        "is_credits": bool(top_v.get("is_credits", False)),
        "blur_boxes": top_v.get("blur_boxes", []),
        "vision_used": bool(top_v.get("vision_used", False)),
        "reason": "Fallback top window",
    }
