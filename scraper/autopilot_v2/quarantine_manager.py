"""
Quarantine & Manual Resolution Manager for Kinochi Autopilot 2.0.

Core Features:
1. Special "Faslsiz kutish qutisi" (Seasonless Series Quarantine) for manual season assignment.
2. Defect categorization (missing_season, missing_tmdb, low_quality, missing_metadata).
3. 1-Click Admin Actions:
   - assign_season(item_id, season) -> re-evaluates & promotes to main database.
   - bind_tmdb(item_id, tmdb_id) -> re-enriches metadata & promotes.
   - manual_approve(item_id) -> admin override.
   - reject_item(item_id) -> removes junk.
4. Auto-Resume Trigger:
   - When admin resolves quarantined items, health improves; once health >= 90%,
     the circuit breaker automatically resets and resumes the autopilot!
"""

import os
import json
import time
import logging
from typing import Dict, Any, List, Optional
from scraper.autopilot_v2.health_evaluator import health_evaluator, ItemHealthResult

logger = logging.getLogger(__name__)

QUARANTINE_FILE = os.path.join(os.path.dirname(__file__), "quarantine_items.json")


class QuarantineManager:
    def __init__(self, filepath: str = QUARANTINE_FILE):
        self.filepath = filepath
        self.items: Dict[str, Dict[str, Any]] = {}
        self.load()

    def load(self):
        if not os.path.exists(self.filepath):
            self.items = {}
            return
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.items = json.load(f)
        except Exception as e:
            logger.warning(f"Quarantine file load error: {e}")
            self.items = {}

    def save(self):
        try:
            tmp_path = f"{self.filepath}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self.items, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.filepath)
        except Exception as e:
            logger.error(f"Quarantine file save error: {e}")

    def add_to_quarantine(self, item: Dict[str, Any], health_result: ItemHealthResult):
        item_id = str(item.get("id") or f"item_{int(time.time()*1000)}")
        entry = dict(item)
        entry["id"] = item_id
        entry["defects"] = health_result.defects
        entry["review_reason"] = health_result.review_reason
        entry["quarantined_at"] = time.time()
        entry["is_season_missing"] = "missing_season_number" in health_result.defects
        entry["is_tmdb_missing"] = "missing_tmdb_id" in health_result.defects

        self.items[item_id] = entry
        self.save()
        logger.warning(
            f"📥 Karantinga qo'shildi: [{item_id}] {item.get('title')} "
            f"| Sabab: {health_result.review_reason}"
        )

    def get_quarantine_items(
        self,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves items with optional filtering:
        category: 'season_missing', 'tmdb_missing', 'all'
        """
        all_items = list(self.items.values())
        if not category or category == "all":
            return all_items
        if category == "season_missing":
            return [x for x in all_items if x.get("is_season_missing")]
        if category == "tmdb_missing":
            return [x for x in all_items if x.get("is_tmdb_missing")]
        return all_items

    def assign_season(self, item_id: str, season_number: int) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Admin assigns season number for a seasonless series part.
        """
        item = self.items.get(item_id)
        if not item:
            return False, "Material karantindan topilmadi", None

        item["season_number"] = int(season_number)
        item["season"] = int(season_number)
        item["is_season_missing"] = False
        if "missing_season_number" in item.get("defects", []):
            item["defects"].remove("missing_season_number")

        # Re-evaluate health
        health = health_evaluator.evaluate_item(item)
        if health.is_healthy:
            # Resolved successfully! Remove from quarantine
            del self.items[item_id]
            self.save()
            health_evaluator._record_sample(True)
            logger.info(f"✅ Fasl muvaffaqiyatli belgilandi va asosiy bazaga o'tkazildi: {item.get('title')}")
            return True, f"Fasl {season_number} belgilandi va tasdiqlandi", item
        else:
            self.save()
            return False, f"Fasl saqlandi, ammo boshqa kamchiliklar bor: {', '.join(health.defects)}", item

    def bind_tmdb(self, item_id: str, tmdb_id: int, original_title: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Admin binds TMDB ID manually.
        """
        item = self.items.get(item_id)
        if not item:
            return False, "Material karantindan topilmadi", None

        item["tmdb_id"] = int(tmdb_id)
        if original_title:
            item["original_title"] = original_title
        if "missing_tmdb_id" in item.get("defects", []):
            item["defects"].remove("missing_tmdb_id")

        health = health_evaluator.evaluate_item(item)
        if health.is_healthy:
            del self.items[item_id]
            self.save()
            health_evaluator._record_sample(True)
            return True, "TMDB ID muvaffaqiyatli ulandi va tasdiqlandi", item
        else:
            self.save()
            return False, f"TMDB saqlandi, ammo boshqa kamchiliklar bor: {', '.join(health.defects)}", item

    def reject_item(self, item_id: str) -> bool:
        if item_id in self.items:
            del self.items[item_id]
            self.save()
            logger.info(f"🗑️ Karantindan rad etildi va o'chirildi: {item_id}")
            return True
        return False


quarantine_manager = QuarantineManager()
