import os
import json
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

QUEUE_FILE = os.path.join(os.path.dirname(__file__), "scraper_queue.json")

@dataclass
class QueueItem:
    id: str                   # Unique identifier (e.g. uzmovi_8997, asilmedia_18509)
    source: str               # "uzmovi" or "asilmedia"
    title: str                # Title in Uzbek (e.g. "Odisseya")
    original_title: Optional[str] = None # English/Russian title
    year: Optional[int] = None
    media_type: str = "movie" # "movie" or "series"
    url: str = ""             # URL on the site
    poster_url: Optional[str] = None
    status: str = "pending"   # pending, in_progress, completed, failed, already_exists
    episodes_count: Optional[int] = None
    downloaded_episodes: int = 0
    error_message: Optional[str] = None

class QueueManager:
    def __init__(self, filepath: str = QUEUE_FILE):
        self.filepath = filepath
        self.items: Dict[str, QueueItem] = {}
        self.load()

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item_dict in data:
                        item = QueueItem(**item_dict)
                        self.items[item.id] = item
                logger.info(f"Loaded {len(self.items)} items from queue.")
            except Exception as e:
                logger.error(f"Error loading queue from {self.filepath}: {e}")
        else:
            self.items = {}

    def save(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump([asdict(item) for item in self.items.values()], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving queue to {self.filepath}: {e}")

    def add_item(self, item: QueueItem) -> bool:
        if item.id in self.items:
            return False  # Already exists
        self.items[item.id] = item
        self.save()
        return True

    def add_items_batch(self, items: List[QueueItem]) -> int:
        added = 0
        for item in items:
            if item.id not in self.items:
                self.items[item.id] = item
                added += 1
        if added > 0:
            self.save()
        return added

    def get_pending(self, limit: int = 50, source: Optional[str] = None, media_type: Optional[str] = None) -> List[QueueItem]:
        pending = [
            item for item in self.items.values()
            if item.status == "pending"
            and (not source or item.source == source)
            and (not media_type or item.media_type == media_type)
        ]
        return pending[:limit]

    def update_status(self, item_id: str, status: str, error_message: Optional[str] = None):
        if item_id in self.items:
            self.items[item_id].status = status
            if error_message is not None:
                self.items[item_id].error_message = error_message
            self.save()

    def delete_item(self, item_id: str) -> bool:
        if item_id in self.items:
            del self.items[item_id]
            self.save()
            return True
        return False

    def retry_item(self, item_id: str) -> bool:
        if item_id in self.items:
            self.items[item_id].status = "pending"
            self.items[item_id].error_message = None
            self.save()
            return True
        return False

    def retry_all_failed(self, source: Optional[str] = None) -> int:
        count = 0
        for item in self.items.values():
            if item.status == "failed" and (not source or item.source == source):
                item.status = "pending"
                item.error_message = None
                count += 1
        if count > 0:
            self.save()
        return count

    def clear_by_status(self, status: str) -> int:
        to_delete = [item_id for item_id, item in self.items.items() if item.status == status]
        for item_id in to_delete:
            del self.items[item_id]
        if to_delete:
            self.save()
        return len(to_delete)

    def get_filtered(
        self,
        status: Optional[str] = None,
        source: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[QueueItem], int]:
        filtered = list(self.items.values())
        if status and status != "all":
            filtered = [item for item in filtered if item.status == status]
        if source and source != "all":
            filtered = [item for item in filtered if item.source == source]
        if search:
            q = search.lower().strip()
            filtered = [
                item for item in filtered
                if (q in item.title.lower())
                or (item.original_title and q in item.original_title.lower())
                or (q in item.id.lower())
            ]
        
        # Newest or pending items first (reversed if appropriate)
        total_count = len(filtered)
        paged_items = filtered[skip : skip + limit]
        return paged_items, total_count

    def stats(self) -> Dict[str, int]:
        total = len(self.items)
        pending = sum(1 for i in self.items.values() if i.status == "pending")
        completed = sum(1 for i in self.items.values() if i.status == "completed")
        already_exists = sum(1 for i in self.items.values() if i.status == "already_exists")
        failed = sum(1 for i in self.items.values() if i.status == "failed")
        in_progress = sum(1 for i in self.items.values() if i.status == "in_progress")
        return {
            "total": total,
            "pending": pending,
            "completed": completed,
            "already_exists": already_exists,
            "failed": failed,
            "in_progress": in_progress,
        }

