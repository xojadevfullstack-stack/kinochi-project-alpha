"""
Anime Health Router & Smart Source Selector for Kinochi Autopilot 2.0.

Core Features:
1. Health-based selection between Anitoob and Animeelar:
   - Evaluates video quality, audio/subtitle cleanliness, metadata completeness.
   - If Anitoob has better or equal health -> Anitoob selected.
   - If Animeelar has better health -> Animeelar selected.
2. Fast-Release with Subsequent Upgrade:
   - If Animeelar releases a new episode earlier, ingest it immediately so users
     don't wait.
   - When Anitoob releases the superior quality/health analog, automatically
     upgrade/replace it!
"""

import logging
from typing import Dict, Any, Optional, Tuple
from scraper.autopilot_v2.health_evaluator import health_evaluator, ItemHealthResult
from scraper.autopilot_v2.quality_manager import parse_quality_rank

logger = logging.getLogger(__name__)


class AnimeHealthRouter:
    @staticmethod
    def calculate_anime_source_score(item: Dict[str, Any]) -> int:
        """
        Calculates a competitive score (0-100) between Animeelar and Anitoob.
        Takes into account:
        - Health evaluation
        - Video resolution rank
        - Subtitle/Audio clarity tag
        - File size <= 2GB
        """
        health_res = health_evaluator.evaluate_item(item)
        if not health_res.is_healthy:
            return 0  # Zero tolerance: defective source gets 0

        score = 50  # Base healthy score

        # Video resolution bonus
        q_rank = parse_quality_rank(item.get("quality"))
        score += q_rank * 6  # 1080p gets +30, 720p gets +24

        # Voiceover / Dubbing studio bonus
        audio = (item.get("voiceover") or item.get("language") or "").lower()
        if "dublyaj" in audio or "prof" in audio:
            score += 15
        elif "subtitr" in audio:
            score += 10

        # Anitoob preference bonus when qualities are tied
        source = (item.get("source") or "").lower()
        if source == "anitoob":
            score += 5  # Anitoob is curated, gets tie-breaker edge

        return min(score, 100)

    @classmethod
    def choose_best_source(
        cls,
        anitoob_variant: Optional[Dict[str, Any]],
        animeelar_variant: Optional[Dict[str, Any]]
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Chooses the winning variant based on health score.
        Returns: (winning_variant, reason)
        """
        if not anitoob_variant and not animeelar_variant:
            return None, "Ikkala manbada ham mavjud emas"

        if not anitoob_variant:
            return animeelar_variant, "Faqat Animeelarda mavjud"

        if not animeelar_variant:
            return anitoob_variant, "Faqat Anitoobda mavjud"

        score_anitoob = cls.calculate_anime_source_score(anitoob_variant)
        score_animeelar = cls.calculate_anime_source_score(animeelar_variant)

        logger.info(
            f"Anime manbalari baholandi: Anitoob={score_anitoob} ball, Animeelar={score_animeelar} ball"
        )

        if score_anitoob >= score_animeelar:
            return anitoob_variant, f"Anitoob salomatligi yuqoriroq ({score_anitoob} vs {score_animeelar})"
        else:
            return animeelar_variant, f"Animeelar salomatligi yuqoriroq ({score_animeelar} vs {score_anitoob})"


anime_health_router = AnimeHealthRouter()
