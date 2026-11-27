# Slice Report: 2026-11-27-poster-v9-vertical-periodic-and-wrap

## What was done
1. Fixed vertical poster title orientation (`_is_vertical_title_box` + `90°` CCW rotation without drop shadow when flat, vertical box midpoint centering) and guarded `is_giant_logo` against mistaking tall narrow vertical titles (`Legion #1119`) for giant centered logos.
2. Added automatic 2-line wrapping (`len >= 18` with >= 2 words), per-line ink-bbox horizontal centering, `<= 0.14` box-center jitter snap (`sw / 2`), and vertical box expansion (`box_h >= 0.135 * sh`) for long single-line titles (`Yakkaxon daraja oshirish #1015`, pixel center error `0.0px / -0.5px`).
3. Implemented procedural periodic-table emerald chemical squares (`_is_periodic_tile_style`, `_render_periodic_tile_poster`, dynamic `_calc_tile_size`) with symmetric line-2 centering (`-48.0px -> -1.5px`) for `Mashaqqatlar sari #1001`, re-uploaded live Telegram posters & DB URLs (`#1001`, `#1015`, `#1119`), visually verified all 3, and updated tests and docs.

## Changed files
- `backend/app/infrastructure/external/poster_localizer.py` - Vertical title rotation + `is_giant_logo` exclusion guard, per-line ink-bbox centering, near-center `sw/2` snap, long single-line auto-wrap, and symmetric periodic-tile chemical squares renderer.
- `backend/tests/test_poster_localizer.py` - Unit & regression tests for vertical title orientation, long single-line wrap (`YAKKAXON\nDARAJA OSHIRISH`), periodic-tile emerald squares & symmetric line-2 centering, near-center jitter snap, and vertical `is_giant_logo` exclusion.
- `STATE.md` - Recorded v9 status, symmetry measurements, and verification outputs.
- `docs/learned.md` - Added aspect-aware vertical orientation & procedural periodic-tile concept note.

## check output
```text
ruff check backend/app/infrastructure/external/poster_localizer.py backend/tests/test_poster_localizer.py
All checks passed!

alembic heads
i9d0e1f2a3b4 (head)

pytest -p no:cacheprovider tests/test_smm_pipeline_and_telegram_pub.py tests/test_smm_worker.py tests/test_poster_localizer.py tests/test_poster_triggers.py tests/test_posters_storage.py tests/test_fix_f013_swallowed_exceptions.py -q
80 passed in 9.44s

pytest -p no:cacheprovider bot/tests -q
116 passed in 6.60s
```

## Risks and unknowns
- Unrelated local workspace edits (`admin-panel/`, `backend/app/api/deps.py`, `scraper/catalog_worker.py`, etc.) were left unstaged.
- Posters without `"periodic_tile"` explicitly returned by Gemini Vision rely on the English title / prompt keyword cue (`Breaking Bad` / `chemical periodic elements`) to trigger emerald element squares.

## Concept to explain to the user
- **Orientatsiya va Protsedural Motiv Himoyasi (`_is_vertical_title_box` + `_render_periodic_tile_poster`)**: Uzun va ingichka vertikal sarlavhani katta markaziy multfilm logotipi bilan adashtirmaslik hamda *Mashaqqatlar sari* kabi yashil kimyoviy element kataklarini oddiy shriftdan alohida matematik shablon bilan chizish — xuddi yo'l belgisining ramkali belgisini oddiy harf deb o'ylamaslik kabi.

## Next step
- Render deploy (`origin/main`) ko'tarilgach sayt (`#1001`, `#1015`, `#1119`) va `Job #9..#16` kliplari chiqishini kuzatish.
