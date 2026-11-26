# Slice Report: 2026-11-26-smm-corner-watermark-consensus

## What was done
1. Hardened `check_frames_for_ads_or_nsfw` Vision prompt to scan all four corners (including dark-on-dark areas) and strictly populate `blur_boxes` whenever a corner logo/watermark is visible.
2. Added `_infer_corner_watermark_boxes` prose recovery in `parse_scene_vision_response`, inward corner padding (`>= 0.75` and thin `0.025–0.06` boxes) in `_sanitize_blur_boxes`, and cross-candidate `blur_boxes` merging across evaluated clean candidates in `select_best_scene_start`.
3. Added 2 TDD tests (`test_smm_scene_scorer.py`), updated `STATE.md` and `docs/learned.md`, and verified all checks cleanly.

## Changed files
- `scraper/smm_scene_scorer.py` - 4-corner Vision prompt, prose corner box recovery, bottom/right padding, candidate box aggregation.
- `backend/tests/test_smm_scene_scorer.py` - TDD tests for reason recovery, tiny/tight corner padding, and candidate box consensus.
- `STATE.md`, `docs/learned.md` - Session verification log and concept note.

## check output
```text
ruff check & ruff check --select F821: All checks passed!
alembic heads: h8c9d0e1f2a3 (head)
pytest test_smm_scene_scorer + test_smm_clipper + test_smm_pipeline_and_telegram_pub + test_smm_worker: 55 passed in 59.66s (re-run verified after final edit)
pytest test_smm_api.py: 9 passed
pytest bot/tests/: 116 passed
```

## Risks and unknowns
- If Gemini completely skips seeing a tiny low-contrast logo on all inspected frames AND omits mentioning it in `reason`, no blur is applied (by design to avoid false blurs on clean films).

## Concept to explain to the user
- 4-Corner Vision Prompt + Prose Corner Recovery + Cross-Candidate Watermark Consensus.

## Next step
- Push to `origin/feat/smm-autopilot` & `origin/main` and re-cut `SMM Job #8` (`#1088`) so bottom-right Kinochilar logo is blurred cleanly.
