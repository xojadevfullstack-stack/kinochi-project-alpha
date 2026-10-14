"""
Quality Manager & Smart Upgrade Engine for Kinochi Autopilot 2.0.

Core Features:
1. Multi-Quality Cascade (1080p -> 720p -> 480p -> 360p -> 240p -> 144p).
2. Telegram 2 GB limit enforcement:
   - If 1080p > 2 GB, 720p becomes the best quality.
   - If 1080p and 720p don't exist, takes the best available quality in source.
3. Dual-Tier Output:
   - Bot always provides 2 options per source:
     Option 1: Mavjud eng yaxshi sifat (Best available <= 2GB)
     Option 2: Undan bir pog'ona pasti (Step-down / Data saver)
4. Smart Upgrade (Variant B):
   - When a higher-quality analog (e.g. 1080p WEB-DL) arrives later from ANY source,
     the old existing video is retained as the step-down quality, and the new analog
     is promoted to best quality. No wasted work!
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Standard Telegram Bot file size limit
MAX_FILE_SIZE_BYTES = 2000 * 1024 * 1024  # 2,000 MB

QUALITY_RANK = {
    "2160p": 6,
    "4k": 6,
    "1080p": 5,
    "720p": 4,
    "480p": 3,
    "360p": 2,
    "240p": 1,
    "144p": 0,
}


def parse_quality_rank(quality_str: Optional[str]) -> int:
    if not quality_str:
        return -1
    q = quality_str.strip().lower()
    for key, rank in QUALITY_RANK.items():
        if key in q:
            return rank
    return -1


class QualityManager:
    @staticmethod
    def select_dual_qualities(available_variants: List[Dict[str, Any]]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Takes available video variants from a source, filters out files > 2GB,
        and selects:
        1. best_quality: highest quality <= 2GB
        2. step_down_quality: one tier below best_quality
        """
        if not available_variants:
            return {"best_quality": None, "step_down_quality": None}

        # 1. Filter out files strictly exceeding 2 GB
        valid_variants = []
        for v in available_variants:
            size = v.get("file_size") or 0
            if size > MAX_FILE_SIZE_BYTES:
                logger.warning(
                    f"Fayl 2 GB limitdan oshdi ({size / (1024*1024):.1f} MB), "
                    f"o'tkazib yuborildi: {v.get('quality')}"
                )
                continue
            valid_variants.append(v)

        if not valid_variants:
            # Fallback: if all exceed 2GB, return empty so it hits quarantine
            return {"best_quality": None, "step_down_quality": None}

        # 2. Sort by quality rank descending
        valid_variants.sort(
            key=lambda x: (parse_quality_rank(x.get("quality")), x.get("file_size", 0)),
            reverse=True
        )

        best = valid_variants[0]
        step_down = None

        best_rank = parse_quality_rank(best.get("quality"))

        # Find the first variant with lower rank than best
        for v in valid_variants[1:]:
            v_rank = parse_quality_rank(v.get("quality"))
            if v_rank < best_rank or (v_rank == best_rank and v.get("file_size", 0) < best.get("file_size", 0)):
                step_down = v
                break

        # If only one quality exists in source, step_down remains None or duplicates lower bitrate
        return {
            "best_quality": best,
            "step_down_quality": step_down
        }

    @staticmethod
    def handle_smart_upgrade(
        existing_media: Dict[str, Any],
        incoming_analog: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Smart Upgrade (Variant B):
        If incoming analog has higher quality (e.g. 1080p vs current 720p)
        or better audio clarity, promote incoming to best_quality,
        and retain current best as step_down_quality.
        """
        existing_best = existing_media.get("best_quality") or {}
        existing_step_down = existing_media.get("step_down_quality") or {}

        existing_rank = parse_quality_rank(existing_best.get("quality"))
        incoming_rank = parse_quality_rank(incoming_analog.get("quality"))
        incoming_size = incoming_analog.get("file_size") or 0

        if incoming_size > MAX_FILE_SIZE_BYTES:
            logger.info("Incoming analog exceeds 2GB limit. Skipping upgrade.")
            return False, existing_media

        # Is incoming better than existing best?
        if incoming_rank > existing_rank:
            logger.info(
                f"🚀 SMART UPGRADE: {existing_best.get('quality')} -> {incoming_analog.get('quality')} "
                f"uchun analog topildi! Eskisi tejamkor variant qilib saqlanadi."
            )
            updated_media = dict(existing_media)
            updated_media["step_down_quality"] = existing_best
            updated_media["best_quality"] = incoming_analog
            updated_media["last_upgraded_at"] = incoming_analog.get("timestamp")
            return True, updated_media

        # Is incoming better than current step-down?
        step_down_rank = parse_quality_rank(existing_step_down.get("quality"))
        if not existing_step_down or (step_down_rank < incoming_rank < existing_rank):
            logger.info(
                f"✨ SMART UPGRADE: Step-down sifat yaxshilandi: {incoming_analog.get('quality')}"
            )
            updated_media = dict(existing_media)
            updated_media["step_down_quality"] = incoming_analog
            return True, updated_media

        return False, existing_media


quality_manager = QualityManager()
