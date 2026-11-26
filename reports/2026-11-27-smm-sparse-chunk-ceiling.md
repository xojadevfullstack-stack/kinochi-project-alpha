# Slice Report: 2026-11-27-smm-sparse-chunk-ceiling

## What was done
1. Fixed `70%` FFmpeg empty-output failure (`frame=0` on `Job #13` *Game of Thrones S03E09*) caused by `scan_start` jumping past the sparse download's end when `target_ratio` was capped at `0.84` while `mapped_peak` remained near `98.5%` (`2932s > 2728s`): clamped `scan_start` and `scan_end` strictly inside `[chunk_floor .. chunk_floor + duration_sec + 35.0]`.
2. Increased default `SMM_RENDER_TIMEOUT_SEC` from `240s` to `360s` in `smm_clipper.py` so `0.1-vCPU` Render handles `720p` anime + `0.35s` poster cover + watermark blur without timing out at `70%`.
3. Added TDD test in `test_smm_pipeline_and_telegram_pub.py` and verified live local cut on `msg #1681` (`start_sec=2590.73`, Red Wedding scene).

## Changed files
- `scraper/smm_pipeline.py` - Clamp `scan_start` and `scan_end` inside downloaded sparse chunk bounds.
- `scraper/smm_clipper.py` - Raise default `SMM_RENDER_TIMEOUT_SEC` to `360s`.
- `backend/tests/test_smm_pipeline_and_telegram_pub.py` - TDD ceiling test for late-SRT sparse bounds.
- `STATE.md` - Session verification metrics.

## check output
```text
ruff check & ruff check --select F821: All checks passed!
pytest test_smm_clipper + test_smm_scene_scorer + test_smm_pipeline_and_telegram_pub + test_smm_worker + test_catalog_worker: 73 passed in 27.86s
pytest test_smm_api.py: 10 passed in 2.55s
pytest bot/tests/: 116 passed in 6.84s
Local msg #1681 re-cut: OK_LOCAL start_sec=2590.73, blur_boxes=[{'x': 0.845, 'y': 0.03, 'w': 0.155, 'h': 0.13, 'kind': 'watermark'}]
```

## Risks and unknowns
- Render free/starter rebuilds triggered by concurrent pushes can still terminate an active `70%` job if both agents deploy during rendering.

## Concept to explain to the user
- Coupled Sparse Download & Scan Window Invariant (`scan_end <= chunk_floor + headroom`).

## Next step
- Push commit to `origin/feat/smm-autopilot` & `origin/main`, then reset `Job #13` and `Job #14` to `generating` after Render deploys.
