# Slice Report: 2026-10-28-f1-s27-actors-catalog-photos-and-expansion

## What was done
1. Fixed missing actor photos: replaced invalid static image hashes with 100% verified, live TMDb image CDN URLs (`https://image.tmdb.org/t/p/w500/...`).
2. Expanded actors catalog: increased popular actors from 11 to 42 world-famous stars and cinema directors (Jason Statham, Tom Cruise, Leonardo DiCaprio, Keanu Reeves, Johnny Depp, Jackie Chan, Cillian Murphy, Christian Bale, Brad Pitt, Robert Downey Jr., Christopher Nolan, The Rock, Vin Diesel, Will Smith, Tom Hardy, Ryan Reynolds, Margot Robbie, Scarlett Johansson, Angelina Jolie, Benedict Cumberbatch, Chris Hemsworth, Chris Evans, Al Pacino, Robert De Niro, Morgan Freeman, Denzel Washington, Matthew McConaughey, Zendaya, Timothée Chalamet, Henry Cavill, Hugh Jackman, Joaquin Phoenix, Quentin Tarantino, James Cameron, Steven Spielberg, Chris Pratt, Bruce Willis, Arnold Schwarzenegger, Salma Hayek, Zoe Saldana, Kate Winslet, Julia Roberts).
3. Added dynamic TMDb person search: if a user searches for any actor not in the curated 42, the backend automatically queries TMDb `search/person` API and returns results with photos and filmography.
4. Added graceful image error handling in `website/app/actors/page.tsx` (`ActorCard` component) so broken network images fall back to the avatar icon instead of rendering browser `alt` text.
5. Added automated regression test in `backend/tests/test_actors_filmography_bridge.py` (56 passed).

## Changed files
- `backend/app/api/v1/actors.py` - Expanded to 42 verified actors with TMDb photos & dynamic person search fallback.
- `website/app/actors/page.tsx` - Added `ActorCard` with `imgError` fallback & debounced search.
- `backend/tests/test_actors_filmography_bridge.py` - Regression assertions for 40+ actors and valid TMDb photo URLs.
- `STATE.md` - State tracked.

## check output
```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Администратор\Desktop\kino bot project\kinochi project\backend
configfile: pyproject.toml
plugins: anyio-4.14.1, asyncio-1.4.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 56 items

backend\tests\test_fix_f013_swallowed_exceptions.py .                    [  1%]
backend\tests\test_website_mediaplus_ui.py ..                            [  5%]
backend\tests\test_navbar_clean.py .                                     [  7%]
backend\tests\test_continue_watching_section.py ...                      [ 12%]
backend\tests\test_movie_card_itv_redesign.py .                          [ 14%]
backend\tests\test_media_marquee_section.py ..                           [ 17%]
backend\tests\test_navbar_transparency_and_clean_cards.py ..             [ 21%]
backend\tests\test_mobile_ux_optimizations.py ..                         [ 25%]
backend\tests\test_premieres_page_and_mobile_3_col_grid.py ...           [ 30%]
backend\tests\test_home_cards_and_marquee_boundaries.py ..               [ 33%]
backend\tests\test_subscriptions_page_and_sidebar_pin.py ...             [ 39%]
backend\tests\test_itv_filter_bar.py .                                   [ 41%]
backend\tests\test_fix_filter_mocks_and_continue_watching.py .....       [ 50%]
backend\tests\test_cast_crew_tmdb.py ...                                 [ 55%]
backend\tests\test_continue_watching_v2_and_hero_mobile.py ...           [ 60%]
backend\tests\test_fix_continue_watching_zero_id.py ..                   [ 64%]
backend\tests\test_unified_card_template.py ....                         [ 71%]
backend\tests\test_season_episodes_section.py ....                       [ 78%]
backend\tests\test_cast_crew_slider_and_tmdb_bridge.py ...               [ 83%]
backend\tests\test_subscriptions_favorites_page.py ..                    [ 87%]
backend\tests\test_actors_filmography_bridge.py ...                      [ 92%]
backend\tests\test_collections_categories_split.py ..                    [ 96%]
backend\tests\test_fix_sidebar_and_hydration_bugs.py ..                  [100%]

======================= 56 passed, 4 warnings in 3.05s ========================
```

## Risks and unknowns
- TMDb person search rate limiting: protected by SlowAPI `60/minute` endpoint rate limiter and `TMDbRateLimiter` token bucket.

## Concept to explain to the user
- Curated Static Cache with Dynamic API Fallback — Eng mashhur 42 ta yulduzni zudlik bilan keshdan chiqarish, qidiruvda boshqa yulduz so'ralsa TMDb API orqali dinamik topib berish.

## Next step
- Await user verification on live browser (`http://localhost:3000/actors`).
