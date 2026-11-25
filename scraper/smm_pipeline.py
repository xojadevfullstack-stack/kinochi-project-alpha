"""End-to-end smart clip generation pipeline (Sparse Download -> Scene Scorer -> 9:16 Render)."""
from __future__ import annotations

import asyncio
import inspect
import os
import tempfile
from typing import Any, Callable, Dict, Optional

from scraper.smm_clipper import compute_clip_window, download_sparse_clip_source, render_vertical_clip
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
) -> Dict[str, Any]:
    """Download targeted sparse chunk, score cleanest moment, and render 9:16 clip."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    fd, raw_path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)

    try:
        await _emit_progress(progress_cb, 15, "Video segment yuklanmoqda...")
        _, total_dur = await download_sparse_clip_source(
            client,
            storage_msg,
            raw_path,
            target_ratio=target_ratio,
            chunk_mb=None,
        )
        effective_dur = total_dur or 120.0
        await _emit_progress(progress_cb, 45, "AI sahna va reklama tahlili...")
        if start_sec is not None:
            chosen_start, clip_dur = compute_clip_window(effective_dur, duration_sec=duration_sec, start_sec=start_sec)
            score_meta = {"start_sec": chosen_start, "has_ad_banner": False, "score": 0.0, "reason": "Manual start"}
        else:
            center = effective_dur * target_ratio
            scan_start = max(0.0, center - 10.0)
            scan_end = min(effective_dur, center + duration_sec + 30.0)
            score_meta = await select_best_scene_start(
                raw_path,
                clip_duration=duration_sec,
                scan_start_sec=scan_start,
                scan_end_sec=scan_end,
                check_vision=check_vision,
            )
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
