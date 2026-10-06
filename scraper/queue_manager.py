import os
import json
import time
import logging
import threading
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict, fields

logger = logging.getLogger(__name__)

QUEUE_FILE = os.path.join(os.path.dirname(__file__), "scraper_queue.json")

_FILE_LOCK = threading.RLock()
_QUEUE_FIELDS = None


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


def _known_fields():
    global _QUEUE_FIELDS
    if _QUEUE_FIELDS is None:
        _QUEUE_FIELDS = {f.name for f in fields(QueueItem)}
    return _QUEUE_FIELDS


class QueueManager:
    """
    JSON-file backed queue.

    The file is shared between the scraper subprocess and the API process,
    so every mutation re-reads the file first (to avoid lost updates) and
    writes atomically (tmp file + os.replace) so readers never see a
    half-written file.
    """

    def __init__(self, filepath: str = QUEUE_FILE):
        self.filepath = filepath
        self.items: Dict[str, QueueItem] = {}
        self.load()

    # ── persistence ──────────────────────────────────────────
    def load(self):
        with _FILE_LOCK:
            if not os.path.exists(self.filepath):
                self.items = {}
                return
            data = None
            for attempt in range(5):
                try:
                    with open(self.filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    break
                except Exception as e:
                    logger.warning(f"Queue read attempt {attempt + 1} failed: {e}")
                    time.sleep(0.15)
            if data is None:
                # Keep previously loaded items instead of wiping them.
                logger.error(f"Could not read queue file {self.filepath}; keeping in-memory state.")
                return

            known = _known_fields()
            items: Dict[str, QueueItem] = {}
            for item_dict in data:
                try:
                    clean = {k: v for k, v in item_dict.items() if k in known}
                    item = QueueItem(**clean)
                    items[item.id] = item
                except Exception as e:
                    logger.warning(f"Skipping bad queue entry: {e}")
            self.items = items

    def save(self):
        with _FILE_LOCK:
            tmp_path = f"{self.filepath}.{os.getpid()}.tmp"
            try:
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump([asdict(item) for item in self.items.values()], f, ensure_ascii=False, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                last_err = None
                for _ in range(10):
                    try:
                        os.replace(tmp_path, self.filepath)
                        last_err = None
                        break
                    except PermissionError as e:  # Windows: file briefly locked by a reader
                        last_err = e
                        time.sleep(0.1)
                if last_err:
                    raise last_err
            except Exception as e:
                logger.error(f"Error saving queue to {self.filepath}: {e}")
                try:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                except OSError:
                    pass

    # ── mutations (all reload first to avoid overwriting other process' changes) ──
    def add_item(self, item: QueueItem) -> bool:
        with _FILE_LOCK:
            self.load()
            if item.id in self.items:
                return False
            self.items[item.id] = item
            self.save()
            return True

    def add_items_batch(self, items: List[QueueItem]) -> int:
        with _FILE_LOCK:
            self.load()
            added = 0
            for item in items:
                if item.id not in self.items:
                    self.items[item.id] = item
                    added += 1
            if added > 0:
                self.save()
            return added

    def update_status(
        self,
        item_id: str,
        status: str,
        error_message: Optional[str] = None,
        episodes_count: Optional[int] = None,
        downloaded_episodes: Optional[int] = None,
    ):
        with _FILE_LOCK:
            self.load()
            if item_id in self.items:
                self.items[item_id].status = status
                if episodes_count is not None:
                    self.items[item_id].episodes_count = episodes_count
                if downloaded_episodes is not None:
                    self.items[item_id].downloaded_episodes = downloaded_episodes
                if error_message is not None:
                    self.items[item_id].error_message = error_message
                elif status in ("completed", "pending", "in_progress"):
                    self.items[item_id].error_message = None
                self.save()

    def delete_item(self, item_id: str) -> bool:
        with _FILE_LOCK:
            self.load()
            if item_id in self.items:
                del self.items[item_id]
                self.save()
                return True
            return False

    def update_item_details(
        self,
        item_id: str,
        title: Optional[str] = None,
        year: Optional[int] = None,
        poster_url: Optional[str] = None,
        media_type: Optional[str] = None,
        original_title: Optional[str] = None,
        status: Optional[str] = "pending",
        error_message: Optional[str] = None,
    ) -> bool:
        with _FILE_LOCK:
            self.load()
            if item_id in self.items:
                item = self.items[item_id]
                if title:
                    item.title = title
                if year is not None:
                    item.year = year
                if poster_url is not None:
                    item.poster_url = poster_url
                if media_type is not None:
                    item.media_type = media_type
                if original_title is not None:
                    item.original_title = original_title
                if status is not None:
                    item.status = status
                item.error_message = error_message
                self.save()
                return True
            return False

    def retry_all_failed(self, source: Optional[str] = None) -> int:
        with _FILE_LOCK:
            self.load()
            count = 0
            for item in self.items.values():
                if item.status == "failed" and (not source or item.source == source):
                    item.status = "pending"
                    item.error_message = None
                    count += 1
            if count > 0:
                self.save()
            return count

    def reset_stuck_in_progress(self) -> int:
        """Items left 'in_progress' by a crashed/stopped run go back to pending."""
        with _FILE_LOCK:
            self.load()
            count = 0
            for item in self.items.values():
                if item.status == "in_progress":
                    item.status = "pending"
                    count += 1
            if count > 0:
                self.save()
            return count

    def clear_by_status(self, status: str) -> int:
        with _FILE_LOCK:
            self.load()
            to_delete = [item_id for item_id, item in self.items.items() if item.status == status]
            for item_id in to_delete:
                del self.items[item_id]
            if to_delete:
                self.save()
            return len(to_delete)

    # ── queries ──────────────────────────────────────────────
    def get_item(self, item_id: str) -> Optional[QueueItem]:
        with _FILE_LOCK:
            self.load()
            return self.items.get(item_id)

    def get_item_by_code(self, code: str) -> Optional[QueueItem]:
        with _FILE_LOCK:
            self.load()
            clean_code = str(code).strip()
            for item in self.items.values():
                if item.id.endswith(f"_{clean_code}") or item.id == clean_code:
                    return item
            return None

    def get_pending(self, limit: int = 50, source: Optional[str] = None, media_type: Optional[str] = None) -> List[QueueItem]:
        pending = [
            item for item in self.items.values()
            if item.status == "pending"
            and (not source or item.source == source)
            and (not media_type or item.media_type == media_type)
        ]
        return pending[:limit]

    def get_filtered(
        self,
        status: Optional[str] = None,
        source: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[QueueItem], int]:
        filtered = list(self.items.values())
        if status and status != "all":
            filtered = [item for item in filtered if item.status == status]
        if source and source != "all":
            filtered = [item for item in filtered if item.source == source]
        if search:
            q = search.lower().strip()
            filtered = [
                item for item in filtered
                if (q in (item.title or "").lower())
                or (item.original_title and q in item.original_title.lower())
                or (q in item.id.lower())
            ]

        # in_progress first so the active item is always visible on page 1
        filtered.sort(key=lambda i: 0 if i.status == "in_progress" else 1)
        total_count = len(filtered)
        return filtered[skip: skip + limit], total_count

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
