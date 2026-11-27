# Slice Report: 2026-11-27-smm-climax-window-alignment

## What was done
1. Fixed the 60–90s premature cut bug by moving sparse `anchor_sec` from `peak - 120.0` to `peak - 35.0`, wrapping `scan_start..scan_end` symmetrically around `mapped_peak`, and raising the late-act ceiling from `0.84` to `0.91` (`scraper/smm_scene_finder.py`, `scraper/smm_pipeline.py`).
2. Added adaptive SRT digest buckets (`30s/45s/60s`), `backup_peak_sec`/`backup_ratio` credits fallback, stricter Vision `excitement_score` rubric (`excitement * 12 + cue_match * 16`), and TDD tests (`backend/tests/test_smm_scene_scorer.py`, `backend/tests/test_smm_pipeline_and_telegram_pub.py`).
3. Verified locally on `#1272` (*Mashaqqatlar sari S05E14*, `2096.41 -> 2199.08`) and `#1014` (*Qasoskorlar 4 Intiho*, `8619.54 -> 8636.24`), and updated `STATE.md` and `docs/learned.md`.

## Changed files
- `scraper/smm_scene_finder.py` - Adaptive SRT buckets, `peak - 35s` anchor, `0.91` ceiling, and `backup_ratio`.
- `scraper/smm_pipeline.py` - Peak-centered `scan_start`/`scan_end` inside bounded chunk and `backup_ratio` credits fallback.
- `scraper/smm_scene_scorer.py` - Stricter action/drama `excitement_score` prompt and semantic weights (`12` / `16`).
- `backend/tests/test_smm_scene_scorer.py` - Updated credits ceiling check (`0.91`) and added adaptive/late-act alignment test.
- `STATE.md`, `docs/learned.md` - Session tracking and concept documentation.

## check output
```text
ruff check & ruff check --select F821: All checks passed!
pytest test_smm_clipper + test_smm_scene_scorer + test_smm_pipeline_and_telegram_pub + test_smm_worker + test_catalog_worker: 75 passed
pytest test_smm_api.py: 10 passed
pytest bot/tests/: 116 passed
```

## Risks and unknowns
- Late-act scenes near `0.90–0.91` may occasionally touch short dubbing end-credits if Telegram file duration differs from SRT span; `backup_ratio` mitigates this cleanly.

## Concept to explain to the user
- Peak-Centered Sliding Window (`anchor = peak - 35s`, `ratio <= 0.91`).

## Next step
- Push slice to `origin/feat/smm-autopilot` and `origin/main`, prioritize Jobs `#10`, `#13`, `#19` on Render, and inspect finished video outputs.
