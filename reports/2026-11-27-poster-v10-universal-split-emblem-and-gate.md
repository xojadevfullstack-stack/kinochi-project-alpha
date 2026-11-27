# Slice Report: 2026-11-27-poster-v10-universal-split-emblem-and-gate

## What was done
1. Added universal `layout_mode` routing (`standard`, `split_around_center` leaving central 20% subject unobstructed, `emblem_inner` preserving badges/circles and cleaning bright interior text with `_clean_bright_emblem_interior`) plus dark/thin gothic support (`_REGULAR_FONT_MAP["gothic"]`) and crisp dark/bright rim outlines.
2. Fixed spray-stencil letter spacing (`gap >= 9px`) preventing letter fusion (`Arra odam S#1065`, renamed in DB from `"Binzopila odam"`), fixed `sub_y` positioning below centered `respect_box_bounds` main titles, updated `_detect_residual_text_boxes` to ignore background building signs (`Muqaddima 52 WEST`), and removed false-positive Uzbek spelling rejections from `_verify_rendered_poster_quality`.
3. Added regression unit tests for `split_around_center` and `emblem_inner` preservation, ran blind verification on 6 complex Uzbek posters, and passed all linters and test suites.

## Changed files
- `backend/app/infrastructure/external/poster_localizer.py` - Universal `split_around_center`, `emblem_inner`, `_clean_bright_emblem_interior`, spray letter spacing, background-sign guard, and visual-only quality gate.
- `backend/tests/test_poster_localizer.py` - Tests for split center-gap preservation, `emblem_inner` textless bypass, spray upright drips, and low-score quality gate rejection.
- `STATE.md` - Recorded v10 universal rules and test results.
- `docs/learned.md` - Added subject-flanking split layout & saturation-guarded bright-emblem cleanup concept.

## check output
```text
ruff check backend/app/infrastructure/external/poster_localizer.py backend/tests/test_poster_localizer.py
All checks passed!

alembic heads
i9d0e1f2a3b4 (head)

pytest -p no:cacheprovider tests/test_smm_pipeline_and_telegram_pub.py tests/test_smm_worker.py tests/test_poster_localizer.py tests/test_poster_triggers.py tests/test_posters_storage.py tests/test_fix_f013_swallowed_exceptions.py -q
84 passed in 21.58s

pytest -p no:cacheprovider bot/tests -q
116 passed in 6.77s
```

## Risks and unknowns
- Tight custom emblems whose original dark letters protrude outside the inner white fill (`Demon Slayer` outer `D`/`S` tips on red ring) can still trigger quality gate `gate=False` (safely keeping the original poster rather than publishing artifacts).
- Unrelated dirty files in workspace remain untouched and unstaged.

## Concept to explain to the user
- **Subject-Flanking Split Layout & Bright-Emblem Cleanup:** Markaziy qahramonni yopmasdan sarlavhani ikki yonga ajratish hamda emblemali doira ichidagi matnni qizil chetiga tegmasdan tozalash — xuddi qizil muhr chizig'ini buzmasdan oq o'rtasidagi eski yozuvni o'chirish kabi.

## Next step
- Render deploy (`origin/main`) ko'tarilgach `Yigitlar #1000` va tanlangan posterlarni jonli bazaga yuklashni tasdiqlash.
