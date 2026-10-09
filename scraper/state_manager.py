"""
State Manager for Kinochi Scraper & Grabber.
Persists scraper checkpoint, page offsets, rating thresholds, and live bot statuses
so scraping and grabbing can resume seamlessly across restarts without human intervention.
"""

import os
import json
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

STATE_FILE = os.path.join(os.path.dirname(__file__), "scraper_state.json")

DEFAULT_STATE: Dict[str, Any] = {
    "uzmovi_current_page": 1,
    "uzmovi_total_pages": 350,
    "asilmedia_current_page": 1,
    "asilmedia_total_pages": 400,
    "kawaii_current_page": 1,
    "kawaii_total_pages": 50,
    "min_rating": 6.0,
    "autopilot_active": False,
    "autopilot_pages": 3,
    "autopilot_limit": 10,
    "telegram_bot_status": "idle",
    "last_run_timestamp": None,
    "speed_items_per_min": 0.0
}


class StateManager:
    _instance = None

    def __new__(cls, filepath: str = STATE_FILE):
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
            cls._instance.filepath = filepath
            cls._instance.state = dict(DEFAULT_STATE)
            cls._instance.load()
        return cls._instance

    def load(self) -> Dict[str, Any]:
        if not os.path.exists(self.filepath):
            self.state = dict(DEFAULT_STATE)
            self.save()
            return self.state

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Merge with defaults for any missing keys
                merged = dict(DEFAULT_STATE)
                merged.update(data)
                self.state = merged
        except Exception as e:
            logger.warning(f"Error loading scraper state from {self.filepath}: {e}")
            self.state = dict(DEFAULT_STATE)
        return self.state

    def save(self):
        try:
            tmp_path = f"{self.filepath}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.filepath)
        except Exception as e:
            logger.error(f"Error saving scraper state to {self.filepath}: {e}")

    def get_state(self) -> Dict[str, Any]:
        self.load()
        return dict(self.state)

    def update(self, **kwargs) -> Dict[str, Any]:
        self.load()
        for k, v in kwargs.items():
            if k in DEFAULT_STATE or k in self.state:
                self.state[k] = v
        self.save()
        return dict(self.state)

    def advance_page(self, source: str, count: int, from_page: int = None) -> int:
        self.load()
        key = f"{source.lower()}_current_page"
        current = from_page if from_page is not None else int(self.state.get(key, 1))
        new_page = current + count
        self.state[key] = new_page
        self.save()
        logger.info(f"[STATE] {source} sahifasi oshirildi: {current} -> {new_page}")
        return new_page

    def set_bot_status(self, status: str):
        self.load()
        self.state["telegram_bot_status"] = status
        self.save()
