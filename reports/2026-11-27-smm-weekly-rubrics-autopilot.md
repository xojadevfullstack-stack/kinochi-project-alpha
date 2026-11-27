# Slice Report: 2026-11-27-smm-weekly-rubrics-autopilot

## What was done
1. Built `scraper/smm_rubric_planner.py` to schedule 4 weekly prime-time (`21:00 UTC+5`) Golden Standard rubrics (`tavsiya` Mon, `bilasizmi` Wed, `yangiliklar` Fri, `kadr_ortida` Sun) alongside daytime `scene` clips, convert numeric codes to natural Uzbek 2+2 speech, and transliterate Latin Uzbek TTS text to Cyrillic `ў/қ/ғ/ҳ` for accurate `Charon` articulation.
2. Built `scraper/smm_rubric_visuals.py` & `scraper/smm_rubric_engine.py` implementing all 4 approved covers (`T1`, `F2`, `Y2`, `B`), Cinematic Red HUD/Outro (`#E50914`, gold star ONLY for IMDb), zero-lag `-60ms` ASS subtitles, Haar/gradient subject centering (`compute_subject_focus_x`), and sequential `<512MB RAM` Render-safe FFmpeg concat + single overlay pass (`low_ram=True`).
3. Wired rubric selection (`auto_pick_catalog_movie(db, now_local=...)`), sparse-bounded generation (`process_generating_job` with safe `scene` fallback), and `backend/app/api/v1/smm.py` `clip_mode` schema without adding extra DB migrations; added TDD unit & FFmpeg smoke tests and updated `STATE.md`, `docs/learned.md`, and `docs/failures.md`.

## Changed files
- `scraper/smm_rubric_planner.py` - Weekly 4-rubric schedule, DB selector, `digits_to_uz_2plus2_spoken`, and `lat_to_uz_cyrillic_tts`
- `scraper/smm_rubric_visuals.py` - Approved `T1/F2/Y2/B` covers, HUD/Outro PNGs, and zero-lag ASS subtitles
- `scraper/smm_rubric_engine.py` - Auto subject centering, grounded Gemini script, single-take `Charon` TTS, and Render-safe FFmpeg pipeline
- `scraper/smm_worker.py` - Evening rubric picker hook and `process_generating_job` routing with `scene` fallback
- `backend/app/api/v1/smm.py` - Expanded `SmmClipJobCreate.clip_mode` allowed literals
- `backend/tests/test_smm_rubric_planner.py` - Planner, phonetic converter, and DB rubric query tests
- `backend/tests/test_smm_rubric_engine.py` - Visuals, ASS, focus centering, single-take flow, and real FFmpeg smoke test
- `backend/tests/test_smm_worker.py` - Weekly rubric prime-slot pick and worker routing regression tests

## check output
```text
ruff check (touched files): All checks passed!
alembic heads: i9d0e1f2a3b4 (head)
SMM + Rubric suite (test_smm_scene_scorer + test_smm_rubric_planner + test_smm_rubric_engine + test_smm_facts_clipper + test_smm_clipper + test_smm_pipeline_and_telegram_pub + test_smm_worker): 85 passed in 34.59s
SMM API suite (test_smm_api.py): 10 passed, 1 warning in 2.65s
Bot test suite (bot/tests/): 116 passed in 7.41s
```

## Risks and unknowns
- Running live `Charon` TTS on Render relies on Gemini API daily quotas (`10 req/day` free tier per model); automatic fallback to `scene` clips prevents missed posting slots on `429`.
- Full-length movie sparse chunks (`48 MB`) depend on movie source scenes matching rubrics; dedicated YouTube trailer/BTS fetching inside Render is intentionally deferred to keep `512 MB RAM` safe.

## Concept to explain to the user
- *Sequential Low-RAM Concat (`concat -c copy`) + Subject Focus (`compute_subject_focus_x`)* — katta 10 ta klipni bir vaqtda xotiraga ochib serverni qulatmaslik uchun ularni bittadan kadr markazini aniqlab kesish, keyin qayta siqmasdan (`-c copy`) ulab bitta yengil yakuniy qatlam bilan chiqarish.

## Next step
- Push `feat/smm-autopilot` to `main` for Render deployment and verify one live prime-time `21:00` rubric job in Admin `/smm` and Telegram preview.
