"""End-to-end smart clip generation pipeline (Sparse Download -> Scene Scorer -> 9:16 Render)."""
from __future__ import annotations

import os
import tempfile
from typing import Any, Dict, Optional

from scraper.smm_clipper import compute_clip_window, download_sparse_clip_source, render_vertical_clip
from scraper.smm_scene_scorer import select_best_scene_start


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
) -> Dict[str, Any]:
    """Download targeted sparse chunk, score cleanest moment, and render 9:16 clip."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    fd, raw_path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)

    try:
        _, total_dur = await download_sparse_clip_source(
            client, storage_msg, raw_path, target_ratio=target_ratio, chunk_mb=25
        )
        effective_dur = total_dur or 120.0
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
        render_vertical_clip(
            input_path=raw_path,
            output_path=output_path,
            movie_code=movie_code,
            start_sec=chosen_start,
            duration_sec=clip_dur,
            imdb_rating=imdb_rating,
            copyright_shield=copyright_shield,
            blur_watermark=blur_watermark,
            blur_bottom_ad=blur_ad,
        )
        return {
            "output_path": output_path,
            "start_sec": chosen_start,
            "duration_sec": clip_dur,
            "blur_bottom_ad": blur_ad,
            "scene_score": score_meta.get("score", 0.0),
            "reason": score_meta.get("reason", ""),
        }
    finally:
        if os.path.exists(raw_path):
            try:
                os.remove(raw_path)
            except OSError:
                pass
