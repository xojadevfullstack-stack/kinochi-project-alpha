# Project State (STATE.md)

## Current goal
Tizim barqarorligini ta'minlash, Neon DB uzoq server ulanishlaridagi timeout/semafor xatolarini bartaraf etish, hamda Qora klever va Demon Slayer media qismlarini to'liq yuklashga tayyor holatga keltirish.

## In progress (slice, branch)
- Slice: C18 (Remote DB Connection Timeout Hardening & Exponential Socket Retry).
- Branch: `main`.

## Blocked
- None (Barcha testlar 100% yashil, DB ulanish timeout 45s ga oshirildi, retry qo'shildi).

## Next step (one task)
- Foydalanuvchiga natijalarni hisobot qilish va download/autopilot jarayonini boshqarishga topshirish.

## Open questions for the user
- None.

## Last verification & check results (Terminal Evidence)
- **Pytest Gate:** 17 passed in 2.54s across anime catalog, auth and queue tests.
- **QueueManager + DuplicateChecker Remote Connect Test:** `ITEM: anitoob_41 Iblislar qotili (Demon Slayer) series pending`, `DC DONE` (Exit code: 0).
- **TypeScript Gate (Admin & Website):** Zero errors (`tsc --noEmit`: code 0).
- **Live Backend Page 8 (Multfilm) Verification:** Faqat haqiqiy multfilm qaytarilmoqda (`Ajoyib raqamli sirk`), Anime to'liq izolyatsiya qilindi.
- **Series #1036 (Qora klever) Verification:**
  - `Pages`: ['Anime'] (Multfilm yorlig'i butunlay yo'qoldi)
  - `Seasons`: Season 1 tartiblandi, soxta qismlar tozalandi.
- **Series #1035 (Demon Slayer) Verification:**
  - `Title`: 'Iblislar qotili (Demon Slayer)' (eski 'temirchilar qishlogi' o'rniga)
  - `TMDb ID`: 85937 (TV Series, 2019, Reyting: 8.6)
  - `Pages`: ['Anime']
- **Ingest Queue Verification:** `anitoob_41` media_type = 'series', 58 qism bilan qayta navbatga qo'yildi.
- **Git Diff:** Atomic slice within governance budget.

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
