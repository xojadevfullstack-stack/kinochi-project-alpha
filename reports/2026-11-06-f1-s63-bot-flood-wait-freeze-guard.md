# Slice Report: 2026-11-06-f1-s63-bot-flood-wait-freeze-guard

## What was done
1. Diagnosed root cause of the 45+ minute scraper freeze on "Iblislar qotili: Cheksiz poyezd": `@asilmediabot` returned a long rate-limit message ("41 daqiqadan so'ng urinib ko'ring"), causing `get_flood_wait_seconds()` to return 2465s and `asyncio.sleep(2465)` to blindly sleep for 41 minutes, repeated across items until each hit the 20-minute item timeout.
2. Implemented `MAX_BOT_FLOOD_WAIT = 120` guard, `BotFloodWaitError`, and `handle_bot_flood_wait()` in `scraper/telethon_moderator_pipeline.py` across all 7 flood points; long flood waits (> 120s) now abort without sleeping, flag the bot in `StateManager`, fail fast with descriptive reason, and prevent the scraper batch loop in `run_scraper.py` from hammering the throttled bot.
3. Terminated the frozen background scraper process (PID 51196), recovered database `ingest_items` rows, wrote comprehensive unit test `backend/tests/test_bot_flood_wait_guard.py` (4/4 passed), and verified full test suite.

## Changed files
- `scraper/telethon_moderator_pipeline.py` - Added `MAX_BOT_FLOOD_WAIT`, `BotFloodWaitError`, and `handle_bot_flood_wait()` across all 7 flood wait points; caught error in `run_item`.
- `scraper/run_scraper.py` - Added bot flood check before item loop, handled `BotFloodWaitError` without blocking, fixed `needs_review` status overwrite bug.
- `backend/tests/test_bot_flood_wait_guard.py` - Unit test verifying text extraction, fast abort without sleep for > 120s, and `run_item` fast fail.
- `backend/tests/test_run_scraper_flood_wait.py` - Normalized enum status assertions (`pending`/`queued`, `completed`/`published`).

## check output
```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Администратор\Desktop\kino bot project\kinochi project\backend
configfile: pyproject.toml
plugins: anyio-4.14.1, asyncio-1.4.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 13 items

backend\tests\test_bot_flood_wait_guard.py ....                          [ 30%]
backend\tests\test_run_scraper_flood_wait.py ..                          [ 46%]
backend\tests\test_search_punctuation_tolerance.py ..                    [ 61%]
backend\tests\test_anime_enricher_guards.py ..                           [ 76%]
backend\tests\test_enricher_root_fixes.py ...                            [100%]

======================= 13 passed, 3 warnings in 4.60s =======================
```

## Risks and unknowns
- `@asilmediabot` maintains its own server-side flood timeout; while our scraper now aborts and fails fast rather than freezing for 45 minutes, downloading from `@asilmediabot` will fail until their rate limit window expires (typically 30-60 mins).
- Other sources (Uzmovi, Kinochilar, AniToob, Animeelar) are unaffected and can be processed without delay.

## Concept to explain to the user
- Fast-Fail and Circuit Breaker (Tezkor to'xtatish va avariya o'chirgichi): Yo'lda katta to'siq yoki ko'chki chiqqanda mashinani 1 soat gazini bosib kutib turish o'rniga, darhol to'xtab haydovchiga xabar berish va aylanma yo'lni tanlash.

## Next step
- Monitor scraper operation in Admin Panel, test subsequent media downloads across active sources.
