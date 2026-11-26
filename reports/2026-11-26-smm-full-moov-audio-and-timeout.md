# Slice Report: 2026-11-26-smm-full-moov-audio-and-timeout

## What was done
1. Fixed missing audio track in long sparse-downloaded MP4s (`clip_8.mp4`, `msg #5015` where `moov` is `5.75 MB > 4 MB`, cutting off Track 2 Audio `stco` at `4.95-5.74 MB`) by dynamically fetching through `parse_mp4_moov_end`, covering all substantial `stco/co64` tracks in `compute_sparse_byte_range`, and failing loudly if input audio is dropped from rendered output.
2. Added subprocess/network timeout guards (`15s` FFmpeg audio volume probe, `12s` top-3 Vision models, `90s` scene scorer wrapper) and clamped `scan_start >= effective_dur * eff_ratio` so sparse cuts never scan/render before downloaded media bytes.
3. Added TDD tests (`test_smm_clipper.py`, `test_smm_scene_scorer.py`, `test_smm_pipeline_and_telegram_pub.py`), verified live cut on `msg #5015` (`Stream #0:1 Audio: aac`, `mean_volume: -25.5 dB`, `max_volume: -7.1 dB`), and updated `STATE.md` and `docs/learned.md`.

## Changed files
- `scraper/smm_clipper.py` - Dynamic `moov` size fetch, multi-track `stco/co64` bounds, silent-output guard.
- `scraper/smm_scene_scorer.py` - Subprocess timeout on `_measure_audio_db` and bounded Vision model fallback timeouts.
- `scraper/smm_pipeline.py` - Sparse `scan_start` floor clamp and `90s` scorer timeout fallback.
- `backend/tests/test_smm_clipper.py` - 3 TDD regression tests for `>4MB moov`, multi-track `stco`, and dropped-audio detection.
- `backend/tests/test_smm_scene_scorer.py` - Subprocess timeout recovery test.
- `backend/tests/test_smm_pipeline_and_telegram_pub.py` - Sparse scan floor boundary assertion.
- `STATE.md`, `docs/learned.md` - Session verification log and concept note.

## check output
```text
ruff check (6 edited files): All checks passed!
ruff check --select F821 (6 edited files): All checks passed!
alembic heads: h8c9d0e1f2a3 (head)
pytest test_smm_clipper + test_smm_scene_scorer + test_smm_pipeline_and_telegram_pub + test_smm_worker + test_catalog_worker: 61 passed in 48.77s
pytest test_smm_api.py: 9 passed in 2.46s
pytest bot/tests/: 116 passed in 7.21s
Live msg #5015 cut verification: Stream #0:1 Audio: aac, 48000 Hz, stereo, n_samples: 4235994, mean_volume: -25.5 dB, max_volume: -7.1 dB
```

## Risks and unknowns
- Non-faststart MP4s with `moov` > `20 MB` at EOF still exceed tail fallback cap, though standard 480p-1080p MP4 `moov` headers are `1-8 MB`.
- Make.com Facebook webhook execution for `Job #8` still depends on Render finishing the re-cut cleanly (`clip_8.mp4`).

## Concept to explain to the user
- Dynamic MP4 `moov` atom size parsing + multi-track `stco` bounding (kitob mundarijasining qolgan betlarini ham to'liq yuklab olish).

## Next step
- Deploy commits to `origin/main`, reset `SMM Job #8` (`#1088`) to `generating`, and verify non-silent audio on Render `/api/v1/smm/jobs/8/video`.
