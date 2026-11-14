# Project State (STATE.md)

## Current goal
Fix episode code resolution (unique code vs display code), multi-source branding badges (Kinochilar, AniToob, Animeelar, Uzmovi), and scraper needs_review state transitions.

## In progress (slice, branch)
- Slice: Episode unique code indexing, multi-source badges in admin/web, and scraper queue transition stability — COMPLETED.
- Branch: `main`.

## Blocked
- None.

## Next step (one task)
- Verification of Telegram bot direct code searches with unique codes.

## Open questions for the user
- None.

## Last verification & check results (Terminal Evidence)
- **Backend Code & Source Branding Suite:** `pytest backend/tests/test_code_and_source_branding_fixes.py backend/tests/test_admission_gate.py backend/tests/test_pages_publish_status.py` -> 15 passed in 3.01s (100% green).
- **Bot Episode Resolution & UX Suite:** `pytest bot/tests/test_code_resolver.py bot/tests/test_episode_uploading_ux.py` -> 15 passed in 4.02s (100% green).
- **Total Tests Passed:** 30 passed, 0 failures.


## Live Database Metrics (PostgreSQL Evidence)
- **Movies (Kinolar):** 31 ta (100% sog'lom)
- **Series (Seriallar):** 35 ta (100% sog'lom)
- **Content Requests (So'rovlar):** 15 ta (100% boyitilgan, faol TOP-15 tavsiya ro'yxati)
- **Catalog Default View:** Barcha kinolar va seriallar birlashtirilib reyting / sana / ID bo'yicha to'liq ko'rsatilmoqda.

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
