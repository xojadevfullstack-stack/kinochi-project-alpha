# Failure Log (docs/failures.md)

## Failure 013: Muddy Ambient Backdrop Gradients and Conflicting Dark Stage Enforcement in Light Mode (2026-11-18)
- **Mistake:** Attempting to preserve a blurred backdrop image with dark gradients (`bg-gradient-to-t from-[#08090C] ...`) and forcing `.cinema-stage` to `#09090B` with white glowing text inside Light Mode, resulting in an ugly grey/black smudge behind movie titles, unreadable white-on-white text, and dark rectangular patches across light mode mockups.
- **Impact:** Light Mode on mobile and desktop detail pages (`mockup_media_detail.html`, `mockup_series_detail.html`) looked dirty, broken, and unreadable, frustrating the user repeatedly.
- **Fix:** Completely purged the `<div class="absolute inset-0 z-0">` ambient blur and gradient overlays from the HTML, removed the broken contrast enforcement block across all 23 mockups, and converted `.cinema-stage` in Light Mode into a 100% clean, spotless solid white (`#FFFFFF`) canvas with dark slate (`#0F172A`) typography.
- **Rule:** Never layer dark gradient overlays or blurred images onto light-mode containers; in light mode, stage backgrounds must be solid, crisp, and clean with zero gradient mud.

## Failure 012: CSS Light Mode Inverted Specificity Collision on Cinema Stage Elements (2026-11-18)
- **Mistake:** Forcing `.cinema-stage` to remain dark (`#0A0D14 !important`) in Light Mode while a global rule `body.light-theme .text-white { color: #0F172A !important; }` converted title text to dark navy, resulting in unreadable dark-on-dark text in Light Mode.
- **Impact:** Movie detail titles (e.g. "Dune: Part Two") became nearly invisible dark navy text against a black stage background.
- **Fix:** Redesigned `.cinema-stage` in Light Mode to render as an authentic clean light canvas (`#FFFFFF`) with crystal clear `#0F172A` text, and guaranteed `#FFFFFF` text inside all primary red CTA buttons.
- **Rule:** Never apply dark backgrounds to sections in light mode without scoping child text rules to `#FFFFFF` with strict priority, and prefer consistent theme semantics across all views.

## Failure 011: Autopilot Enrichment, Vision Gate False Positives & Kinochilar Series Pagination Bugs (2026-11-18)
- **Mistake:**
  1. **Donghua vs Anime Collision (`#1116`):** Chinese donghua «Ishlayotgan yovuz qirol» (*The Demon King Who Lost His Job*, `TMDb 283322`, 2025) from `@ANITOOBUZ_BOT` was misidentified as 2013 Japanese anime *The Devil is a Part-Timer!* (`TMDb 45997`).
  2. **Missing Kinochilar Site Search:** `scraper/site_search.py` lacked `_search_kinochilar()`, returning empty results in Admin Panel when searching the `kinochilar` source.
  3. **Vision Gate False Positives on Studio Intros:** Opening frames (`35s–85s`) showing studio intros, watermarks, or cast credits caused Gemini Vision to return `"Unknown"` / `"studio intro"`, which Vision Gate treated as a content mismatch (`rejected`), while unawaited `QueueManager().update_status()` calls overwrote the specific reason with generic `"Video olinmadi yoki xatolik"`.
  4. **Verbose LLM Title Translation (`#889`):** Gemini returned multi-line explanatory prose instead of a bare title for *Ode to My Father* (`Otamga qasida`), polluting `movies.title` and topic `#9595`.
  5. **Kinochilar Series Stopping After Episode 1:** `@kinochilar_fast_bot` requires clicking `"Qismlar ro'yxati"`, mutates the episode list message in-place into quality buttons without a back button after Episode 1 is clicked, uses `➡️ Keyingi` / `⬅️ Oldingi` pagination, and captions subsequent episodes with the donor's original title (`item.title`) rather than the TMDb-enriched title.
- **Fix:**
  1. Updated `series #1116`, `series_sources #1298`, and Topic `#9463` to `Ishlayotgan yovuz qirol (2025)` (`TMDb 283322`), and added the mapping to `ANIME_TITLE_MAP` in `scraper/smart_enricher.py`.
  2. Added `_search_kinochilar()` in `scraper/site_search.py` and wired it into `search_sites()`.
  3. Updated `scraper/autopilot_vision_gate.py` and `scraper/video_verifier.py` to gracefully pass `"Unknown"` / `"watermark"` / `"studio intro"` / `"credits"` frames when no conflicting title is detected, and switched status updates in `scraper/telethon_moderator_pipeline.py` to `await QueueManager().update_status_async(...)`.
  4. Added `clean_translated_title_output()` in `backend/app/infrastructure/external/translator.py` and cleaned Movie `#889` (`Otamga qasida`) and Topic `#9595`.
  5. Added `"Qismlar ro'yxati"` auto-click, `_reopen_series_episodes_card()`, `➡️ Keyingi` / `⬅️ Oldingi` pagination support, and `item.title` / `source_id` matching in `matches_series_video()` inside `scraper/telethon_moderator_pipeline.py`; re-queued 8 incomplete series with `priority = 100`.
- **Rule:** Always handle in-place Telegram message mutations in donor bots by re-fetching the start card when episode buttons disappear, strip LLM conversational preamble from title translations, and never reject videos on generic studio intro/watermark frames unless a distinct conflicting title is positively identified.

## Failure 010: Direct Ingest Status Transition from `queued` to `published` Violating State Machine
- **Mistake:** Fast ingestion routes in autopilot attempted to update item status from `queued` directly to `published` via `QueueManager().update_status()`. IngestItemModel state machine only permitted `queued -> in_progress`.
- **Impact:** Raised `ValueError: Taqiqlangan status o'tishi: 'queued' -> 'published'`, aborting database queue item status sync even though the media itself was successfully uploaded and published.
- **Fix:** Enhanced `update_status_async` in `scraper/queue_manager.py` to automatically execute intermediary `queued -> in_progress` transition before transitioning to `published`.
- **Rule:** When updating state machine entities to terminal states, always respect intermediary lifecycle stages or auto-promote through permitted paths.

## Failure 009: Unvalidated Ingest Seed TMDb IDs Causing Franchise Corruption (Kichkina Dodo)
- **Mistake:** Seed catalog `ingest_items` contained erroneous/copy-pasted `tmdb_id` entries (e.g. `82540` for Slime Code 218, which actually corresponds to German cartoon "Kleiner Dodo"), and `smart_enricher.py` gave `explicit_tmdb_id` an unconditional `100.0` score without verifying title compatibility.
- **Impact:** Pipeline created Series 1102 "Kichkina Dodo" and uploaded Slime anime episodes under the caption "Kichkina Dodo 4-Mavsum" in Telegram topic 7959.
- **Fix:** Purged Series 1102, its seasons, episodes, and Telegram topic 7959. Added an automated title validation guard in `scraper/smart_enricher.py`: if `explicit_tmdb_id` scores < 35.0 against the candidate title, it is rejected with a warning and falls back to AI search. Audited and cleaned all corrupted TMDb IDs in `ingest_items`.
- **Rule:** Never trust external or pre-seeded IDs without semantic verification against the input entity's title.


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

## Failure 007: Vercel Build Type Error & Empty Preview (API URL mismatch)
- **Mistake:** (1) `SeasonEpisodesSection.tsx` read `episode.display_code`, but the `Episode` type had no such field. Local `next lint` and the dev server do not type-check, so the error only surfaced in the Vercel `next build`. (2) The Vercel Preview showed `0 ta` content: probe results show `kinochi-project-alpha.onrender.com` returns 503, while `kinochi-project-alpha-9g6j.onrender.com` returns 200 with 18 movies and 11 series.
- **Impact:** Vercel build failed once; the Preview catalog rendered empty.
- **Fix:** Added optional `display_code?: string | null` to `Episode` (`248e6b3`). Run `tsc --noEmit -p website/tsconfig.json` before every push. The Vercel env var `NEXT_PUBLIC_API_URL` was NOT verified (HYPOTHESIS: Preview env points to the dead host).
- **Rule:** Run a type check (`tsc --noEmit`) in addition to lint before pushing frontend changes. `next build` fails with EPERM while `next dev` is running, so rely on `tsc` locally.

## Failure 008: Dynamic Page Duplicate Row & Stranded Series Card
- **Mistake:** (1) `resolve_page_ids` automatically appended `13` (`Seriallar` dynamic subpage) to incoming standard TV series. (2) `fetchApi("/series?limit=20&exclude_paged=true")` on the homepage excluded any series with attached pages, while `pagesData.map` dynamically rendered an identical `<MovieRow title="Seriallar">` for Page 13.
- **Impact:** The homepage rendered two distinct "Seriallar" rows: the main row with seeded series (Taxtlar oʻyini, Breaking Bad), and an isolated second row below containing only a single card ("Flash").
- **Fix:** Removed `page_ids.append(13)` in `telethon_moderator_pipeline.py`. Deleted Page 13 ("Seriallar") from `pages` table and unbound Flash from `page_series`. Added frontend duplicate protection in `website/app/page.tsx` filtering out `pagesData` with title or slug matching "Seriallar" or "Kinolar".
- **Rule:** Primary media entities (`movies`, `series`) must not be given dummy subpage IDs matching their main entity names. Homepage dynamic page loops must filter out canonical sections to prevent row title duplication.

## Failure 009: Premature Franchise Guessing & Multi-Card Ingestion Collision
- **Mistake:** Blindly assuming that sequential AniToob bot card codes (e.g. 227..234) represented sequential anime seasons (1..6) in `sync_anitoob_merged_queue.py` without verifying their real content in Telegram.
- **Impact:** Card 230 was marked Season 4, creating an empty gap (Season 1 had 1 episode, Seasons 2 and 3 were skipped, and Season 4 was created with 11 episodes). In reality, AniToob only possessed Season 1 across multiple re-uploaded/split cards.
- **Fix:** (1) Inspected real bot card content via Telethon, identifying that codes 227..234 are Season 1 copies. (2) Removed fake season mappings, marked redundant duplicates as `already_exists`, and mapped working Code 230 to Season 1. (3) Updated `telethon_moderator_pipeline.py` to dynamically adjust `total_ep_count = max(total_ep_count, max(ep_video_map.keys()))`. (4) Cleaned up Series 1100 corrupted seasons/episodes and re-ingested clean Season 1.
- **Rule:** Never invent or assume season numbers in franchise mappings without verifying actual episode counts and bot card payloads. Duplicate and broken cards must be marked `already_exists` or `failed`.

## Failure 009: Telethon Topic Deletion Parameter & Multi-Season Bundling Flaw
- **Mistake:** (1) In `_delete_topic_safe`, `DeleteTopicHistoryRequest` was imported from `telethon.tl.functions.channels` instead of `messages`, and passed `channel=peer` instead of `peer=peer`, causing silent failures on every forum topic deletion attempt. (2) AniToob and Animeelar pipelines hardcoded `season_number=1`, ignoring season tags in titles (e.g. "Naruto 2-fasl") and dumping multi-season episodes into Season 1 or creating duplicate series cards. (3) `smart_enricher` did not enforce strict animation genre (16) for anime, allowing non-animated archive broadcasts (Obs 86 Show) and fan edits (Naruto The Ocean Cut) to match.
- **Impact:** Failed downloads left orphaned Telegram forum topics with "Qismlar yuklanmoqda...", Series cards had wrong posters and titles, and multi-season anime episodes were crammed into Season 1.
- **Fix:** Corrected `DeleteTopicHistoryRequest(peer=peer, top_msg_id=topic_id)` in `telethon_moderator_pipeline.py`. Added dynamic season extraction (`extract_season_number_from_text`) and season creation. Added strict animation genre requirement and banned fan-edits in `smart_enricher.py`. Automated orphan topic cleanup on 0 downloaded episodes.
- **Rule:** Always verify Telethon TL request signatures with `inspect.signature` before deployment. Never hardcode season numbers in media pipelines.


## Failure 009: Scraper Queue Endpoint Threadpool Loop Detachment
- **Mistake:** The admin route `/api/v1/scraper/queue` was defined as a synchronous `def` function. FastAPI dispatched it into a worker thread where `_run_coro_sync` spawned a new event loop. When the coroutine queried the database, SQLAlchemy's `asyncpg` connection pool (bound to the main loop) threw `got Future attached to a different loop`. An exception handler swallowed the error and returned `{ "items": [], "total": 0 }`.
- **Impact:** The Admin Panel top stats cards and tabs correctly displayed 99 queue items, but the table explorer below remained empty with "Hech qanday element topilmadi (0 ta)".
- **Fix:** Converted `get_queue`, `get_status`, and all QueueManager-calling routes in `backend/app/api/v1/scraper.py` into native `async def` endpoints awaiting `get_filtered_async` and `stats_async`. Implemented `get_status_async` in `ProcessManager`. Updated admin panel badges to recognize both `pending`/`queued` and `completed`/`published`. Added regression test `backend/tests/test_scraper_queue_endpoint.py`.
- **Rule:** Any FastAPI route accessing async resources or connection pools must be declared as `async def` to execute on the main asyncio event loop without cross-thread detachment.

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
4. `scraper_unbounded_flood_wait_freeze` (2026-11-06):
   - **Symptom:** Scraper process stuck in Admin Panel showing `⏱️ 45:14` on "Iblislar qotili: Cheksiz poyezd" with zero CPU activity.
   - **Root Cause:** `@asilmediabot` returned a long rate-limit message ("Biroz sekinroq. 41 daqiqadan so'ng urinib ko'ring"), which was parsed into 2465 seconds. The pipeline called `await asyncio.sleep(2465)` without a maximum threshold cap, freezing each item until its 20-minute timeout fired and repeating across all queued items.
   - **Fix:** Added `MAX_BOT_FLOOD_WAIT = 120` limit and `BotFloodWaitError` via `handle_bot_flood_wait()`. Long flood delays now abort immediately without sleeping, update `StateManager`, and prevent consecutive doomed calls to the throttled bot.

## Failure 010: Series Episode Loop Swallowing BotFloodWaitError
- **Mistake:** Inside run_single_series in scraper/telethon_moderator_pipeline.py, the episode loop caught generic Exception as ep_err:. When donor bot @asilmediabot returned a 56-minute rate-limit, handle_bot_flood_wait correctly raised BotFloodWaitError, but the handler swallowed it, logged a single episode failure, slept 3.5s, and continued iterating through all remaining 48 episodes across 2 seasons.
- **Impact:** Scraper repeatedly hammered the locked donor bot 48 times, wasting time and keeping the admin panel progress stuck on [2-mavsum] 17-qism yuklanmoqda (1/24)... with Bot: FloodWait (Kutishda).
- **Fix:** Added except BotFloodWaitError: raise in scraper/telethon_moderator_pipeline.py at both the season switch (line 1305) and episode loop (line 1941). Added test_series_episode_flood_wait_raises_immediately in backend/tests/test_run_scraper_flood_wait.py.
- **Rule:** Never catch generic Exception over custom flow-control or circuit-breaker exceptions like BotFloodWaitError without explicitly re-raising them.


### 2026-11-09: Cross-Loop asyncpg Connection Checkout in Scraper & QueueManager
- **What happened:** In `scraper/process_manager.py` and `scraper/run_scraper.py`, synchronous wrapper methods (`qm.stats()`, `qm.get_pending()`) were called from inside active asyncio event loops or background worker threads. This spun up worker threads calling `_run_coro_sync` which attempted to check out pooled `asyncpg` connections initialized on the main FastAPI event loop, throwing `RuntimeError: Future attached to a different loop`.
- **Root cause:** FastAPI event loop pooled async connections cannot be shared across different threads/loops; furthermore, calling sync wrappers from inside an `async def` function is an anti-pattern.
- **Rule:** Inside `async def` routines, always directly `await` native async methods (`stats_async`, `get_pending_async`). For multi-threaded access outside the main loop, use a dedicated `NullPool` session factory.


### 2026-11-09: Global Checkpoint Contamination Across Distinct Content Categories
- **What happened:** In `state.json`, `asilmedia_current_page` was shared across all media types. After scraping general movies to page 6, switching to `anime` caused the scraper to start at page 6 and loop through pages 6, 7, 8, 9... finding 0 items on every page, because Asilmedia only has 3 pages (~29 anime) in its entire database.
- **Root cause:** Checkpoint offsets and total page limits were global per source (`asilmedia_current_page: 6`, `asilmedia_total_pages: 400`) instead of being isolated per `(source, media_type)`.
- **Rule:** Scraper checkpoint states and total page limits must be scoped per `(source, media_type)`. If a category finishes or has fewer pages, it must start at page 1 for that category and stop when the category ends.


### 2026-11-09: Class-Level NullPool Engine Caching Across Ephemeral Event Loops
- **What happened:** In `scraper/queue_manager.py`, `_nullpool_session_factory` was cached as a static class attribute (`cls._nullpool_session_factory`). When multiple sync calls executed `_run_coro_sync` across ephemeral worker threads, subsequent calls reused the engine created on a previously closed event loop, triggering `Future attached to a different loop`. Simultaneously in `admin-panel/app/scraper/page.tsx`, a recursive call in `fetchQueue` caused `reqId !== queueReqId.current` race condition that kept `loadingQueue = true`, freezing the queue UI in an infinite "Yuklanmoqda..." spinner.
- **Root cause:** Even with `NullPool`, an SQLAlchemy `AsyncEngine` binds to the active event loop when initialized. Reusing the engine across closed/new loops breaks asyncpg's protocol. Additionally, recursive UI fetch calls desynchronize request token counters.
- **Fix:** Bound the `NullPool` factory per unique event loop instance (`setattr(loop, "_kinochi_loop_session_factory", factory)`), flattened `fetchQueue` to handle page fallbacks synchronously without recursion, and reset `queuePage` to 1 upon clicking any status tab.
- **Rule:** Never cache async database engines across different event loop instances. Bind engines to the specific loop instance.


### 2026-11-09: Telegram Bot Catalog Button Duplication & Missing Thin-Client State Sync
- **What happened:** In Telegram Bot `/katalog`, duplicate `📁 Kino` and `📁 Serial` buttons appeared next to `🎬 Kinolar` and `📺 Seriallar`, causing distorted grid alignment. Additionally, banned users could still use the bot despite being banned in the Admin Panel (`is_banned` ignored), issue reports lacked `telegram_user_id`, and users had no way to clear watch history from the bot.
- **Root cause:** Dynamic page keyboards blindly iterated through the `pages` table without filtering canonical entities (`movie`, `series`), and thin-client bot handlers lacked synchronization middlewares with newly created backend CRUD operations.
- **Fix:** (1) Deduplicated `movie`, `series`, `film` pages in `bot/keyboards/inline.py` and strictly aligned rows via `builder.adjust([2, 1, 2..., 1])`. (2) Created `BanCheckMiddleware` (with 60s TTL cache) to halt banned users on all messages and callbacks. (3) Added `telegram_user_id` pass-through to `/reports`. (4) Built `DELETE /users/by-telegram/{telegram_id}/history` and integrated a confirmation dialog in `bot/handlers/profile.py`.
- **Rule:** Always filter canonical system sections from dynamic page loops, and ensure every admin management state (e.g. `is_banned`, report attribution, history reset) is enforced via global middleware in the bot client.


### 2026-11-10: Bot Latency Fallback Misleading Error & Column Index Disabling
- **What happened:** In `bot/services/api_client.py`, the HTTP timeout was 10.0s, and all exceptions (`httpx.TimeoutException`, network error) were swallowed with `return None`. Handlers interpreted `None` as "resource does not exist", displaying `"⚠️ Bu serial topilmadi"` or `"⚠️ Bu qism topilmadi"` when Neon DB took 11+ seconds on cold start. Simultaneously, `func.lower(EpisodeModel.code)` in SQL prevented using the B-Tree index on `code`, triggering full table scans and loading entire series entity trees just to compute prev/next episode codes.
- **Root cause:** Conflating network timeouts with HTTP 404 (Not Found), short 10s client timeout on serverless DB cold queries, wrapping indexed columns in SQL functions, and eager-loading entire series trees for single-episode lookups.
- **Fix:** Increased timeout to 25.0s, introduced `APIConnectionError` for timeout/network failures with an explicit retry notice ("⏳ Serverga ulanishda vaqtinchalik kechikish yuz berdi. Iltimos, qayta urinib ko'ring."), stripped heavy eager loads in `SeriesRepository`, preserved exact indexed lookup on `code`, and added 60s TTL caching in FastAPI.
- **Rule:** Never map transient network or timeout errors to `None`/404. Keep database lookups indexed directly without expression wrappers on unique columns.

### 2026-11-10: Media Type Misclassification, Dorama Category Drift & Asymmetric Catalog Queries
- **What happened:** Newly scraped doramas appeared on the homepage but rendered completely empty inside the catalog (/doramas and /catalog?type=dorama). Concurrently, 20 anime series polluted the Cartoons (/cartoons) catalog, and catalog type searches for anime/cartoons ignored all TV series.
- **Root cause:**
  1. Typo in smart_enricher.py assigned Category 3 (Drama) instead of Category 40 (Doramalar).
  2. Fragile single-index coupling: frontend queried only category_id=40 while scraper pipeline attached page_id=5.
  3. External API genre bleed: TMDb genre 16 ('Animation') automatically attached Category 22 (Animatsiya) to anime series.
  4. Scraper pipeline attached phantom Page IDs (9, 10, 11, 12) that did not exist in the PostgreSQL pages table.
  5. Asymmetric frontend queries: /catalog?type=anime and /catalog?type=cartoon only queried /movies, hiding all TV series.
- **Fix:**
  1. Corrected smart_enricher.py to map doramas strictly to Category 40, Turkish series/movies to 39/38, Indian movies to 37, and Tarjima to 36.
  2. Implemented strict mutual de-contamination: stripped Category 22 from anime and Category 2 from cartoons in scraper and backfilled 26 affected database records.
  3. Implemented Dual-Index Fault Tolerance in series_repository.py and movie_repo.py uniting Categories (40, 2, 22) with Pages (5, 1, 8).
  4. Updated catalog/page.tsx, doramas/page.tsx, movies/page.tsx, and series/page.tsx to fetch balanced mixes of series and movies.
  5. Added comprehensive regression test suite in ackend/tests/test_dorama_catalog_distribution.py (4 tests).
- **Rule:** Never rely on a single categorization vector; always enforce dual-index resilience between Categories and Pages in repositories. Isolate anime from cartoons by explicitly stripping cross-genres. Always query both series and movie endpoints when rendering polymorphic catalog media types.

### 2026-11-14: Blind Trust in Seeded Ingest TMDb IDs Causing Cartoon Hallucination ("Kichkina Dodo")
- **What happened:** Ingestion of Code 218 (`Shilliq sifatida qayta tug'ilganim haqida (4-mavsum)`) erroneously created Series 1102 titled `"Kichkina Dodo (2026)"` and posted anime episodes into a newly created Telegram topic titled `"📺 Kichkina Dodo (2026)"`.
- **Root cause:** 
  1. Historical seed typo in `ingest_items` table: row 1223 had `tmdb_id = 82540` (TMDb ID for the European animation "Kleiner Dodo" / "Kichkina Dodo") instead of `82684` ("That Time I Got Reincarnated as a Slime"). Similar dummy IDs existed for Cyberpunk and Tomodachi Game.
  2. `smart_enricher.py` blindly trusted `explicit_tmdb_id` with `best_score = 100.0` without cross-validating the candidate title against the input title.
- **Fix:**
  1. Immediately killed the ingestion task, deleted Telegram topic 7959 via Telegram Bot API, purged Series 1102, its seasons, and episodes from PostgreSQL.
  2. Updated `smart_enricher.py` to strictly score `explicit_tmdb_id` against the input title: if score < 35.0, it rejects the explicit ID, logs a warning, and falls back to AI search.
  3. Added Slime directly into `ANIME_TITLE_MAP` with TMDb ID `82684`.
  4. Swept `ingest_items` in PostgreSQL and corrected all corrupted placeholder `tmdb_id`s (82540, 209867).
- **Rule:** Never grant 100.0 confidence to external or seeded TMDb IDs without title token validation. Always verify token overlap before renaming a media entity.


### 2026-11-18: Global CSS Gradient Selector Bleed into Cinema Stage Hero
- **What happened:** A global utility override `body.light-theme .from-[#08090C]` intended to soften marquee edge fades globally overrode the dark gradients inside `.cinema-stage`, turning mobile hero headers into washed-out muddy grey-white vertical split gradients and causing film titles to render in dark navy blue against dark images.
- **Root cause:** Writing un-scoped Tailwind arbitrary utility overrides (`.from-[#08090C]`) in the global light theme stylesheet without scoping them strictly to `.marquee-container`.
- **Fix:** Confined all marquee gradient overrides strictly to `.marquee-container .from-[#08090C]` and explicitly enforced deep dark cinema backgrounds (`#08090C`) and luminous white typography (`#FFFFFF`) with KaTeX/CSS specificity inside `.cinema-stage`.
- **Rule:** Never apply un-scoped color overrides to arbitrary Tailwind gradient utility classes (`.from-*`, `.to-*`); always prefix them with a parent container class.

### 2026-11-27: Shared SQLite Test Pollution & Post-Reload Mock Binding in `test_smm_worker.py`
- **What happened:** Adding `await db_session.commit()` inside `test_smm_rubric_planner.py` persisted `MovieModel(id=1)` inside `test_shared.sqlite3` across test files, breaking `test_auto_pick_catalog_movie_selects_unused_published_movie_with_storage`; additionally, importing `process_generating_job` at top of `test_smm_worker.py` bypassed `patch(...)` after an earlier test ran `importlib.reload(scraper.smm_worker)`, and calling `download_sparse_clip_source` with unverified kwargs caused silent fallback.
- **Fix:** Switched new unit tests to `await db_session.flush()` (no committed row leakage), used post-reload module imports inside worker tests, and fixed `download_sparse_clip_source(..., target_ratio=0.35, chunk_mb=..., clip_duration=90.0)` with explicit `sample_start_sec`/`sample_span_sec` bounds so sparse `0x00` holes are never probed.
- **Rule:** Never guess helper keyword signatures without reading their declaration, avoid `.commit()` in shared-SQLite unit tests unless cleaning up explicitly, and avoid binding module attributes before tests that call `importlib.reload`.
