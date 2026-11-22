import os
import re
import json
import base64
import tempfile
import asyncio
try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover - optional on headless slim containers without libglib
    cv2 = None
import numpy as np
import httpx
from typing import List, Dict, Any, Optional

def is_frame_valid(frame: np.ndarray, min_brightness: float = 15.0, min_laplacian_var: float = 30.0) -> bool:
    """Checks if a frame is not solid black, solid color, or overly blurred."""
    if frame is None or frame.size == 0:
        return False
    if cv2 is None:
        mean_val = float(np.mean(frame))
        return min_brightness <= mean_val <= 250.0 and float(np.std(frame)) >= 5.0
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean_val = float(np.mean(gray))
    if mean_val < min_brightness or mean_val > 250.0:
        return False
    var_val = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    return var_val >= min_laplacian_var

def parse_vision_response(raw_text: str) -> Dict[str, Any]:
    """Parses JSON response from Gemini Vision, with regex fallback if truncated."""
    cleaned = raw_text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if match:
        cleaned = match.group(1).strip()
    else:
        brace_match = re.search(r"(\{[\s\S]*\})", cleaned)
        if brace_match:
            cleaned = brace_match.group(1).strip()
    try:
        data = json.loads(cleaned)
        if not isinstance(data, dict):
            raise ValueError("Expected JSON object")
        return {
            "is_match": bool(data.get("is_match", False)),
            "confidence": str(data.get("confidence", "LOW")).upper(),
            "detected_title": str(data.get("detected_title", "")),
            "detected_season": data.get("detected_season"),
            "detected_episode": data.get("detected_episode"),
            "reason": str(data.get("reason", ""))
        }
    except Exception as e:
        m_match = re.search(r'"is_match"\s*:\s*(true|false)', raw_text, re.IGNORECASE)
        m_conf = re.search(r'"confidence"\s*:\s*"([^"]+)"', raw_text, re.IGNORECASE)
        m_title = re.search(r'"detected_title"\s*:\s*"([^"]+)"', raw_text)
        m_s = re.search(r'"detected_season"\s*:\s*(\d+|null)', raw_text)
        m_e = re.search(r'"detected_episode"\s*:\s*(\d+|null)', raw_text)
        m_r = re.search(r'"reason"\s*:\s*"([^"\n\r]*)', raw_text)
        if m_title:
            return {
                "is_match": bool(m_match and m_match.group(1).lower() == "true"),
                "confidence": (m_conf.group(1).upper() if m_conf else "MEDIUM"),
                "detected_title": m_title.group(1).strip(),
                "detected_season": int(m_s.group(1)) if (m_s and m_s.group(1).isdigit()) else None,
                "detected_episode": int(m_e.group(1)) if (m_e and m_e.group(1).isdigit()) else None,
                "reason": m_r.group(1).strip() if m_r else "Extracted via regex fallback"
            }
        return {
            "is_match": False,
            "confidence": "LOW",
            "detected_title": "",
            "detected_season": None,
            "detected_episode": None,
            "reason": f"JSON parse error: {e}. Raw: {raw_text[:200]}"
        }

class VideoVerifier:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-3.5-flash-lite"):
        if not api_key:
            from dotenv import load_dotenv
            load_dotenv("backend/.env")
            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY", "")
        self.api_key = api_key
        self.model_name = model_name
        self.fallback_model = "gemini-3.1-flash-lite"

    def _get_endpoint_url(self, model: str) -> str:
        return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"

    async def extract_frames_from_message(
        self,
        client: Any,
        message: Any,
        num_frames: int = 3,
        chunk_size_mb: int = 15,
        return_metadata: bool = False
    ) -> Any:
        """Fast streaming download of partial video chunk from Telegram and keyframe extraction.
        Supports sparse moov atom stitching for MP4 files and native format detection for MKV.
        Extracts up to num_frames distinct non-black frames across different opening timestamps."""
        if not message or not message.media:
            return [] if not return_metadata else []
        
        frames_b64: List[str] = []
        frames_meta: List[Dict[str, Any]] = []
        doc = getattr(message.media, "document", None) if hasattr(message.media, "document") else None
        mime = getattr(doc, "mime_type", "") if doc else ""
        is_mkv = "matroska" in mime or "webm" in mime
        file_suffix = ".mkv" if is_mkv else ".mp4"

        with tempfile.NamedTemporaryFile(suffix=file_suffix, delete=False) as tmp:
            tmp_path = tmp.name

        try:
            chunk_start = bytearray()
            max_bytes = chunk_size_mb * 1024 * 1024
            async for chunk in client.iter_download(message.media, offset=0, request_size=1024 * 1024):
                chunk_start.extend(chunk)
                if len(chunk_start) >= max_bytes:
                    break

            total_size = getattr(doc, "size", None) if doc else len(chunk_start)

            # Check if moov is present at start. For non-MKV MP4 files without FastStart, stitch moov from end
            if not is_mkv and b"moov" not in chunk_start and total_size and total_size > len(chunk_start):
                end_fetch_bytes = min(total_size, 10 * 1024 * 1024)
                end_offset = max(0, total_size - end_fetch_bytes)
                chunk_end = bytearray()
                async for chunk in client.iter_download(message.media, offset=end_offset, request_size=1024 * 1024):
                    chunk_end.extend(chunk)

                moov_idx = chunk_end.find(b"moov")
                if moov_idx != -1 and moov_idx >= 4:
                    atom_start_in_end = moov_idx - 4
                    moov_data = chunk_end[atom_start_in_end:]
                    moov_file_offset = end_offset + atom_start_in_end
                    with open(tmp_path, "wb") as f:
                        f.write(chunk_start)
                        f.seek(moov_file_offset)
                        f.write(moov_data)
                else:
                    with open(tmp_path, "wb") as f:
                        f.write(chunk_start)
            else:
                with open(tmp_path, "wb") as f:
                    f.write(chunk_start)

            cap = cv2.VideoCapture(tmp_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
            if fps <= 0 or fps > 120:
                fps = 24.0

            # Seek across distinct timestamps past studio intros (65s, 85s, 45s, 30s, 20s...)
            candidate_seconds = [65, 85, 45, 55, 35, 25, 40, 20, 15, 10, 5]
            seen_seconds = []
            for sec in candidate_seconds:
                # Ensure spacing of at least 4 seconds between extracted frames
                if any(abs(sec - s) < 4 for s in seen_seconds):
                    continue
                pos = int(sec * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
                ret, frame = cap.read()
                if ret and is_frame_valid(frame):
                    seen_seconds.append(sec)
                    h, w = frame.shape[:2]
                    if w > 720:
                        new_w = 720
                        new_h = int(h * (720 / w))
                        frame = cv2.resize(frame, (new_w, new_h))
                    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                    b64_str = base64.b64encode(buffer).decode("utf-8")
                    timecode = f"{sec//60:02d}:{sec%60:02d}"
                    frames_b64.append(b64_str)
                    frames_meta.append({
                        "second": sec,
                        "timecode": timecode,
                        "b64": b64_str
                    })
                    if len(frames_b64) >= num_frames:
                        break

            # Robust fallback: sequential stepping if fewer than num_frames extracted
            if len(frames_b64) < num_frames:
                step = max(int(fps * 3), 15)
                curr = int(fps * 2)
                for _ in range(30):
                    if len(frames_b64) >= num_frames:
                        break
                    curr += step
                    cap.set(cv2.CAP_PROP_POS_FRAMES, curr)
                    ret, frame = cap.read()
                    if not ret:
                        break
                    if is_frame_valid(frame):
                        sec = int(curr / fps)
                        if any(abs(sec - s) < 2 for s in seen_seconds):
                            continue
                        seen_seconds.append(sec)
                        h, w = frame.shape[:2]
                        if w > 720:
                            new_w = 720
                            new_h = int(h * (720 / w))
                            frame = cv2.resize(frame, (new_w, new_h))
                        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                        b64_str = base64.b64encode(buffer).decode("utf-8")
                        timecode = f"{sec//60:02d}:{sec%60:02d}"
                        frames_b64.append(b64_str)
                        frames_meta.append({
                            "second": sec,
                            "timecode": timecode,
                            "b64": b64_str
                        })
            cap.release()
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

        if return_metadata:
            return frames_meta
        return frames_b64

    async def verify_content(
        self,
        frames_b64: List[str],
        expected_title: str,
        expected_type: str = "series",
        expected_season: Optional[int] = None,
        expected_episode: Optional[int] = None
    ) -> Dict[str, Any]:
        """Sends frames to Gemini Vision and asserts matching against expected title/season/episode with retry & fallback."""
        if not frames_b64:
            return {
                "is_match": False,
                "confidence": "NONE",
                "detected_title": "",
                "detected_season": None,
                "detected_episode": None,
                "reason": "No valid frames could be extracted from video"
            }

        prompt = f"""You are an elite video content verification system for a cinema streaming platform.
Our database expects this video to be:
- Title: {expected_title}
- Media Type: {expected_type}
- Season: {expected_season}
- Episode: {expected_episode}

Analyze the provided video frame(s) and determine if this video MATCHES the expected content.
IMPORTANT RULES:
1. Note that '{expected_title}' may be an Uzbek or Russian translated title of an international movie/series/anime. If the visual frames match the movie/series corresponding to '{expected_title}', set "is_match": true.
2. If the frames only show generic studio logos, distributor intros, website watermarks (e.g. Kinochilar, Asilmedia, Uzmovi), or generic opening credits where a DIFFERENT specific movie cannot be 100% proven, set "is_match": true and "detected_title": "".
3. Set "is_match": false ONLY if you can positively identify a DIFFERENT specific movie, series, or anime in the frames.
Return STRICT JSON in this exact structure:
{{
  "is_match": true/false,
  "confidence": "HIGH" / "MEDIUM" / "LOW",
  "detected_title": "Exact title of movie/series/anime you identified (or empty string if generic intro)",
  "detected_season": integer or null,
  "detected_episode": integer or null,
  "reason": "Brief reason in 1 sentence explaining matches or discrepancies"
}}
"""
        parts = [{"text": prompt}]
        for fb in frames_b64:
            parts.append({"inline_data": {"mime_type": "image/jpeg", "data": fb}})

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 512}
        }
        models_to_try = [self.model_name, self.fallback_model]

        async with httpx.AsyncClient(timeout=45.0) as http_client:
            for model in models_to_try:
                endpoint = self._get_endpoint_url(model)
                for attempt in range(3):
                    try:
                        resp = await http_client.post(endpoint, json=payload)
                        if resp.status_code == 200:
                            res_json = resp.json()
                            raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                            return parse_vision_response(raw_text)
                        elif resp.status_code == 429:
                            # Rate limit hit, backoff and retry
                            wait_time = (attempt + 1) * 3
                            print(f"[RETRY] Model {model} hit 429, waiting {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue
                        elif resp.status_code in (500, 503, 504):
                            wait_time = (attempt + 1) * 2
                            print(f"[RETRY] Model {model} server error {resp.status_code}, waiting {wait_time}s...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            print(f"[WARN] Model {model} returned HTTP {resp.status_code}: {resp.text[:100]}")
                            break
                    except (httpx.TimeoutException, httpx.NetworkError) as e:
                        print(f"[RETRY] Model {model} network error ({e}), retrying...")
                        await asyncio.sleep(2.0)
                        continue

        return {
            "is_match": False,
            "confidence": "ERROR",
            "detected_title": "",
            "detected_season": None,
            "detected_episode": None,
            "reason": "All Gemini vision models exhausted or unavailable"
        }
