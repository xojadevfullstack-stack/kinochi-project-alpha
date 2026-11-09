# Project State (STATE.md)

## Current goal
MediaPlus / Kinochi barcha filtr va saralash tizimini audit qilish va tuzatish (`FILTER_AUDIT.md`, `FILTER_CONTRACT.md`, `FILTER_FIX_REPORT.md`).

## In progress (slice, branch)
- Slice: F1-S72: Filter & Sorting System Remediation (`FILTER_FIX_REPORT.md`).
- Branch: `filters/fix-all`

## Blocked
- None (All 7 filter bugs fixed, verified with Oracle & Pytest, waiting for user review).

## Next step (one task)
- User review of `FILTER_FIX_REPORT.md` and decision on Director API (separate route vs actors department filter).

## Open questions for the user
- Director API: Hozirda rejissyorlar `/actors` sahifasida `department: "Directing"` roli bilan qatnashmoqda. Ularni alohida `/directors` sahifasiga ajratamizmi yoki `/actors` ichida "Rejissyorlar" tabi qo'shamizmi?

## Last verification & check results (Terminal Evidence)
- **Filter Regression Suite (pytest):** 4 passed in 3.86s (`pytest backend/tests/test_filter_*.py`).
- **Backend Filter Oracle Suite:** 16 PASS | 0 FAIL | 1 MAVJUD EMAS (`python scratch/audit_backend_oracle.py`).
- **TypeScript Static Verification:**
  * Website: `tsc -p website/tsconfig.json --noEmit` -> 0 errors.
  * Admin-Panel: `tsc -p admin-panel/tsconfig.json --noEmit` -> 0 errors.

## Live Database Metrics (PostgreSQL Evidence)
- **Movies (Kinolar):** 29 ta (100% sog'lom)
- **Series (Seriallar):** 32 ta (100% sog'lom)
- **Episodes (Qismlar):** 948 ta
- **Users (Foydalanuvchilar):** 49 ta
- **Scraper Queue (`ingest_items`):** 50 ta
  * `queued`: 42 ta
  * `already_exists`: 5 ta
  * `published`: 2 ta
  * `in_progress`: 1 ta

---

## Done (Chronological Slices)

### Faza F0: Stabilization & Foundations (Commits C0.1 to C0.6)
- **C0.1 (`00170bb`):** Isolated test environment and frozen autopilot defaults.
- **C0.2 (`d5fbaae`):** Merged dual Alembic migration heads into single linear head `f1322da82a96`.
- **C0.3 (`751486d`):** Configured asyncpg connection pooler-safe engine for PgBouncer/Neon (`statement_cache_size=0`).
- **C0.4 (`a9a2948`):** Optimized series list query with lightweight pagination and `noload` options.
- **C0.5 (`47c46ec`):** Throttled new episode Telegram notifications with exponential retry and 403 user cleanup.
- **C0.6 (`31bd515`):** Established GitHub Actions CI workflow with postgres service, ruff lint, pytest, and website build.

### Faza F1: Feature Slices & Autopilot Hardening (F1-S01 to F1-S71)
- **F1-S70:** Corrected anime catalog titles, updated Chainsaw Man Reze movie card (#842, TMDb: 1218925), and fixed Kaiju: 8-son (#1026) episode sequence gaps with strict 12 consecutive episodes.
- **F1-S71:** Restored media audit quality score from 75.4% to 100.0%. Added multilingual video language parameter (`include_video_language: "en,ru,ja,null"`) to TMDb client, populated YouTube trailers and release years across 15 anime series (#1017-#1031), and resolved all critical audit issues across movies and series (61/61 healthy).
- **C5b:** Independent Audit of Kaiju No. 8 & Bot/Backend Latency (`KAIJU_VERIFY.md`). Verified database re-indexing (12 episodes) and SQL index scan (0.055ms), uncovered 7 defects (KAIJU-001..007) including 5xx swallowing and delayed callback query answering. Verdict: `SHARTLI`.
- **F1-S72:** Comprehensive Filter & Sorting System Audit & Remediation (`FILTER_AUDIT.md`, `FILTER_CONTRACT.md`, `FILTER_FIX_REPORT.md`). Audited 44 pages across website and admin-panel. Fixed 7 defects (FILTER-001..007) via strict TDD (RED -> GREEN). Added missing filters to `/search`, `/category/[id]`, `/p/[slug]`, and admin `/movies`, `/series`, `/users`. Verified with 16/16 passing backend oracle checks and 4 pytest suites without touching production or series repository.
