# Project State (STATE.md)

## Current goal
Post-Audit bug remediation across MediaPlus / Kinochi ecosystem. Systematically fix all 10 verified defects (BUG-001 through BUG-010) from AUDIT_REPORT.md under strict TDD and single-commit discipline.

## In progress (slice, branch)
- Slice: Audit Defect Fixes Complete (BUG-001 through BUG-010). Preparing for Phase 3 Independent Verification.
- Branch: `main`

## Blocked
- None.

## Next step (one task)
- Hand off to independent QA / Security Auditor for Phase 3 verification.

## Open questions for the user
- None. All 10 defects have been resolved and verified with automated test suites.

## Last verification & check results (Terminal Evidence)
- **Backend Test Suite (pytest):** 529 passed, 0 failed, 10 skipped in 89.25s (`cd backend; pytest tests/ -q`). Total coverage: 53% (9898 statements, 4670 miss).
- **Bot Test Suite (pytest):** 92 passed, 0 failed in 10.08s (`cd bot; pytest tests/ -q`).
- **Admin Panel (tsc):** `cd admin-panel; npx tsc --noEmit` passed with 0 errors.
- **Website Portal (tsc & playwright):** `cd website; npx tsc --noEmit` passed with 0 errors; `npx playwright test tests/continue_watching_sync.spec.ts` 2 passed in 1.7s; 0 Cinematic Red violations.
- **Database Migrations:** Clean DB migration upgrade/downgrade fully verified (`c011ec7100` collections dependency fixed). Alembic head is `b2c3d4e5f6a7 (head)`.

## Live Database Metrics (PostgreSQL Evidence)
- **Movies (Kinolar):** 24 ta
- **Series (Seriallar):** 20 ta
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

### Faza F1: Feature Slices & Autopilot Hardening (F1-S01 to F1-S68)
- **F1-S01:** Resolved swallowed exceptions in `movies.py`, `series.py`, and `telegram_client.py` (F-013), verified `test_fix_f013_swallowed_exceptions.py` GREEN (`339 passed`).
- **F1-S02:** Removed deceptive `"8.5"` rating mock fallback from `website/app/page.tsx` and added `#CODE` / `SERIAL` badges across home page and catalog cards with TDD verification (`test_website_mediaplus_ui.py`, `341 passed`).
- **F1-S03:** Cleaned up Navbar navigation drawer, eliminated 21 dead/bloated links and accordion dropdowns, replaced with 8 streamlined primary routes with TDD regression test (`test_navbar_clean.py`, `342 passed`).
- **F1-S04:** Removed bulky `RandomRecommendationWidget` from home page (`website/app/page.tsx`), freeing up primary viewport space.
- **F1-S05:** Implemented "Ko'rishni davom ettirish" (Continue Watching) component with authenticated API history and guest localStorage persistence with reactive synchronization (`test_continue_watching_section.py`, 3 passed).
- **F1-S06:** Redesigned `MovieCard.tsx` following iTV/Kinopoisk split-card layout (rounded-2xl poster, clean title & Obuna below, hover drawer with Year, Country, Genre, IMDb, K, /TV ratings) (`test_movie_card_itv_redesign.py`, 1 passed).
- **F1-S07:** Built iTV-style 3-row continuous infinite marquee showcase (`MediaMarqueeSection.tsx`) with calm 3x slower speed, compact referenced square/wide dimensions, and clean "Kinolar va seriallar" title (`test_media_marquee_section.py`, 2 passed).
- **F1-S08:** Applied glassmorphic transparency to Navbar (`Navbar.tsx`) and removed `#CODE` and `SERIAL` badges across all movie/series cards for clean cinema aesthetic (`test_navbar_transparency_and_clean_cards.py`, 2 passed).
- **F1-S09:** Optimized mobile layout by shortening "Eng so'nggi premyeralar va yangiliklar" to clean single-line "Premyeralar va yangiliklar" and scaled up 3-row marquee cards on mobile to touch-friendly `w-28` dimensions (`test_mobile_ux_optimizations.py`, 2 passed).
- **F1-S10:** Created dedicated `/premieres` page (`app/premieres/page.tsx`), updated BottomNav/Navbar "Premyera" routes, and switched mobile catalog grid to 3 columns (`grid-cols-3 gap-2.5`) (`test_premieres_page_and_mobile_3_col_grid.py`, 3 passed).
- **F1-S11:** Unified home page cards with new `MovieCard` (removed 125 legacy lines) and constrained marquee to container bounds (`max-w-container-max mx-auto px-gutter`) (`test_home_cards_and_marquee_boundaries.py`, 2 passed).
- **F1-S12:** Built dedicated VIP subscriptions page (`website/app/subscriptions/page.tsx`), routed BottomNav/Navbar to `/subscriptions`, and fixed desktop sidebar pin persistence across F5 page reloads (`test_subscriptions_page_and_sidebar_pin.py`, 3 passed).
- **F1-S13:** Implemented iTV horizontal filter bar (`website/components/catalog/UnifiedFilterBar.tsx`) (`test_itv_filter_bar.py`, 1 passed).
- **F1-S14:** Cleaned all mock parameters and fields (removed mock Obuna, mock 6+ age badge, mock /TV rating, hardcoded country; removed non-existent filter fields: subtitr, audiotrek, mamlakat, bepul pills); fixed z-index navbar scroll overlap; fixed 404 error on continue watching cards; inscribed Parameter Law in `facts.md` and `AGENTS.md` (`test_fix_filter_mocks_and_continue_watching.py`, 5 passed).
- **F1-S15:** Added "Suratga olish guruhi" (Cast & Crew via TMDb API with Redis caching); fixed Continue Watching 404 via episode code/ID resolution; redesigned Continue Watching to unified MovieCard (removed play icon & bottom progress bar); made hero premiere poster responsive and compact on mobile; launched Admin Panel on port 3001 (`test_cast_crew_tmdb.py`, `test_continue_watching_v2_and_hero_mobile.py`, 33 passed).
- **F1-S16:** Resolved `/series/0` 404 in Continue Watching: added custom `href` prop support and `targetSeriesId` zero-guard to `MovieCard.tsx`; filtered out zero IDs and injected resolved `targetHref` in `ContinueWatchingSection.tsx` (`test_fix_continue_watching_zero_id.py`, 35 passed).
- **F1-S17:** Unified card template across all 3 sections (Continue Watching, Home page rows, Catalog grids): standardized on a single clean `IMDb` rating badge in `MovieCard.tsx`; added auto-enrichment in `ContinueWatchingSection.tsx` so legacy items instantly acquire year, genre, and rating; updated `TelegramWatchButton.tsx` and detail pages to persist full metadata (`test_unified_card_template.py`, 38 passed).
- **F1-S18:** Modernized serial seasons and episodes UX (`SeasonEpisodesSection.tsx`): removed giant mobile season poster, added interactive season switcher tabs, compact ergonomic episode cards in responsive grid (`grid-cols-2 xs:grid-cols-3 md:grid-cols-5 lg:grid-cols-6`) (`test_season_episodes_section.py`, 40 passed).
- **F1-S19:** Upgraded Cast & Crew with desktop slider navigation buttons and mouse drag-to-scroll; built TMDb bridge returning creators, key crew (Rejissyor, Muallif, Produser, Operator, Bastakor), actors, and production details (Asl nomi, Mamlakat, Studiya, Premyera, Davomiyligi, Holati); unified both into a single container div (`test_cast_crew_slider_and_tmdb_bridge.py`, 43 passed).
- **F1-S20:** Refactored `/subscriptions` from mock VIP paywall to real user watchlist/favorites: queries `GET /users/me/subscriptions`, renders user's subscribed series and collections with live episode tracking and unsubscribe actions (`test_subscriptions_favorites_page.py`, 45 passed).
- **F1-S21:** Built full TMDb actor filmography bridge with database cross-referencing: added `GET /api/v1/actors` and `GET /api/v1/actors/{id}/movies`; displays actor photos, filmography, local movie availability badge ("Bazada mavjud" with direct watch button vs "Bazada yo'q" with instant film request submission) (`test_actors_filmography_bridge.py`, 47 passed).
- **F1-S22:** Categorized collections into 3 distinct tabs (Mavzular, Franshizalar, Xronologiyalar) in `CollectionsClientView.tsx` and `catalogThemes.ts` with TMDb-based chronological timelines (`test_collections_categories_split.py`, 49 passed).
- **F1-S23:** Resolved Continue Watching card template discrepancy (Chernobil card missing year/rating/genre): made `/api/v1/series/{series_id_or_code}` accept either integer ID, code, or episode code; updated `/me/history` to return `release_year`, `imdb_rating`, and `genres`; upgraded `ContinueWatchingSection.tsx` with multi-strategy auto-enrichment and localStorage synchronization so legacy items automatically acquire `2019 • Drama` and `IMDb 8.7` (`test_series_flexible_identifier.py`, `test_unified_card_template.py`, 44 passed).
- **F1-S24:** Synchronized PostgreSQL database migrations to head `f1322da82a96` (`d012ec7201`, `e013ec7302`), fixing missing `broadcasts.media_type` column and creating `content_requests` table; verified `GET /api/v1/broadcasts/public` HTTP 200 OK (52 passed).
- **F1-S25:** Enforced Cinematic Red Design Standard (`#E50914` / Primary Red) across entire ecosystem. Inscribed strict color anti-pattern law in `design.md`, `AGENTS.md`, and `facts.md` (forbidding yellow/gold on CTA buttons, active season/episode tabs, card hover, card titles, borders, and play icons — restricting rating-gold strictly to IMDb/Kinopoisk ratings). Corrected yellow/amber misuses across all UI components.
- **F1-S26:** Fixed sidebar accessibility & client hydration crash: added explicit hamburger button (`menu`) to `Navbar.tsx`, enabled full responsive drawer support across all screen sizes (removed `hidden xl:flex`), purged corrupted `.next` webpack cache (`MODULE_NOT_FOUND ./682.js`), and implemented Server-Side Rendering (SSR) pre-fetching for `CastCrewSection` on series and movie details pages for instant zero-skeleton display (`test_fix_sidebar_and_hydration_bugs.py`, 55 passed).
- **F1-S27:** Resolved missing actor photos and expanded actors catalog: upgraded `POPULAR_ACTORS_CATALOG` to 42 verified cinema icons with 100% valid TMDb photo URLs, added dynamic `search/person` fallback to TMDb API, debounced client search, and added `ActorCard` graceful error handling preventing browser broken `alt` text display (`test_actors_filmography_bridge.py`, 56 passed).
- **F1-S28:** Connected 1-Click Filmography modal to Cast & Crew section: created reusable `ActorFilmographyModal.tsx`, converted avatars into interactive buttons with drag-gesture filtering, updated `get_person_filmography` in `tmdb_client.py` to retrieve both cast roles and directing/producing crew credits, allowing instant filmography modal access directly from movie and series detail pages with watch and request actions (`test_cast_crew_slider_and_tmdb_bridge.py`, 57 passed).
- **F1-S29:** Implemented Netflix-style Ambient Hero Trailer Backdrop (`HeroTrailerBackdrop.tsx`): placed YouTube/MP4 trailer directly in the background of movie and series hero banners with protective dark vignette gradient overlays, instant LCP poster fallback, and a floating interactive sound toggle button; removed the bulky standalone "Treyler" section (and eliminated the non-compliant rating-gold header bar); added an ergonomic "TREYLER" modal trigger in the primary hero actions row (`test_hero_trailer_backdrop.py`, 22 passed).
- **F1-S30:** Optimized Mobile Actor Cards layout (`website/app/actors/page.tsx`): converted mobile grid to touch-friendly 3 columns (`grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2.5 sm:gap-4 md:gap-5`), downscaled avatar circle to `w-16 h-16` on mobile, padded with `p-2.5`, removed bulky bottom bar, reducing card height from ~280px to ~140px for 2x information density on phones (`test_actors_filmography_bridge.py`, 22 passed).
- **F1-S31:** Resolved MovieRow card left-edge gluing bug: moved `px-gutter` from inner horizontal flex container to parent `<section className="max-w-container-max mx-auto px-gutter ...">` in `MovieRow` (`website/app/page.tsx`) and `RecommendationsSection.tsx`.
- **F1-S32:** Fixed Telegram deep linking for numeric episode codes and standardized bot username fallbacks across website. Resolved bot "Hech narsa topilmadi" failure when accessing episode codes generated by shortuuid (such as Taxtlar o'yini 1-qismi `28831337`) in `bot/utils/code_resolver.py` by enabling code lookups for numeric strings while preserving ambiguous raw ID protection; updated `SeasonEpisodesSection.tsx` to generate explicit `ep_${episodeCode}` deep links; standardized bot username fallbacks across website to `kinochi_mvp_bot`.
- **F1-S33:** Implemented Mobile Expanding Search with Animated Logo Transition (`Navbar.tsx`, `LiveSearch.tsx`): added responsive mobile search trigger button (`sm:hidden`); on tap, Logo and header actions smoothly slide & fade out, expanding a full-width search layer in place with back button, auto-focusing input, full-width fixed dropdown popover, and tap-outside backdrop dismiss.
- **F1-S34:** Redesigned Catalog into clean 6-Category Hub (`website/app/catalog/page.tsx`): purged cluttered Asilmedia 3-poster deck and duplicate collections from catalog; built prominent 6 Category Cards hub in a responsive grid with themed gradient glows and direct subpage routing.
- **F1-S35:** Implemented Smart Idle Inactivity Transition & Cinema Mode in `HeroTrailerBackdrop.tsx`: 4.5s idle timer auto-fades foreground metadata and dark gradients, bringing the trailer into unblurred, full-clarity cinema mode with title and sound controls; any mouse move, touch, or keypress instantly wakes up and restores all movie details and CTA buttons.
- **F1-S36:** Re-engineered `HeroTrailerBackdrop.tsx` according to user's exact specification: purged all floating buttons; upon page enter, movie metadata is 100% visible; after 3.5 seconds, metadata dims to semi-transparent (`opacity-25`), softening gradients and bringing the trailer into unhindered primary focus; connected window scroll listener to immediately restore 100% full opacity to all details whenever the user scrolls slightly.
- **F1-S37:** Implemented MovieCard Hover & Mobile Hold Trailer Preview and refined Hero Mobile Responsiveness: added debounced (450ms) desktop hover and mobile touch-hold trailer video previews directly on media cards (`MovieCard.tsx`); resolved mobile hero layer collision; anchored scroll restoration so details remain 100% visible whenever `scrollY > 20` and only dim after 3.5s when stationary at the very top.
- **F1-S38:** Created 6 Dedicated Pages for Catalog Hub (Top 100, Kinolar, Seriallar, Doramalar, Anime, Multfilmlar): replaced "Barchasi" with "Top 100" (`/top100`), created dedicated pages `website/app/top100/page.tsx`, `website/app/doramas/page.tsx`, `website/app/anime/page.tsx`, and `website/app/cartoons/page.tsx`, and updated `website/app/catalog/page.tsx` to link each of the 6 cards directly to their dedicated pages with unified filter bars.
- **F1-S39:** Cropped YouTube channel/title UI and eliminated Hero top black gap: over-scanned iframe inside `MovieCard.tsx` (`w-[300%] h-[140%]`) to push YouTube channel badge and video titles beyond the card clip boundaries; anchored `HeroTrailerBackdrop.tsx` with `-top-24 sm:-top-32` behind the fixed navbar and scaled iframe, gluing the background video seamlessly to the top edge on mobile and desktop without black gaps.
- **F1-S40:** Reordered Catalog Filter Bar and Conditional Categories Concealment (`website/app/catalog/page.tsx`): placed `UnifiedFilterBar` directly beneath search header bar and above 6 category cards; wrapped 6 category cards with `!hasFilterActive` so whenever a filter is active, the 6 category cards automatically hide and filtered movie/series elements rise immediately to the filter bar.
- **F1-S41:** Mobile Hold Trailer Preview without Continuous Hold & Hero Scroll-Top Dim Cycle: 1s touch-and-hold triggers trailer preview filling the 2:3 card; on release, video continues playing without requiring continuous finger hold; release click is intercepted to prevent accidental page jump; tapping again navigates; window scroll stops preview. Unified `TOP_SCROLL_THRESHOLD = 50`.
- **F1-S42:** Elimination of YouTube Initial Controls Flash & True Full-Bleed Video Fill: added poster buffer delay so YouTube's initial white `|< || >|` controls splash occurs completely hidden behind the original poster; video smoothly fades in only when already streaming frames. Enlarged YouTube container to full bleed.
- **F1-S43:** Full Isolation of YouTube Touch/Click Events & 2.4s Clean Video Transition: extended buffer threshold to 2.4s in `MovieCard.tsx` and `HeroTrailerBackdrop.tsx` so initial splash finishes before fade-in; injected global physical shield layer at `z-30` (`rgba(0,0,0,0.001)`).
- **F1-S44:** Permanent Removal of Playlist Arrows & Desktop Resolution Iframe Trick: removed `&playlist=${youtubeId}` which forced playlist overlay arrows; set fixed desktop iframe dimensions with CSS transforms, disabling YouTube mobile touch overlay and eliminating pause icon and arrows.
- **F1-S45:** Merged `v2-f1-catalog-and-ux` into `main` (fast-forward), fixed `Episode.display_code` (`248e6b3`), verified live Render deployment (`kinochi-project-alpha-9g6j.onrender.com`), and normalized `API_URL` across website and admin client components.
- **F1-S47:** Cleaned mock FHD/HD badges and refined title legibility in `MediaMarqueeSection.tsx`: removed mock quality badge; toned down title font weight from `font-bold` to clean `font-medium`; added `backdrop-blur-md` with soft gradient behind title text matching cinema card glassmorphic standards.
- **F1-S48:** Resolved Admin Panel "Serverga ulanib bo'lmadi" connection and CORS rejection: configured backend `CORS_ORIGIN_REGEX` for Vercel deployment domains; added `resolveApiUrl()` in `admin-panel/lib/api.ts` with auto-routing to active Render backend; connected `LoginPage.tsx` to centralized `API_URL` and `HEALTH_URL`; extended health check Neon ping timeout to 5.0s.
- **F1-S49:** Eliminated asyncpg connection leaks, cross-thread event loop mismatch, and status machine race conditions across TMDb Top Seed Ingestor, site search, and Telethon download pipeline.
- **F1-S50:** Autopilot 5-Item Ingestion & Pipeline Hardening: downloaded and published 5 items to live database and website via end-to-end autopilot (Flash, Bola mol tulki va ot, Bleach, Death Note, Ob-havo farzandi); identified and permanently fixed 6 critical pipeline bugs.
- **F1-S51:** Asilmedia Anime Collection & Search Ingestion: expanded Asilmedia parser to scrape both dedicated anime collections and DLE search; collected 35 anime titles; enqueued 34 items into `ingest_items`.
- **F1-S52:** Franchise Brand Name Protection & Canonical TMDb Deduplication: updated series title in DB from literal translation to canonical "Bleach"; added canonical mappings in `ANIME_TITLE_MAP`; injected rule #7 into `gemini_identify_movie`; added post-enrichment TMDb deduplication check in `run_anitoob_anime` and `run_scraper.py`.
- **F1-S53:** Dual-Source Autopilot Execution & Pipeline Resilience: added `--source both` support; fixed Uzmovi anime parser `default_media_type="anime"`; extended `is_multi_part` detection; fixed status transition state-machine crash.
- **F1-S54:** Elimination of Duplicate "Seriallar" Row and Unified Series Display: removed `page_ids.append(13)` in `telethon_moderator_pipeline.py`; deleted redundant Page 13 from DB; added frontend duplicate filtering in `website/app/page.tsx`.
- **F1-S55:** Admin Panel Scraper Queue Async Endpoint & Event Loop Collision Fix: converted `get_queue` and all QueueManager-calling routes in `backend/app/api/v1/scraper.py` into native `async def` endpoints; added `get_status_async` in `ProcessManager`; fixed admin panel queue empty explorer bug.
- **F1-S56:** Queue State Machine Race Condition & Cross-Loop Recovery Hardening: prevented illegal `needs_review -> failed` transition in `run_scraper.py`; hardened `recover_stale_in_progress_async` with `NullPool` kwargs in `QueueManager`; enforced `UZMOVI_BOT_CODE_VERIFIED=False` protection.
- **F1-S57:** TMDb multi-type search and numeric ID lookup fix: concurrent `tv` and `movie` queries when numeric ID is supplied; cross-fallback for textual search; expanded FastAPI endpoint parameters to accept all media types (`anime`, `dorama`, `multfilm`, `series`, `movie`).
- **F1-S58:** Home page slider deduplication fix: implemented `seenRecentKeys` deduplication filter in `website/app/page.tsx` ensuring each movie/series is rendered exactly once even if attached to multiple categories.
- **F1-S59:** Strict Anime vs Cartoon (Multfilm) isolation: prevented TMDb generic genre 16 ("Animation") from automatically binding Anime to Page 8 (Multfilm); cleaned DB associations.
- **F1-S60:** Autopilot End-to-End Enrichment Isolation: prevented Category 22 ("Animatsiya") from attaching to Anime content; ensured suggested categories strictly include "Anime" and exclude "Multfilm".
- **F1-S61:** Anime Title Integrity, Subtitle Hyphen Splitting, and Live-Action Isolation: fixed regex hyphen splitter; added canonical mappings for `Aka-uka Grimm ertaklari` and `Kiki: Eltuv xizmati`; isolated live-action movies from Anime subpage.
- **F1-S62:** Search Punctuation and Space Tolerance (Fuzzy Hyphen Normalization): tokenized search queries with `re.split(r"[\s\-_:]+", clean_query)` and `word_wildcard` across movies, series, and collections in backend API and repositories, fixing zero-results on queries like `aka uka`.
- **F1-S63:** Scraper Flood Wait Freeze Guard and Timeout Hardening: introduced `MAX_BOT_FLOOD_WAIT = 120`s threshold, `BotFloodWaitError`, and immediate abort when donor bot returns long wait times (41 mins, etc.), preventing 80-minute frozen scraper hangs.
- **F1-S64:** Series Episode Loop FloodWait Swallowing Guard: added `except BotFloodWaitError: raise` in `run_single_series` at season switch and episode loops, preventing 48 useless consecutive requests to throttled bots.
- **F1-S65:** Cross-Loop asyncpg Connection Containment & QueueManager Hardening: isolated thread sessions with dedicated `NullPool` factory when not running on the main thread; replaced sync wrappers in async routines with native `await` calls; fixed `RuntimeError: Future attached to a different loop`.
- **F1-S66:** Checkpoint Isolation by Media Type & Scraper Category Limits: isolated page checkpoints per `(source, media_type)` (e.g. `asilmedia_anime_current_page`) in `state_manager.py`; added category page limits (`SOURCE_MEDIA_TOTAL_PAGES`); updated Asilmedia anime URL to genre archive.
- **F1-S67:** MediaPlus Missing & Tangled CRUD Consolidation and Telegram Bot Synchronization:
  - Connected `publish_status: Depends(resolve_publish_status)` in `series.py` seasons/episodes to allow admins full access to pending series.
  - Added full atomic CRUD endpoints: movie translation update (`PUT /movies/translations/{id}`), broadcast draft edit (`PUT /broadcasts/{id}`) and deletion (`DELETE /broadcasts/{id}`), review moderation deletion (`DELETE /reviews/{id}`) and global feed (`GET /reviews/admin`), and user watch history clear endpoints (`DELETE /users/me/history/{id}`, `DELETE /users/me/history`, `DELETE /users/by-telegram/{telegram_id}/history`).
  - Created `admin-panel/app/users/page.tsx` with user search and 1-click ban/unban controls; added "Foydalanuvchilar" to admin sidebar; added broadcast delete button adhering to Cinematic Red standard.
  - Telegram Bot Synchronization: deduplicated `/katalog` buttons and organized layout into `[2, 1, 2..., 1]`; created `BanCheckMiddleware` to block banned users across all bot interactions; connected `telegram_user_id` to reports; integrated watch history clearing flow with confirmation in `bot/handlers/profile.py`.
- **F1-S68:** Loop-Bound NullPool Session Isolation, Scraper Progress Transparency & Queue Spinner Fix:
  - Bound `NullPool` engine factory directly to the active event loop instance (`setattr(loop, "_kinochi_loop_session_factory", factory)`), eliminating cross-loop future collisions in worker threads.
  - Flattened `fetchQueue` in `admin-panel/app/scraper/page.tsx` to handle page correction inline without recursive reqId race conditions; added automatic `setQueuePage(1)` reset on status tab selection, resolving the infinite "Yuklanmoqda..." spinner.
  - Updated loop logger in `scraper/run_scraper.py` to print `[{idx}/{len(pending)}]` and transparently display downloaded counts.
  - Formatted episode progress string in `scraper/telethon_moderator_pipeline.py` to `(Qism: {ep_num}/{total_eps_in_season}, yuklangan: {uploaded_count})`.
  - Terminated ghost duplicate bot process 50564, eliminating `TelegramConflictError`.

---

## Key files
- `facts.md`: Immutable source of truth (users, stack, Cinematic Red standard, parameter law).
- `STATE.md`: Real-time project trajectory, verified metrics, and completed slice history.
- `AGENTS.md`: Governance, 8-Axis filter, TDD protocol, and operational laws.
- `docs/decisions.md`: Architectural decision records (ADR-001 to ADR-009).
- `docs/failures.md`: Failure incident logs and preventative engineering rules.
- `backend/app/api/v1/series.py`: Series, season, and episode endpoints with admin publish status access.
- `backend/app/api/v1/scraper.py`: Native async scraper control and queue inspection routes.
- `scraper/queue_manager.py`: Loop-isolated NullPool and async database queue manager.
- `scraper/telethon_moderator_pipeline.py`: Telethon MTProto downloader and moderator pipeline with flood wait circuit breaker.
- `scraper/run_scraper.py`: Central scraper CLI controller and batch dispatcher.
- `admin-panel/app/scraper/page.tsx`: Real-time scraper queue monitor and manual control dashboard.
- `admin-panel/app/users/page.tsx`: User management, ban/unban, and activity inspection dashboard.
- `bot/main.py` & `bot/middlewares/ban_check.py`: Telegram thin-client bot entrypoint and security middleware.
