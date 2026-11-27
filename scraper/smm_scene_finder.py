"""Open-source SRT subtitle scene-timecode lookup for viral SMM clip selection."""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)
_GEMINI_SCENE_MODELS = ("gemini-flash-lite-latest", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite")


def sanitize_hook_text(raw_hook: str, movie_title: str = "", max_chars: int = 44) -> str:
    """Clean emojis/hashtags, enforce word length, and block movie-title spoilers in hooks."""
    raw_low = (raw_hook or "").lower()
    title_words = [w.lower() for w in re.findall(r"[A-Za-z0-9\u0400-\u04ff']+", movie_title or "") if len(w) >= 4]
    if any(w in raw_low for w in title_words):
        return ""
    txt = re.sub(r"#\S+", "", raw_hook or "")
    txt = "".join(ch for ch in txt if (32 <= ord(ch) <= 126) or ch in "‘’“”–—" or ("\u0400" <= ch <= "\u04ff"))
    txt = re.sub(r"\s+", " ", txt).strip(" \t\r\n\"'«»")
    if not txt:
        return ""
    if len(txt) > max_chars:
        cut = txt[: max_chars - 1].rsplit(" ", 1)[0].strip()
        txt = (cut or txt[: max_chars - 1]).rstrip(",;:") + "..."
    return txt


def fallback_hook_for_genres(genres: Optional[str] = None) -> str:
    """Return a punchy Uzbek intrigue hook tailored to movie genre without spoilers."""
    low = (genres or "").lower()
    if any(k in low for k in ("triller", "thriller", "sirli", "mystery", "detektiv")):
        return "Oxirida nima bo'lishini kutmagandingiz!"
    if any(k in low for k in ("jangari", "ekshn", "action", "sarguzasht")):
        return "Bu kadrni oxirigacha ko'ring!"
    if any(k in low for k in ("fantastika", "sci-fi", "fentezi")):
        return "Bunday burilishni hech kim kutmagan edi!"
    if "anime" in low:
        return "Eng kuchli anime sahnalardan biri!"
    if any(k in low for k in ("komediya", "comedy")):
        return "Kulmasdan oxirigacha ko'ra olasizmi?"
    if any(k in low for k in ("qo'rqinchli", "horror", "dahshat")):
        return "Yolg'iz ko'rish tavsiya etilmaydi!"
    return "Bu sahnadan keyin hamma hayratda qoldi!"


def parse_srt_blocks(srt_text: str) -> List[Tuple[float, float, str]]:
    """Parse SRT captions into (start_sec, end_sec, text) tuples."""
    blocks: List[Tuple[float, float, str]] = []
    pattern = re.compile(
        r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*\r?\n([\s\S]*?)(?=\r?\n\r?\n|\Z)"
    )
    for m in pattern.finditer(srt_text or ""):
        sh, sm, ss, sms, eh, em, es, ems, body = m.groups()
        start = int(sh) * 3600 + int(sm) * 60 + int(ss) + int(sms) / 1000.0
        end = int(eh) * 3600 + int(em) * 60 + int(es) + int(ems) / 1000.0
        clean = re.sub(r"<[^>]+>", "", body).replace("\r", " ").replace("\n", " ").strip()
        if clean:
            blocks.append((start, end, clean))
    return blocks


def compress_srt_for_llm(blocks: List[Tuple[float, float, str]], bucket_sec: Optional[int] = None) -> str:
    """Group timestamped SRT lines into adaptive ~30-60s buckets for accurate LLM timecode lookup."""
    if not blocks:
        return ""
    if bucket_sec is None:
        span = float(blocks[-1][1])
        eff_bucket = 30 if span <= 3600 else (45 if span <= 7200 else 60)
    else:
        eff_bucket = max(15, int(bucket_sec))
    buckets: Dict[int, List[str]] = {}
    for start, _, txt in blocks:
        buckets.setdefault(int(start // eff_bucket), []).append(txt)
    lines = []
    for b in sorted(buckets):
        t = b * eff_bucket
        mm, ss = divmod(t, 60)
        lines.append(f"[{t}s / {mm:02d}:{ss:02d}] {' | '.join(buckets[b])[:220]}")
    return "\n".join(lines)


async def fetch_imdb_id(tmdb_id: int, content_type: str = "movie") -> Optional[str]:
    """Resolve IMDb ID (tt...) from TMDb external_ids endpoint."""
    try:
        from app.infrastructure.external.tmdb_client import tmdb_client

        kind = "tv" if content_type in {"tv", "series", "episode"} else "movie"
        data = await tmdb_client._request_with_retry(f"/{kind}/{int(tmdb_id)}/external_ids", {})
        imdb_id = (data or {}).get("imdb_id")
        return str(imdb_id).strip() if imdb_id else None
    except Exception as exc:
        logger.debug("TMDb external_ids lookup skipped for %s/%s: %s", content_type, tmdb_id, exc)
        return None


async def fetch_stremio_srt(
    imdb_id: str,
    content_type: str = "movie",
    season_number: Optional[int] = None,
    episode_number: Optional[int] = None,
) -> Optional[str]:
    """Fetch English or Russian SRT text from public keyless Stremio OpenSubtitles endpoint."""
    if not imdb_id:
        return None
    if content_type in {"tv", "series", "episode"} and season_number and episode_number:
        meta_url = f"https://opensubtitles-v3.strem.io/subtitles/series/{imdb_id}:{int(season_number)}:{int(episode_number)}.json"
    else:
        meta_url = f"https://opensubtitles-v3.strem.io/subtitles/movie/{imdb_id}.json"
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(meta_url)
            if resp.status_code != 200:
                return None
            subs = resp.json().get("subtitles") or []
            chosen = next((s for lang in ("eng", "en", "rus", "ru") for s in subs if (s.get("lang") or "").lower() == lang and s.get("url")), None)
            if not chosen:
                chosen = next((s for s in subs if s.get("url")), None)
            if not chosen:
                return None
            srt_resp = await client.get(chosen["url"])
            return srt_resp.text if srt_resp.status_code == 200 and srt_resp.text else None
    except Exception as exc:
        logger.debug("Stremio SRT fetch skipped (%s): %s", imdb_id, exc)
        return None


async def _ask_gemini_scene_timecode(
    title: str,
    srt_end_sec: float,
    digest: str,
    season_number: Optional[int] = None,
    episode_number: Optional[int] = None,
    api_key: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Ask Gemini Flash-Lite for the most viral/plot-twist/climax timecode and visual cue."""
    key = (api_key or os.getenv("GEMINI_API_KEY") or "").strip()
    if not key or not digest:
        return None
    ep_tag = f" Season {season_number} Episode {episode_number}" if season_number and episode_number else ""
    prompt = (
        f"Analyze the timestamped subtitle digest of '{title}'{ep_tag} (span: {int(srt_end_sec)}s).\n"
        "Pick peak_sec at the EXACT peak climax/action/plot-twist moment (NOT slow buildup beforehand) for a 25-30s Reel/Short, "
        "plus a strong backup_peak_sec earlier (25%-75% of span) in case the finale overlaps credits.\n"
        "Avoid first 120s intro recaps and NEVER pick timestamps in the final 6% (end credits) of the span.\n"
        "Also write a punchy 3-6 word Uzbek intrigue hook (`hook_uz`) and YouTube Shorts hook title (`yt_title_uz`) WITHOUT revealing the movie title or ending.\n"
        'Return STRICT JSON ONLY: {"start_sec": int, "peak_sec": int, "backup_peak_sec": int, "visual_cue": "short visual description", "reason_uz": "1 short Uzbek sentence", "hook_uz": "3-6 word Uzbek hook", "yt_title_uz": "short Uzbek YT title"}\n\n'
        f"SUBTITLE DIGEST:\n{digest}"
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}}
    async with httpx.AsyncClient(timeout=25.0) as client:
        for model in _GEMINI_SCENE_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            try:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    continue
                txt = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                match = re.search(r"\{[\s\S]*\}", txt)
                if match:
                    return json.loads(match.group(0))
            except Exception as exc:
                logger.debug("Gemini SRT scene finder %s fallback: %s", model, exc)
    return None


async def find_viral_scene_target(
    tmdb_id: Optional[int],
    title: str,
    content_type: str = "movie",
    season_number: Optional[int] = None,
    episode_number: Optional[int] = None,
    api_key: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Return {peak_sec, srt_end_sec, target_ratio, visual_cue, reason_uz} or None if unavailable."""
    if not tmdb_id or int(tmdb_id) <= 0:
        return None
    imdb_id = await fetch_imdb_id(int(tmdb_id), content_type=content_type)
    if not imdb_id:
        return None
    srt_text = await fetch_stremio_srt(imdb_id, content_type=content_type, season_number=season_number, episode_number=episode_number)
    blocks = parse_srt_blocks(srt_text or "")
    if len(blocks) < 3:
        return None
    srt_end = max(120.0, float(blocks[-1][1]))
    pick = await _ask_gemini_scene_timecode(
        title=title,
        srt_end_sec=srt_end,
        digest=compress_srt_for_llm(blocks),
        season_number=season_number,
        episode_number=episode_number,
        api_key=api_key,
    )
    if not pick:
        return None
    try:
        peak = float(pick.get("peak_sec") or pick.get("start_sec") or 0)
    except (TypeError, ValueError):
        return None
    if peak <= 0:
        return None
    max_safe_peak = max(120.0, srt_end - 45.0)
    peak = min(peak, max_safe_peak)
    anchor_sec = max(60.0, peak - 35.0)
    backup_ratio: Optional[float] = None
    try:
        backup_peak = float(pick.get("backup_peak_sec") or 0)
        if 120.0 <= backup_peak < peak - 90.0:
            backup_ratio = round(max(0.15, min(0.78, (backup_peak - 35.0) / srt_end)), 4)
    except (TypeError, ValueError):
        backup_ratio = None
    hook_uz = sanitize_hook_text(str(pick.get("hook_uz") or ""), movie_title=title)
    yt_title_uz = sanitize_hook_text(str(pick.get("yt_title_uz") or ""), movie_title=title, max_chars=58)
    return {
        "peak_sec": peak,
        "srt_end_sec": srt_end,
        "target_ratio": round(max(0.05, min(0.91, anchor_sec / srt_end)), 4),
        "backup_ratio": backup_ratio,
        "visual_cue": str(pick.get("visual_cue") or "").strip(),
        "reason_uz": str(pick.get("reason_uz") or "").strip(),
        "hook_uz": hook_uz,
        "yt_title_uz": yt_title_uz or hook_uz,
    }
