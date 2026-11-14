# Slice Report: 2026-11-14-hero-banner-newest-first

## What was done
1. Fixed inverted default catalog ordering (`id.asc()` -> `id.desc()`) across `series_repository.py` and `movie_repo.py`, ensuring default listing endpoints return newest uploads first.
2. Enhanced homepage hero premiere discovery in `website/app/page.tsx` by ingesting direct global newest media (`/movies?limit=10` and `/series?limit=10`) so new anime, movies, and doramas immediately appear on the Hero banner.
3. Added strict TDD regression test `test_default_newest_first_sorting.py` and verified 100% green across backend (24 passed) and bot suites (15 passed), alongside successful static Next.js production build (26/26 pages).

## Changed files
- `backend/app/infrastructure/db/repositories/series_repository.py` - Changed default series ordering from `id.asc()` to `id.desc()` and added native SQL-level sorting support.
- `backend/app/infrastructure/db/repositories/movie_repo.py` - Changed default movies ordering fallback from `id.asc()` to `id.desc()`.
- `backend/app/application/series/series_service.py` - Passed `sort=sort` to repository for native SQL-level ordering.
- `website/app/page.tsx` - Ingested global latest movies and series into hero item candidate pool for real-time premiere updates.
- `backend/tests/test_default_newest_first_sorting.py` - New TDD regression test asserting default newest-first ordering.

## check output
```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Администратор\Desktop\kino bot project\kinochi project\backend
configfile: pyproject.toml
plugins: anyio-4.14.1, asyncio-1.4.0, cov-7.1.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 24 items

backend\tests\test_default_newest_first_sorting.py .                     [  4%]
backend\tests\test_code_and_source_branding_fixes.py ...                 [ 16%]
backend\tests\test_admission_gate.py ...........                         [ 62%]
backend\tests\test_pages_publish_status.py .                             [ 66%]
backend\tests\test_anime_enricher_guards.py ..                           [ 75%]
backend\tests\test_anime_matching_fixes.py ....                          [ 91%]
backend\tests\test_filter_series_sort.py .                               [ 95%]
backend\tests\test_filter_movies_sort_and_genre_slug.py .                [100%]

======================= 24 passed, 2 warnings in 6.89s ========================
```

## Risks and unknowns
- Stale CDN or client browser cache if ISR revalidation is set to 60s; Next.js ISR auto-refreshes within 60 seconds on production.

## Concept to explain to the user
- Default Ordering (Odatiy saralash): Kutubxona peshtaxtasiga yangi kelgan kitoblar eng oldingi vitrinaga qo'yilishi kerak, aks holda yangi kelgan kitoblar omborxonaning eng orqa burchagida qolib ketadi va vitrinada faqat eng eski kitoblar turaveradi.

## Next step
- Live server deployment and user review of the dynamically updated Hero banner.
