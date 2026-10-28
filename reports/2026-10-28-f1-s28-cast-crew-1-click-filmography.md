# Slice Report: 2026-10-28-f1-s28-cast-crew-1-click-filmography

## What was done
1. Implemented 1-click filmography modal directly from the "Suratga olish guruhi" (Cast & Crew) section on movie and series detail pages.
2. Created reusable client component `website/components/media/ActorFilmographyModal.tsx` that queries `GET /api/v1/actors/{person_id}/movies` and renders actor/creator filmography with green "Tomosha qilish" (available locally) and "Buyurtma berish" (content request) buttons.
3. Converted circular avatar cards in `website/components/media/CastCrewSection.tsx` into interactive buttons with hover scaling and drag-scroll distance threshold guard so dragging the horizontal slider does not accidentally trigger the modal.
4. Upgraded `get_person_filmography` in `backend/app/infrastructure/external/tmdb_client.py` to aggregate both acting cast credits and key crew credits (directors, producers, screenwriters, composers), ensuring directors like David Yates or Christopher Nolan return their full directed filmography.
5. Added automated regression test `test_cast_crew_1_click_filmography_modal_integration` in `backend/tests/test_cast_crew_slider_and_tmdb_bridge.py` (57 passed).

## Changed files
- `website/components/media/ActorFilmographyModal.tsx` - Reusable filmography modal with watch and order actions.
- `website/components/media/CastCrewSection.tsx` - Added 1-click filmography modal trigger with drag filter.
- `backend/app/infrastructure/external/tmdb_client.py` - Aggregated cast and directing crew filmography.
- `backend/tests/test_cast_crew_slider_and_tmdb_bridge.py` - Automated verification test.
- `STATE.md` - State tracked.

## check output
```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Администратор\Desktop\kino bot project\kinochi project\backend
configfile: pyproject.toml
plugins: anyio-4.14.1, asyncio-1.4.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 57 items

backend\tests\test_fix_f013_swallowed_exceptions.py .                    [  1%]
backend\tests\test_website_mediaplus_ui.py ..                            [  5%]
backend\tests\test_navbar_clean.py .                                     [  7%]
backend\tests\test_continue_watching_section.py ...                      [ 12%]
backend\tests\test_movie_card_itv_redesign.py .                          [ 14%]
backend\tests\test_media_marquee_section.py ..                           [ 17%]
backend\tests\test_navbar_transparency_and_clean_cards.py ..             [ 21%]
backend\tests\test_mobile_ux_optimizations.py ..                         [ 24%]
backend\tests\test_premieres_page_and_mobile_3_col_grid.py ...           [ 29%]
backend\tests\test_home_cards_and_marquee_boundaries.py ..               [ 33%]
backend\tests\test_subscriptions_page_and_sidebar_pin.py ...             [ 38%]
backend\tests\test_itv_filter_bar.py .                                   [ 40%]
backend\tests\test_fix_filter_mocks_and_continue_watching.py .....       [ 49%]
backend\tests\test_cast_crew_tmdb.py ...                                 [ 54%]
backend\tests\test_continue_watching_v2_and_hero_mobile.py ...           [ 59%]
backend\tests\test_fix_continue_watching_zero_id.py ..                   [ 63%]
backend\tests\test_unified_card_template.py ....                         [ 70%]
backend\tests\test_season_episodes_section.py ....                       [ 77%]
backend\tests\test_cast_crew_slider_and_tmdb_bridge.py ....              [ 84%]
backend\tests\test_subscriptions_favorites_page.py ..                    [ 87%]
backend\tests\test_actors_filmography_bridge.py ...                      [ 92%]
backend\tests\test_collections_categories_split.py ..                    [ 96%]
backend\tests\test_fix_sidebar_and_hydration_bugs.py ..                  [100%]

======================= 57 passed, 4 warnings in 2.97s ========================
```

## Risks and unknowns
- Drag vs Click ambiguity on touch and trackpads: `hasDraggedRef` with 6px threshold ensures swiping to scroll does not mistakenly trigger modal popup.

## Concept to explain to the user
- Contextual Deep Discovery (1-Click Filmography Bridge) — Kino tomosha qilayotgan foydalanuvchiga boshqa sahifaga o'tib ketmasdan, to'g'ridan-to'g'ri ijodkor ustiga bosish orqali uning butun karyerasidagi filmlarni bir zumda taqdim etish.

## Next step
- Await user verification on movie or series detail page.
