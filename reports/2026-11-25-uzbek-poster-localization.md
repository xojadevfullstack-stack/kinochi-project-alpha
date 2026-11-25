# Slice Report: 2026-11-25-uzbek-poster-localization

## What was done
1. **Slice 1 (Telegram Poster Storage & Proxy):** Added `send_photo_with_result(..., message_thread_id)` and Redis-cached `download_file_bytes()` to `telegram_client.py`; created `backend/app/api/v1/posters.py` (`upload_poster_to_telegram()` storing in `STORAGE_CHANNEL_ID` + media forum topic, and `GET /api/v1/posters/tg/{file_id}` immutable public proxy).
2. **Slice 2 (Poster Localization Engine):** Added `tmdb_client.get_textless_poster()`, Gemini Vision style/box analysis + OpenCV `cv2.inpaint` cleanup + `Pillow` gradient/shadow typography renderer (`poster_localizer.py`) with bundled OFL `.ttf` fonts (`backend/app/assets/fonts/`).
3. **Slice 3 (Automatic Triggers & Tests):** Hooked `schedule_poster_localization()` background tasks into `movies.py`, `series.py`, and `audit.py` whenever `tmdb_id` or an external `poster_url` is attached/updated; added 12 unit/integration tests across `test_posters_storage.py`, `test_poster_localizer.py`, and `test_poster_triggers.py`.

## Changed files
- `backend/app/infrastructure/telegram/telegram_client.py` - Topic-aware `send_photo_with_result()` and cached `download_file_bytes()`
- `backend/app/api/v1/posters.py` - Telegram channel/topic upload helper, `/posters/tg/{file_id}` proxy, `/posters/localize/{media_type}/{media_id}`, and background scheduler
- `backend/app/infrastructure/external/tmdb_client.py` - `get_textless_poster()` (`include_image_language=null,xx`)
- `backend/app/infrastructure/external/poster_localizer.py` - Vision style analysis, OpenCV title box cleanup, Pillow Uzbek title renderer, and end-to-end orchestrator
- `backend/app/api/v1/movies.py`, `backend/app/api/v1/series.py`, `backend/app/api/v1/audit.py`, `backend/app/main.py` - Router registration and automatic background triggers
- `requirements.txt`, `backend/requirements.txt`, `backend/pyproject.toml`, `backend/app/assets/fonts/*` - `pillow>=10.0,<12.0` and bundled OFL cinema `.ttf` fonts
- `backend/tests/test_posters_storage.py`, `backend/tests/test_poster_localizer.py`, `backend/tests/test_poster_triggers.py` - Verification suites

## check output
```text
All checks passed! (ruff check on new/modified poster files)
26 passed, 5 warnings in 9.05s (test_poster_triggers.py, test_poster_localizer.py, test_posters_storage.py, test_fix_f013_swallowed_exceptions.py, test_open_topic.py, test_series_perf_c04.py, test_write_paths_gate.py, test_alembic.py)
115 passed in 6.86s (bot/tests/)
h8c9d0e1f2a3 (head) (alembic heads)
```

## Risks and unknowns
- Render production container needs `PUBLIC_API_BASE_URL` (or `RENDER_EXTERNAL_URL`) configured so `/api/v1/posters/tg/{file_id}` URLs resolve to the live backend domain.
- If `GEMINI_API_KEY` is missing or rate-limited during manual-URL fallback (when TMDb has no textless poster), `poster_localizer.py` falls back to default bottom typography placement without erasing existing text.

## Concept to explain to the user
- **Textless-First + Immutable Telegram `file_id` Proxy:** Tijoriy Image-to-Image AI lar mashhur aktyorlar yuzi va mualliflik huquqi sababli posterlarni bloklaganda, avval TMDb dan matnsiz toza poster olib (yoki faqat eski matn qutisini OpenCV bilan tozalab) Pillow orqali bexato o'zbekcha shrift chizish hamda 1 soatda eskiradigan Telegram `getFile` linkini proksi endpoint orqali doimiy URL ga aylantirish.

## Next step
- Verify live generation in production (`PUBLIC_API_BASE_URL` + `GEMINI_API_KEY`) by attaching a `tmdb_id` or external `poster_url` on one movie/series.
