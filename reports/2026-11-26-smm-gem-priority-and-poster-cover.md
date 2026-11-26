# Slice Report: 2026-11-26-smm-gem-priority-and-poster-cover

## What was done
1. Added branded 9:16 frame-0 poster cover support (`build_clip_cover_image`, `render_vertical_clip(..., cover_image_path, cover_duration_sec=0.35)`, `_fetch_poster_bytes` supporting both external URLs and internal `/api/v1/posters/tg/{file_id}`, and `_resolve_media_poster_url` in `smm_worker.py`). Audio runs continuously from `0.0s` while `overlay=enable='lt(t,0.35)'` guarantees Instagram, Facebook, TikTok, YouTube Shorts, and Telegram display the media poster on grid/thumbnails.
2. Upgraded `auto_pick_catalog_movie()` from blind `id.desc()` to Gem-Priority (`imdb_rating * 10 + recent >= 2023 bonus + view_count * 2`), skipping `< 5.8` pre-2023 flops so SMM quotas are never wasted on low-engagement films.
3. Enqueued 24 SRT-verified high-engagement gems (`Job #9..#32`, alternating blockbusters/new 2024-2026 releases, mega series episodes, and viral anime films for 8 days at 3/day) and logged Render Paid Plan `1080p High` quality upgrade to `STATE.md` Backlog.

## Changed files
- `scraper/smm_clipper.py` - `build_clip_cover_image` and single-pass `overlay=enable='lt(t,0.35)'` in `render_vertical_clip`.
- `scraper/smm_pipeline.py` - `_fetch_poster_bytes` and temporary cover build/cleanup around render.
- `scraper/smm_worker.py` - Gem-Priority `auto_pick_catalog_movie()` and `_resolve_media_poster_url`.
- `backend/tests/test_smm_clipper.py` - Real FFmpeg verification that frame 1 shows cover and `t=1.25s` shows video.
- `backend/tests/test_smm_pipeline_and_telegram_pub.py` - Pipeline poster fetch & graceful fallback test.
- `backend/tests/test_smm_worker.py` - Gem-Priority ordering and low-IMDb skip test.
- `STATE.md`, `docs/learned.md` - Backlog note (`1080p High` on paid Render), verification metrics, and concept note.

## check output
```text
ruff check & ruff check --select F821: All checks passed!
alembic heads: h8c9d0e1f2a3 (head)
pytest test_smm_clipper + test_smm_scene_scorer + test_smm_pipeline_and_telegram_pub + test_smm_worker + test_catalog_worker: 66 passed in 29.67s
pytest test_smm_api.py: 9 passed in 2.73s
pytest bot/tests/: 116 passed in 9.06s
```

## Risks and unknowns
- Low-bitrate (`~600 kb/s`) legacy Telegram source files (`Avengers msg #2544`) remain capped by source quality until Render is upgraded off `0.1 vCPU / 512 MB` (`low_ram` kept for safety; `1080p High` tracked in `STATE.md` Backlog).
- Uzbek poster localization only appears on clips whose `poster_url` has already been localized to `/api/v1/posters/tg/...` (respecting Cloudflare daily reset limits).

## Concept to explain to the user
- Single-pass `Frame-0` poster overlay + Gem-Priority queue scoring.

## Next step
- Commit & push to `origin/feat/smm-autopilot` & `origin/main`, reset `Job #9` (and any un-covered `#10..#32` once deployed) so all 24 gem clips render with their poster cover.
