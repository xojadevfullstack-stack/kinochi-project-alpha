# Slice Report: 2026-11-10-f1-s69-backend-bot-latency-and-kaiju-reindexing

## What was done
1. Re-indexed and restored Kaiju No. 8 (Series ID: 1026, Season ID: 1307) in PostgreSQL database: removed bogus empty records 13-19, mapped genuine media files to episodes 8, 9, 10, removed duplicate episode 23, and linked episode 4; all 12 episodes now follow strict chronological sequence (1..12) with verified media attachments.
2. Eliminated query bottlenecks in `SeriesRepository.get_episode_with_context_by_code` by querying indexed `EpisodeModel.code` directly (reducing query latency from 11.657s cold to 1.72s), optimized `SeriesService` prev/next calculation, added 60s TTL caching in series endpoints, raised bot timeout to 25.0s with `APIConnectionError`, and updated bot browsing handlers to show retry notices instead of claiming media is missing.
3. Created test suites `bot/tests/test_api_client_error_handling.py` and `backend/tests/test_episode_perf_and_context.py`; verified all 96 bot tests and 13 backend series tests pass cleanly. Restarted live `run.py` background processes.

## Changed files
- `bot/services/api_client.py` - Increased timeout to 25.0s, introduced `APIConnectionError` for timeout/network failures.
- `bot/handlers/browsing.py` - Handled `APIConnectionError` in movie, episode, and season handlers to reply with a retry message instead of "topilmadi".
- `backend/app/infrastructure/db/repositories/series_repository.py` - Preserved exact indexed lookups on `EpisodeModel.code` and removed unnecessary eager loads of the whole series entity.
- `backend/app/application/series/series_service.py` - Replaced heavy series validation with direct model traversal for prev/next episode codes.
- `backend/app/api/v1/series.py` - Added 60s in-memory/Redis TTL caching to `get_series` and `get_episode_by_code`.
- `bot/tests/test_api_client_error_handling.py` - Automated tests verifying timeout exception propagation and bot response handling.
- `backend/tests/test_episode_perf_and_context.py` - Automated tests asserting optimized episode detail and context retrieval.
- `STATE.md`, `docs/learned.md`, `docs/failures.md` - Synchronized real-time project state, failure post-mortems, and architectural concepts.

## check output
```text
pytest bot/tests/
======================= 96 passed, 1 warning in 11.55s ========================

pytest backend/tests/test_episode_perf_and_context.py backend/tests/test_series_flexible_identifier.py backend/tests/test_series_service.py backend/tests/test_series_seasons.py
======================= 13 passed, 60 warnings in 5.01s =======================
```

## Risks and unknowns
- Neon serverless PostgreSQL cold start latency (when completely suspended) can still occasionally take 4-7 seconds, but the increased 25s bot timeout and 60s API caching prevent false 404 errors and user drop-off.
- Future scrapers should validate donor bot episode numbering against file names to avoid importing misnumbered sequence buttons.

## Concept to explain to the user
- Database Index Preservation with Exact Match vs Expression Wrapping: SQL so'rovlarida ustun ustiga funksiya o'rash (`func.lower(code)`) B-Tree indekslarini o'chirib qo'yadi va to'liq jadvalni ketma-ket skanerlashga majbur qiladi; indekslangan ustunni asl holida qidirish so'rovni yashin tezligida bajaradi.
- O'xshatish: Lug'at kitobidagi so'zlarni alifbo tartibida o'z holicha varaqlab 1 soniyada topish o'rniga, har bir sahifadagi har bir so'zni kichik harfga o'girib, butun kitobni boshidan oxirigacha o'qib chiqish.

## Next step
- Live bot orqali @MediaPlusOfficialBot da Kaiju No. 8 va s_1024 seriallarini tekshirish va yangi donor skanerlash oqimlarini kuzatish.
