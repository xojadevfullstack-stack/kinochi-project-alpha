import pytest
from scraper.queue_manager import QueueItem

def test_queue_item_priority_and_season_payload():
    item = QueueItem(
        id="anitoob_227",
        source="anitoob",
        title="Mening qahramonlik akademiyam (1-mavsum)",
        media_type="anime",
        status="pending",
        episodes_count=12,
        downloaded_episodes=0,
        priority=2000,
        tmdb_id=65930,
        payload={"season_number": 1, "franchise": "my_hero_academia", "episodes_count": 12}
    )
    assert item.priority == 2000
    assert item.payload["season_number"] == 1
    assert item.payload["franchise"] == "my_hero_academia"
    assert item.episodes_count == 12

def test_status_priority_ordering():
    status_priority = {
        "in_progress": 0,
        "queued": 1,
        "pending": 1,
        "needs_review": 2,
        "failed": 3,
        "rejected": 4,
        "blacklisted": 5,
        "published": 6,
        "completed": 6,
        "already_exists": 7,
        "discovered": 8,
    }
    
    items = [
        QueueItem(id="item_done", source="anitoob", title="Done", media_type="anime", status="completed", priority=100),
        QueueItem(id="item_s2", source="anitoob", title="S2", media_type="anime", status="pending", priority=1999),
        QueueItem(id="item_active", source="anitoob", title="Active", media_type="anime", status="in_progress", priority=500),
        QueueItem(id="item_s1", source="anitoob", title="S1", media_type="anime", status="pending", priority=2000),
        QueueItem(id="item_failed", source="anitoob", title="Failed", media_type="anime", status="failed", priority=10),
    ]

    sorted_items = sorted(
        items,
        key=lambda i: (status_priority.get(i.status, 99), -int(getattr(i, "priority", 0) or 0))
    )

    expected_ids = ["item_active", "item_s1", "item_s2", "item_failed", "item_done"]
    assert [it.id for it in sorted_items] == expected_ids
