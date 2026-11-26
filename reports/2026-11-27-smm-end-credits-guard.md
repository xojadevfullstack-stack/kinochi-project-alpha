# Slice Report: 2026-11-27-smm-end-credits-guard

## What was done
1. Prevented SRT viral scene anchoring from overshooting into silent end credits (`Job #13` Game of Thrones S03E09 at `3009s`): clamped `peak <= srt_end - 45s`, pulled `anchor_sec = peak - 120s`, and capped `target_ratio <= 0.84`.
2. Updated `select_best_scene_start` fallback to propagate `is_credits` cleanly and added an automatic `0.50` midpoint sparse re-download fallback in `create_smart_smm_clip` whenever all scanned windows are flagged `is_credits=True`.
3. Added 2 TDD tests (`test_smm_scene_scorer.py`), updated `STATE.md` and `docs/learned.md`, and verified all checks cleanly.

## Changed files
- `scraper/smm_scene_finder.py` - Avoid last 10% credits in prompt, clamp `peak <= srt_end - 45s`, `anchor = peak - 120s`, cap `target_ratio <= 0.84`.
- `scraper/smm_scene_scorer.py` - Expose `is_credits` accurately on rejected-fallback results.
- `scraper/smm_pipeline.py` - Automatically retry at `0.50` midpoint when `score_meta.get("is_credits")` is True.
- `backend/tests/test_smm_scene_scorer.py` - TDD tests for end-credits ratio cap and `is_credits` fallback reporting.
- `STATE.md`, `docs/learned.md` - Verification summary and concept note.

## check output
```text
ruff check & ruff check --select F821: All checks passed!
pytest test_smm_clipper + test_smm_scene_scorer + test_smm_pipeline_and_telegram_pub + test_smm_worker + test_catalog_worker: 72 passed
pytest test_smm_api.py: 10 passed
pytest bot/tests/: 116 passed
```

## Risks and unknowns
- Unusually short episodes or films whose credits exceed 16% of total duration might still need the `0.50` Vision `is_credits` retry fallback.

## Concept to explain to the user
- Pre-credits sparse anchoring (`ratio <= 0.84`) + `is_credits` midpoint recovery.

## Next step
- Commit & push to `origin/feat/smm-autopilot` & `origin/main` and reset `Job #13` (`#1119` Game of Thrones S03E09) so it re-cuts the actual Red Wedding scene cleanly.
