# Project State (STATE.md)

## Current goal
Telegram bot orqali sayt profiliga 1-click kirish autentifikatsiyasini yo'lga qo'yish va Admin panel scraper navbat jadvalidagi cheksiz "Yuklanmoqda..." yuklagich blokirovkasini to'liq bartaraf etish.

## In progress (slice, branch)
- Slice: C15 (Bot One-Click Login Token & Scraper Queue Infinite Loading Fix).
- Branch: `main`.

## Blocked
- None (Barcha testlar 100% yashil, bot login va admin panel navbat jadvali to'liq ishlaydi).

## Next step (one task)
- O'zgarishlarni commit va push qilish (`git commit -m "fix(auth,scraper): add secure bot-login endpoint and resolve queue table loader race condition"`).

## Open questions for the user
- None.

## Last verification & check results (Terminal Evidence)
- **Pytest Gate:** 11 passed in 1.46s (`test_telegram_auth.py` va `test_scraper_queue_endpoint.py`).
- **Live Backend Verification:** `api_client.generate_login_token` returned status 200 with valid JWT access_token.
- **TypeScript Gate (Admin Panel):** Zero errors (`tsc --noEmit`: code 0).
- **Git Diff:** 4 files, 132 insertions, 15 deletions (147 lines <= 200 lines atomic slice).

## Live Database Metrics (PostgreSQL Evidence)
- **Movies (Kinolar):** 31 ta (100% sog'lom)
- **Series (Seriallar):** 35 ta (100% sog'lom, 34 ta published, 1 ta Jodugarlar Jangi Page 1 ga biriktirildi)
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
