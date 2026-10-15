"""
Autopilot 2.0 Main Engine for Kinochi Project.

Coordinates:
- HealthEvaluator (Zero-tolerance health & 90% Circuit Breaker)
- QualityManager (Multi-Quality Cascade, 2GB Limit, Smart Upgrade Variant B)
- AnimeHealthRouter (Anitoob vs Animeelar Health-based Routing)
- QuarantineManager (Faslsiz kutish qutisi & Manual resolution)
- SeedGenerator (TMDB Top + Uzbek Most Viewed priority seeds)
"""

import time
import logging
from typing import Dict, Any, Optional, Tuple, List
from scraper.autopilot_v2.health_evaluator import health_evaluator, ItemHealthResult, CircuitBreakerStatus
from scraper.autopilot_v2.quality_manager import quality_manager
from scraper.autopilot_v2.anime_health_router import anime_health_router
from scraper.autopilot_v2.quarantine_manager import quarantine_manager
from scraper.autopilot_v2.seed_generator import seed_generator

logger = logging.getLogger(__name__)


class AutopilotEngine:
    def __init__(self):
        self.health_evaluator = health_evaluator
        self.quality_manager = quality_manager
        self.anime_router = anime_health_router
        self.quarantine_manager = quarantine_manager
        self.seed_generator = seed_generator
        self.processed_count: int = 0
        self.approved_count: int = 0
        self.quarantined_count: int = 0

    def process_incoming_media(self, raw_item: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Main Ingestion Pipeline for a single media item.
        Returns: (success, message, processed_item)
        """
        # 1. Circuit Breaker Check
        cb_status = self.health_evaluator.check_circuit_breaker()
        if cb_status.is_paused:
            logger.warning(f"⛔ AVTOPILOT TO'XTATILGAN (PAUSED): {cb_status.pause_reason}")
            return False, f"Avtopilot to'xtatilgan: {cb_status.pause_reason}", raw_item

        self.processed_count += 1

        # 2. Anime Source Health Check (if applicable)
        if (raw_item.get("media_type") or "").lower() == "anime":
            anitoob_variant = raw_item.get("anitoob_variant")
            animeelar_variant = raw_item.get("animeelar_variant")
            if anitoob_variant or animeelar_variant:
                winner, reason = self.anime_router.choose_best_source(anitoob_variant, animeelar_variant)
                if winner:
                    raw_item.update(winner)
                    raw_item["source_selection_reason"] = reason

        # 3. Quality Cascade & Dual Tier Selection
        variants = raw_item.get("variants") or []
        if variants:
            dual_qualities = self.quality_manager.select_dual_qualities(variants)
            raw_item["best_quality"] = dual_qualities.get("best_quality")
            raw_item["step_down_quality"] = dual_qualities.get("step_down_quality")
            if raw_item["best_quality"]:
                raw_item["file_size"] = raw_item["best_quality"].get("file_size", 0)
                raw_item["quality"] = raw_item["best_quality"].get("quality")

        # 4. Zero-Tolerance Health Inspection
        health_result = self.health_evaluator.evaluate_item(raw_item)

        if not health_result.is_healthy:
            # Kamchilik aniqlandi! Non-blocking: karantinga oladi va navbat davom etadi
            self.quarantined_count += 1
            self.quarantine_manager.add_to_quarantine(raw_item, health_result)
            logger.warning(f"⚠️ Kontent sifati qoniqarsiz: {health_result.review_reason}. Karantinga olindi, navbat davom etadi.")
            return False, f"Kamchilik aniqlandi va karantinga olindi: {health_result.review_reason}", raw_item

        # 5. Fully Healthy Item: Approved for DB insertion!
        self.approved_count += 1
        raw_item["status"] = "healthy_approved"
        logger.info(f"🌟 100% SOG'LOM MEDIA TASDIQLANDI: [{raw_item.get('source')}] {raw_item.get('title')}")
        return True, "100% Sog'lom va bazaga yozishga tayyor", raw_item

    def get_engine_status(self) -> Dict[str, Any]:
        cb = self.health_evaluator.check_circuit_breaker()
        quarantine_items = self.quarantine_manager.get_quarantine_items()
        return {
            "is_paused": cb.is_paused,
            "pause_reason": cb.pause_reason,
            "health_percentage": cb.health_percentage,
            "total_evaluated": cb.total_evaluated,
            "healthy_count": cb.healthy_count,
            "defective_count": cb.defective_count,
            "quarantine_pending_count": len(quarantine_items),
            "season_missing_count": len([x for x in quarantine_items if x.get("is_season_missing")]),
            "tmdb_missing_count": len([x for x in quarantine_items if x.get("is_tmdb_missing")]),
            "lifetime_processed": self.processed_count,
            "lifetime_approved": self.approved_count,
        }


autopilot_engine = AutopilotEngine()
