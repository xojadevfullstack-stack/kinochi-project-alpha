# Slice Report: 2026-11-25-admin-analytics-tmdb

## What was done
1. Added real view tracking schema (`movies.view_count`, `series.view_count`, `media_view_events` via Alembic `g7b8c9d0e1f2`) and core aggregation/dedup helpers (`backend/app/core/analytics.py`), hooked into Bot (`watch_history.py`), Stream (`stream.py`), and Website (`MediaViewTracker.tsx`).
2. Implemented `POST /api/v1/statistics/track-view`, `GET /api/v1/statistics/analytics`, and `GET /api/v1/statistics/tmdb-insights` (backed by `TMDbClient.get_feed()` with local catalog & request cross-referencing).
3. Built dedicated `/analytics` page (`admin-panel/app/analytics/page.tsx`) combining Real Statistika, integrated Buyurtmalar (`RequestsPanel.tsx`), and TMDb Yangiliklar & Premyeralar, linked in `Sidebar.tsx`.

## Changed files
- `backend/app/infrastructure/db/models/movie.py` - Added `view_count` column
- `backend/app/infrastructure/db/models/series.py` - Added `view_count` column
- `backend/app/infrastructure/db/models/media_view_event.py` - Added `MediaViewEventModel`
- `backend/app/infrastructure/db/models/__init__.py` - Exported `MediaViewEventModel`
- `backend/alembic/versions/g7b8c9d0e1f2_add_view_count_and_media_view_events.py` - Idempotent migration from `a1b2c3d4e5f7`
- `backend/app/core/analytics.py` - `record_media_view`, `get_analytics_overview`, daily trends, TOP 10 queries
- `backend/app/core/watch_history.py` - Hooked bot `mark_movie_started` & `mark_episode_progress` view recording
- `backend/app/api/v1/stream.py` - Hooked stream URL issuance view recording
- `backend/app/infrastructure/external/tmdb_client.py` - Added `get_feed` (`trending_week`, `trending_day`, `upcoming`, `now_playing`, `tv_on_the_air`)
- `backend/app/api/v1/statistics.py` - Added `/track-view`, `/analytics`, `/tmdb-insights`
- `backend/tests/test_analytics.py` - Added TDD unit & endpoint tests
- `website/components/media/MediaViewTracker.tsx` - Non-blocking web page view tracker
- `website/app/movie/[code]/page.tsx`, `website/app/series/[id]/page.tsx` - Mounted `MediaViewTracker`
- `admin-panel/lib/analyticsHelpers.mjs` & `admin-panel/tests/analyticsHelpers.test.mjs` - Pure chart/share/coverage helpers & tests
- `admin-panel/components/RequestsPanel.tsx` & `admin-panel/app/requests/page.tsx` - Shared Requests panel with TMDb quick-search
- `admin-panel/app/analytics/page.tsx` & `admin-panel/components/Sidebar.tsx` - Dedicated Analytics & TMDb Hub page

## check output
```text
ruff check (modified analytics files): All checks passed!
alembic heads: g7b8c9d0e1f2 (head)
pytest tests/test_analytics.py tests/test_alembic.py::test_single_head -v: 5 passed in 1.85s
pytest bot/tests/ -q: 115 passed in 7.00s
node --test admin-panel/tests/*.mjs: 10 passed, 0 failed
tsc --noEmit (admin-panel & website): Exit 0
next build (admin-panel): 23/23 routes Exit 0
next build (website): 31/31 routes Exit 0
```

## Risks and unknowns
- Production database (Supabase) still needs `alembic upgrade head` (`g7b8c9d0e1f2`) run before deploying backend code that queries `view_count` / `media_view_events`.
- Historical views before this migration are `0` until real bot/web/stream traffic accumulates.
- `test_public_routes_hide_pending_and_hidden` has a pre-existing failure (`include_adult=True` arg mismatch from prior `a1b2c3d4e5f7` slice).

## Concept to explain to the user
- **Event Sourcing + Materialized Counter (Hybrid View Tracking)** — Har bir ko'rish hodisasini vaqt va manbasi (`bot`/`web`/`stream`) bilan `media_view_events` jurnaliga yozish va bir vaqtda tezkor o'qish uchun `movies.view_count` hisoblagichini oshirish hamda Redis orqali 1 soatlik dublikat filtr (dedup) qo'llash.

## Next step
- Run `alembic upgrade head` on production DB and verify `/analytics` live with TMDb API key active.
