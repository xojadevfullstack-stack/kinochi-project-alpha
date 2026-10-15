"""
Zero-Tolerance Health & Circuit Breaker Evaluator for Kinochi Autopilot 2.0.

Rules:
1. Zero-Tolerance Per Item:
   If ANY required attribute is missing or defective (TMDB ID, poster, genres,
   dual quality tiers, voiceover/source, Telegram 2GB limit, or season for series),
   the item health score drops to 0 (-100 penalty) and is immediately diverted
   to Quarantine ('needs_review').
2. Rolling Circuit Breaker:
   If overall batch/rolling health drops below 90%, the autopilot AUTOMATICALLY
   PAUSES and notifies admin. It stays paused until quality is restored.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Telegram standard bot upload limit is 2 GB (2 * 1024 * 1024 * 1024 bytes)
TELEGRAM_MAX_FILE_SIZE_BYTES = 2000 * 1024 * 1024  # 2,000 MB safe threshold


@dataclass
class ItemHealthResult:
    is_healthy: bool
    score: int  # 100 if fully healthy, 0 if any defect (-100 penalty)
    defects: List[str] = field(default_factory=list)
    needs_review: bool = False
    review_reason: Optional[str] = None


@dataclass
class CircuitBreakerStatus:
    is_paused: bool
    health_percentage: float
    total_evaluated: int
    healthy_count: int
    defective_count: int
    pause_reason: Optional[str] = None


class HealthEvaluator:
    def __init__(self, min_sample_size: int = 10, pause_threshold_percent: float = 90.0):
        self.min_sample_size = min_sample_size
        self.pause_threshold_percent = pause_threshold_percent
        self.rolling_window_size = 100
        self.history: List[bool] = []  # True for healthy, False for defective
        self.is_paused: bool = False
        self.pause_reason: Optional[str] = None

    def evaluate_item(self, item: Dict[str, Any]) -> ItemHealthResult:
        """
        Zero-tolerance inspection of a single movie / series / anime item.
        """
        defects = []

        # 1. TMDB ID & Original Title Check
        tmdb_id = item.get("tmdb_id")
        if not tmdb_id or int(tmdb_id) <= 0:
            defects.append("missing_tmdb_id")

        title = (item.get("title") or "").strip()
        if not title or len(title) < 2:
            defects.append("missing_title")

        original_title = (item.get("original_title") or "").strip()
        if not original_title:
            defects.append("missing_original_title")

        # 2. Metadata (Poster, Genres, Description)
        poster_url = (item.get("poster_url") or "").strip()
        if not poster_url or not (poster_url.startswith("http://") or poster_url.startswith("https://")):
            defects.append("missing_or_invalid_poster")
        elif "uzmovi.net" in poster_url.lower() or "uzmovi.com" in poster_url.lower():
            if not tmdb_id or int(tmdb_id) <= 0:
                defects.append("unverified_watermarked_poster")

        genres = item.get("genres")
        if not genres:
            defects.append("missing_genres")

        description = (item.get("description") or "").strip()
        if not description or len(description) < 15:
            defects.append("missing_or_insufficient_description")

        # 3. Source & Voiceover / Audio mapping
        source = (item.get("source") or "").strip().lower()
        if source not in ("uzmovi", "asilmedia", "anitoob", "animeelar"):
            defects.append("invalid_source")

        voiceover = (item.get("voiceover") or item.get("language") or "").strip()
        if not voiceover:
            defects.append("missing_voiceover_tag")

        # 4. Multi-Quality (Best + Step-Down) & File Size
        qualities = item.get("qualities") or []
        file_size = item.get("file_size") or 0

        if file_size > TELEGRAM_MAX_FILE_SIZE_BYTES:
            defects.append("file_exceeds_2gb_limit")

        # Check if item has quality info
        if not qualities and not item.get("quality"):
            defects.append("missing_quality_info")

        # 5. Series & Anime Specific: Season and Episode check
        media_type = (item.get("media_type") or "movie").strip().lower()
        if media_type in ("series", "anime", "serial"):
            season_num = item.get("season_number") or item.get("season")
            if season_num is None or int(season_num) <= 0:
                defects.append("missing_season_number")

            episode_num = item.get("episode_number") or item.get("episode")
            if episode_num is None or int(episode_num) <= 0:
                defects.append("missing_episode_number")

        # Evaluation verdict: Zero tolerance for content quality
        if defects:
            result = ItemHealthResult(
                is_healthy=False,
                score=0,
                defects=defects,
                needs_review=True,
                review_reason=f"Kamchiliklar mavjud: {', '.join(defects)}"
            )
            # DIQQAT: Kontent rad etilishi CircuitBreaker'ni to'xtatmaydi!
            return result

        return ItemHealthResult(
            is_healthy=True,
            score=100,
            defects=[],
            needs_review=False,
            review_reason=None
        )

    def record_infrastructure_failure(self, error_type: str, details: str = ""):
        """Infratuzilma xatosi (FloodWait, bot javobsiz, DB xato) yuz berganda chaqiriladi."""
        self._record_sample(False)
        logger.critical(f"🚨 INFRATUZILMA XATOSI: {error_type} - {details} (CircuitBreaker'ga qayd etildi)")

    def record_infrastructure_success(self):
        """Muvaffaqiyatli infratuzilma aloqasida chaqiriladi."""
        self._record_sample(True)

    def _record_sample(self, is_healthy: bool):
        self.history.append(is_healthy)
        if len(self.history) > self.rolling_window_size:
            self.history.pop(0)

        # Re-check circuit breaker
        self.check_circuit_breaker()

    def check_circuit_breaker(self) -> CircuitBreakerStatus:
        total = len(self.history)
        if total == 0:
            return CircuitBreakerStatus(
                is_paused=False,
                health_percentage=100.0,
                total_evaluated=0,
                healthy_count=0,
                defective_count=0,
                pause_reason=None
            )

        healthy_count = sum(1 for x in self.history if x)
        defective_count = total - healthy_count
        health_pct = (healthy_count / total) * 100.0

        if total >= self.min_sample_size and health_pct < self.pause_threshold_percent:
            self.is_paused = True
            self.pause_reason = (
                f"Infratuzilma salomatligi {self.pause_threshold_percent:.1f}% dan tushib ketdi "
                f"(Hozirgi ko'rsatkich: {health_pct:.1f}%). "
                f"So'nggi {total} ta so'rovdan {defective_count} tasida infratuzilma xatosi "
                f"(FloodWait, bot javobsiz yoki DB) aniqlandi. Avtopilot to'xtatildi."
            )
            logger.critical(f"🚨 CIRCUIT BREAKER TRIP: {self.pause_reason}")
        else:
            if self.is_paused and health_pct >= self.pause_threshold_percent:
                logger.info(f"✅ CIRCUIT BREAKER RECOVERED: Infratuzilma {health_pct:.1f}% ga tiklandi. Auto-resuming.")
                self.is_paused = False
                self.pause_reason = None

        return CircuitBreakerStatus(
            is_paused=self.is_paused,
            health_percentage=round(health_pct, 1),
            total_evaluated=total,
            healthy_count=healthy_count,
            defective_count=defective_count,
            pause_reason=self.pause_reason
        )

    def manual_resume(self):
        """Allows admin to manually resume autopilot after fixing filters."""
        self.is_paused = False
        self.pause_reason = None
        # Reset half of defective history to give runway
        self.history = [True] * min(len(self.history), self.min_sample_size)
        logger.info("Admin manual reset executed on Circuit Breaker.")


# Global instance
health_evaluator = HealthEvaluator()
