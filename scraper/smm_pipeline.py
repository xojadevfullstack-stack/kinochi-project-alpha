"""End-to-end smart clip generation pipeline (Sparse Download -> Scene Scorer -> 9:16 Render)."""
from __future__ import annotations

import asyncio
import inspect
import os
import tempfile
from typing import Any, Callable, Dict, Optional

from scraper.smm_clipper import compute_clip_window, download_sparse_clip_source, render_vertical_clip
from scraper.smm_scene_finder import find_viral_scene_target
from scraper.smm_scene_scorer import select_best_scene_start


async def _emit_progress(progress_cb: Optional[Callable[[int, str], Any]], pct: int, stage: str) -> None:
    if not progress_cb:
        return
    try:
        res = progress_cb(pct, stage)
        if inspect.isawaitable(res):
            await res
    except Exception:
        pass


async def create_smart_smm_clip(
    client: Any,
    storage_msg: Any,
    output_path: str,
    movie_code: str,
    imdb_rating: Optional[float] = None,
    duration_sec: float = 45.0,
    target_ratio: float = 0.35,
    start_sec: Optional[float] = None,
    check_vision: bool = True,
    blur_watermark: bool = True,
    copyright_shield: bool = False,
    bot_username: str = "@MediaPlusOfficialBot",
    progress_cb: Optional[Callable[[int, str], Any]] = None,
    tmdb_id: Optional[int] = None,
    original_title: Optional[str] = None,
    content_type: str = "movie",
    season_number: Optional[int] = None,
    episode_number: Optional[int] = None,
) -> Dict[str, Any]:
    """Locate viral SRT timecode (with fallback), download targeted sparse chunk, verify with Vision, and render 9:16 clip."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    fd, raw_path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)

    try:
        scene_hint: Optional[Dict[str, Any]] = None
        eff_ratio = target_ratio
        if start_sec is None and tmdb_id:
            await _emit_progress(progress_cb, 10, "Qiziq sahna taymkodi qidirilmoqda...")
            scene_hint = await find_viral_scene_target(
                tmdb_id=tmdb_id,
                title=original_title or "",
                content_type=content_type,
                season_number=season_number,
                episode_number=episode_number,
            )
            if scene_hint and scene_hint.get("target_ratio"):
                eff_ratio = float(scene_hint["target_ratio"])

        await _emit_progress(progress_cb, 15, "Video segment yuklanmoqda...")
        _, total_dur = await download_sparse_clip_source(
            client,
            storage_msg,
            raw_path,
            target_ratio=eff_ratio,
            chunk_mb=None,
        )
        effective_dur = total_dur or 120.0
        await _emit_progress(progress_cb, 45, "AI sahna va reklama tahlili...")
        if start_sec is not None:
            chosen_start, clip_dur = compute_clip_window(effective_dur, duration_sec=duration_sec, start_sec=start_sec)
            score_meta = {"start_sec": chosen_start, "has_ad_banner": False, "score": 0.0, "reason": "Manual start"}
        else:
            chunk_floor = effective_dur * eff_ratio
            if scene_hint and scene_hint.get("peak_sec") and scene_hint.get("srt_end_sec"):
                mapped_peak = effective_dur * (float(scene_hint["peak_sec"]) / float(scene_hint["srt_end_sec"]))
                scan_start = max(chunk_floor, mapped_peak - 70.0)
                scan_end = min(effective_dur - 10.0, max(scan_start + duration_sec + 25.0, mapped_peak + 15.0))
            else:
                scan_start = max(0.0, chunk_floor - 10.0)
                scan_end = min(effective_dur, chunk_floor + duration_sec + 30.0)
            try:
                score_meta = await asyncio.wait_for(
                    select_best_scene_start(
                        raw_path,
                        clip_duration=duration_sec,
                        scan_start_sec=scan_start,
                        scan_end_sec=scan_end,
                        check_vision=check_vision,
                        visual_cue=(scene_hint or {}).get("visual_cue") or None,
                        compare_candidates=3,
                    ),
                    timeout=90.0,
                )
            except asyncio.TimeoutError:
                score_meta = {
                    "start_sec": round(min(max(0.0, scan_start + 5.0), max(0.0, effective_dur - duration_sec)), 2),
                    "has_ad_banner": False,
                    "blur_boxes": [],
                    "score": 0.0,
                    "reason": "Scorer timeout fallback",
                }
            chosen_start, clip_dur = compute_clip_window(effective_dur, duration_sec=duration_sec, start_sec=score_meta["start_sec"])

        blur_ad = bool(score_meta.get("has_ad_banner", False))
        ai_boxes = list(score_meta.get("blur_boxes") or []) if check_vision else None
        low_ram = os.getenv("SMM_LOW_RAM", "true").strip().lower() in {"1", "true", "yes", "on"}
        await _emit_progress(progress_cb, 70, "9:16 vertikal klipp render qilinmoqda...")
        await asyncio.to_thread(
            render_vertical_clip,
            input_path=raw_path,
            output_path=output_path,
            movie_code=movie_code,
            start_sec=chosen_start,
            duration_sec=clip_dur,
            imdb_rating=imdb_rating,
            bot_username=bot_username,
            copyright_shield=copyright_shield,
            blur_watermark=blur_watermark,
            blur_bottom_ad=blur_ad,
            low_ram=low_ram,
            blur_boxes=ai_boxes,
        )
        await _emit_progress(progress_cb, 95, "Telegram preview & bazaga saqlanmoqda...")
        return {
            "output_path": output_path,
            "start_sec": chosen_start,
            "duration_sec": clip_dur,
            "blur_bottom_ad": blur_ad,
            "blur_boxes": ai_boxes or [],
            "scene_score": score_meta.get("score", 0.0),
            "reason": score_meta.get("reason", ""),
        }
    finally:
        if os.path.exists(raw_path):
            try:
                os.remove(raw_path)
            except OSError:
                pass
