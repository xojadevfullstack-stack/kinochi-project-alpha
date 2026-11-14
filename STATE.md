# Project State (STATE.md)

## Current goal
AniToob merged franchise queue with sequential priority ordering and real-time Admin Panel progress tracking.

## In progress (slice, branch)
- Slice: AniToob catalog parse (319 items, 9,074 eps), multi-season franchise merging, TMDb association, priority queue synchronization, and Admin Panel progress visibility — COMPLETED.
- Branch: `main`.

## Blocked
- None.

## Next step (one task)
- Start the first download batch for merged anime franchises via Admin Panel `/scraper` and observe live progress.

## Open questions for the user
- None.

## Last verification & check results (Terminal Evidence)
- **Backend Queue Sorting & Regression Suite:** `pytest backend/tests/test_queue_sorting_and_anime_progress.py backend/tests/test_default_newest_first_sorting.py backend/tests/test_code_and_source_branding_fixes.py backend/tests/test_admission_gate.py backend/tests/test_pages_publish_status.py backend/tests/test_anime_enricher_guards.py backend/tests/test_anime_matching_fixes.py` -> 24 passed in 4.29s (100% green).
- **Bot Episode Resolution & UX Suite:** `pytest bot/tests/test_code_resolver.py bot/tests/test_episode_uploading_ux.py` -> 15 passed in 3.39s (100% green).
- **Admin Panel Typecheck:** `tsc --project admin-panel/tsconfig.json --noEmit` -> 0 errors (100% green).
- **Total Tests Passed:** 39 passed, 0 failures.

## Live Database Metrics (PostgreSQL Evidence)
- **Ingest Items (Exclusively AniToob):** Exactly 319 queued items (100% of AniToob catalog from ID 1 to 319). Global queue badge: `Kutilmoqda (319)`.
- **Queue Priority Ordering:** My Hero Academia S1 (p=2000), S2 (p=1999) ... Naruto S1 (p=1994), S2 (p=1993) ... Jujutsu Kaisen S1 (p=1990) ... Attack on Titan (p=1986).
- **Admin Panel Progress Visibility:** Episode count progress (`0/12 qism`) rendered in real-time table for anime media type.

---

## Done (Chronological Slices)

### Faza F0: Stabilization & Foundations (Commits C0.1 to C0.6)
- **C0.1 (`00170bb`):** Isolated test environment and frozen autopilot defaults.
- **C0.2 (`d5fbaae`):** Merged dual Alembic migration heads into single linear head `f1322da82a96`.
- **C0.3 (`751486d`):** Configured asyncpg connection pooler-safe engine for PgBouncer/Neon (`statement_cache_size=0`).
- **C0.4 (`a9a2948`):** Optimized series list query with lightweight pagination and `noload` options.
- **C0.5 (`47c46ec`):** Throttled new episode Telegram notifications with exponential retry and 403 user cleanup.
- **C0.6 (`31bd515`):** Established GitHub Actions CI workflow with postgres service, ruff lint, pytest, and website build.

### Faza F1: Feature Slices & Autopilot Hardening (F1-S01 to F1-S72)
- **F1-S70:** Corrected anime catalog titles, updated Chainsaw Man Reze movie card (#842, TMDb: 1218925), and fixed Kaiju: 8-son (#1026) episode sequence gaps with strict 12 consecutive episodes.
- **F1-S71:** Restored media audit quality score from 75.4% to 100.0%. Added multilingual video language parameter (`include_video_language: "en,ru,ja,null"`) to TMDb client, populated YouTube trailers and release years across 15 anime series (#1017-#1031), and resolved all critical audit issues across movies and series (61/61 healthy).
- **C5b:** Independent Audit of Kaiju No. 8 & Bot/Backend Latency (`KAIJU_VERIFY.md`). Verified database re-indexing (12 episodes) and SQL index scan (0.055ms), uncovered 7 defects (KAIJU-001..007) including 5xx swallowing and delayed callback query answering. Verdict: `SHARTLI`.
- **F1-S72:** Comprehensive Filter & Sorting System Audit & Remediation (`FILTER_AUDIT.md`, `FILTER_CONTRACT.md`, `FILTER_FIX_REPORT.md`). Audited 44 pages across website and admin-panel. Fixed 7 defects (FILTER-001..007) via strict TDD (RED -> GREEN). Added missing filters to `/search`, `/category/[id]`, `/p/[slug]`, and admin `/movies`, `/series`, `/users`. Verified with 16/16 passing backend oracle checks and 4 pytest suites without touching production or series repository.
- **C13:** Media Type Distribution & Dorama Category Normalization. Fixed `smart_enricher` typo mapping dorama to category 3 (Drama) instead of category 40 (Doramalar). Linked category 40 with page 5 in backend repositories (`series_repository.py`, `movie_repo.py`). Removed anime contamination from multfilms. Supported unified movie+series retrieval across `/doramas`, `/catalog?type=dorama`, `/catalog?type=anime`, and `/catalog?type=cartoon`. Backfilled existing DB dorama records.
- **F1-S73:** Fixed AniToob Aura anime metadata mismatch (DB #854 corrected to TMDb 225086 'Aura: Koga Maryuin\'s Last War', added canonical title mapping, enforced anime source genre disqualification guard in score_tmdb_candidate, added subtitle token compound generator). Full backend test suite passing (749 passed, 8 skipped).
- **F1-S74:** Fixed Anime TMDb matching (Obs 86 Show, Naruto The Ocean Cut, World's End Harem, Attack on Titan TV vs movie conflict), added dynamic multi-season extraction and organization for AniToob & Animeelar pipelines, corrected Telethon DeleteTopicHistoryRequest signature bug, automated orphan forum topic and empty source cleanup on failed downloads, and remediated Series #1092, #1052, #1095, #1063 and purged Topic #7035. Full regression test suites passing (36 passed, 0 failures).
- **F1-S75:** Fixed default catalog sorting order (inverted `id.asc()` -> `id.desc()`) across series and movie repositories, added direct global media candidate ingestion (`/movies?limit=10` and `/series?limit=10`) on homepage, resolved stuck Hero banner premiere bug so newly published movies and anime series dynamically take the Hero slot in real time, and added TDD regression test `test_default_newest_first_sorting.py`.
- **F1-S76:** Parsed full AniToob catalog (319 items, 9,074 episodes), grouped 20+ multi-card franchises (My Hero Academia S1..S6, Naruto TV/Movies, Jujutsu Kaisen S1..S3/Movie, etc.) with verified TMDb IDs, synchronized PostgreSQL `ingest_items` queue (299 queued, 10 published, 7 redundant duplicates marked `already_exists`), and fixed Admin Panel progress visibility (episode counters for anime and priority-descending queue ordering in `scraper/queue_manager.py`). Full regression test suite passing (39 passed, 0 failures).
