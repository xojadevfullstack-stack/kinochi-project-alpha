# Failure Log (docs/failures.md)

## Failure 001: Asyncpg Multi-Statement Execution Failure in Migrations
- **Mistake:** Passing multiple SQL statements inside a single `op.execute()` call in Alembic migration files (`c011ec7100`, `d012ec7201`, `e013ec7302`).
- **Impact:** Asyncpg protocol strictly forbids multiple statements in a single prepared query, causing migration crashes on clean test databases.
- **Fix:** Split multi-statement SQL strings into atomic individual `op.execute()` calls.
- **Rule:** Never combine multiple SQL statements into a single `op.execute()` under asyncpg.

## Failure 002: Prepared Statement Name Collision with PgBouncer
- **Mistake:** Relying on default asyncpg connection configuration when deploying behind Neon / PgBouncer transaction pooling.
- **Impact:** Prepared statement names collided across shared connections, raising `DuplicatePreparedStatement` exceptions.
- **Fix:** Set `statement_cache_size=0` and `prepared_statement_cache_size=0` in database engine creation.
- **Rule:** Always disable client-side prepared statement caching when using external connection poolers.

## Failure 003: N+1 Relationship Overhead on Series Endpoint
- **Mistake:** Returning full ORM model trees with nested seasons and episodes on the paginated `/api/v1/series` list endpoint.
- **Impact:** Fetching 20 series triggered 40+ secondary queries, spiking database latency and memory footprint.
- **Fix:** Applied `noload(SeriesModel.seasons, SeriesModel.pages)` and introduced dedicated `SeriesSummary` DTOs.
- **Rule:** List endpoints must return lightweight summary DTOs without eager-loading child relations.

## Failure 004: Telegram Flood Wait Lockouts during Broadcasts
- **Mistake:** Firing unthrottled concurrent asyncio tasks to send notifications across Telegram channels and users.
- **Impact:** Hit Telegram rate limits (`429 Too Many Requests`), causing task timeouts and bot thread starvation.
- **Fix:** Built a throttled dispatcher with 20 msg/sec limit, backoff retry mechanism, and automated `403` inactive user cleanup.
- **Rule:** All outward Telegram notification loops must pass through the rate-limited dispatcher.

## Failure 005: Color Palette Bleed & Misuse of Rating Gold for CTA/Hover States
- **Mistake:** Spreading `rating-gold` (`#F5C518` / `#F59E0B`) and amber tokens onto active season buttons, episode card hover states, card titles (e.g., 'Kalmar O'yini'), borders, and request CTA buttons instead of enforcing Cinematic Red (`#E50914` / `primary`).
- **Impact:** Distorted visual hierarchy and violated the Netflix/iTV cinema identity by rendering bright yellow buttons, yellow titles on hover, and yellow season selectors.
- **Fix:** Inscribed strict Anti-Pattern rules into `design.md`, `AGENTS.md`, and `facts.md`. Replaced all misuses across `SeasonEpisodesSection.tsx`, `MovieCard.tsx`, `MediaMarqueeSection.tsx`, `CastCrewSection.tsx`, `LiveSearch.tsx`, `SearchClientView.tsx`, `RequestMovieModal.tsx`, `CollectionTimelineView.tsx`, `ExternalSearchSection.tsx`, and pages with Primary Red (`#E50914`). Added regression tests in `test_season_episodes_section.py` and `test_movie_card_itv_redesign.py`.
- **Rule:** Rating Gold is strictly reserved for IMDb and Kinopoisk star ratings. All CTA buttons, active state selections, hover accents, play icons, and section indicator bars must strictly use Primary Red (`#E50914`).

## Failure 006: Stale Webpack Dev Cache Causing Client Hydration Freeze & Invisible Sidebar Trigger
- **Mistake:** (1) Running Next.js development server continuously for 6+ hours across dozens of file modifications caused `.next` webpack chunk manifests to desynchronize (`MODULE_NOT_FOUND ./682.js` and `main.js` 404), breaking client-side JavaScript execution, freezing skeleton loaders, and returning a 500 blank screen on dynamic routes (`/series/1008`). (2) Removing the hamburger menu button from `Navbar.tsx` and restricting the sidebar container to `hidden xl:flex` left mobile, tablet, and mouse-click desktop users with no way to open the navigation drawer.
- **Impact:** Website appeared frozen in skeleton loading states (Continue Watching, Cast & Crew), route navigation failed, `/series/1008` yielded a blank white screen, and sidebar was inaccessible.
- **Fix:** Added an explicit hamburger menu button (`menu` / `close`) to `Navbar.tsx`, made `<aside>` responsive (`flex`) across all viewports with backdrop overlay, purged corrupted `website/.next` cache, and added server-side credits pre-fetching to `[id]/page.tsx` and `[code]/page.tsx` for instant SSR. Verified with `test_fix_sidebar_and_hydration_bugs.py`.
- **Rule:** Never rely purely on invisible hover edge triggers for critical navigation; always provide an explicit, clickable hamburger toggle. When Next.js dev server accumulates missing chunk errors, purge `.next` and restart cleanly.

## Frozen Baseline Failures (F0 -> F1 Transition)
1. `test_fix_f013_swallowed_exceptions.py::test_no_swallowed_exceptions_in_critical_modules`:
   - **Root Cause:** Regex AST scan detected 6 bare `except ...: pass` blocks in `movies.py:875`, `series.py:981`, and `telegram_client.py:317, 353, 409, 444`.
   - **Status:** RESOLVED (2026-10-28). Replaced bare passes with structured logging (`logger.warning` / `logger.debug`), test passes green.
2. `test_seed_config_s2.py::test_seed_config_defaults`:
   - **Root Cause:** Test asserts `SEED_INCLUDE_SERIES is False`, whereas `Settings` default was intentionally flipped to `True` during series decoupling.
   - **Status:** Frozen baseline from F0. To be reconciled in scraper/seed configuration task without weakening test semantics.
3. `test_seed_ingestor_full_s9.py::test_s9_build_seeds_filters_adult_and_low_votes_and_rating`:
   - **Root Cause:** Ingestion count assertion mismatch (`added == 1` vs actual `2`) due to dual-seed fixture mock data interaction.
   - **Status:** Frozen baseline from F0. To be isolated in seed scraper test suite task.
