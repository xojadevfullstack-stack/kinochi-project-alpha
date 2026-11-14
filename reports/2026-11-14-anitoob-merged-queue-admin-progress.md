# Slice Report: 2026-11-14-anitoob-merged-queue-admin-progress

## What was done
1. Parsed AniToob completely (319 items, 9,074 episodes), grouped franchises into unified series/movies with sequential priorities (S1 -> S2 -> S3), and assigned verified TMDb IDs.
2. Synchronized database queue (`ingest_items`): 299 queued items, 10 published, 7 redundant duplicates safely set to `already_exists`, 0 rejected/failed.
3. Enhanced Admin Panel `/scraper` progress visibility: enabled episode count progress (`downloaded_episodes / episodes_count qism`) for `anime` media type, and fixed `QueueManager.get_filtered_async` ordering by `priority DESC` within queued status.

## Changed files
- `scraper/queue_manager.py` - Enforced priority-descending ordering in `get_filtered_async` and added `"pending"` / `"completed"` into `status_priority`.
- `admin-panel/app/scraper/page.tsx` - Extended episode counter rendering to include `anime` alongside `series` and `dorama`.
- `scripts/sync_anitoob_merged_queue.py` - Idempotent synchronization utility merging franchise seasons and standalone anime into PostgreSQL queue.
- `backend/tests/test_queue_sorting_and_anime_progress.py` - Regression test asserting priority-based queue sorting and season payload integrity.

## check output
```text
======================= 24 passed, 2 warnings in 4.29s ========================
bot: 15 passed in 3.39s
admin-panel tsc: zero errors
```

## Risks and unknowns
- Download duration: 9,074 episodes across 316 cards require ~10-14 hours due to Telegram FloodWait rate limits (429 handling).
- Redundant cards: 7 duplicate cards are safely marked `already_exists` so that they do not download twice.

## Concept to explain to the user
- Priority Queue (Ustuvorlikka asoslangan navbat): Kasalxonada og'ir bemorlarni birinchi qabul qilgandek, fasllar tartibini buzmaslik uchun 1-mavsumga eng yuqori ball (2000), 2-mavsumga (1999) berilib, tizim ularni qat'iy ketma-ketlikda yuklaydi.

## Next step
- Boshqaruv panelida (Admin Panel `/scraper`) birinchi 5-10 ta birlashtirilgan anime paketini yuklashni boshlash va natijani tekshirish.
