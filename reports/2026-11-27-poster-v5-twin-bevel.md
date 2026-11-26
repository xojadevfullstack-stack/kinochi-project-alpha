# Slice Report: 2026-11-27-poster-v5-twin-bevel

## What was done
1. **Textless Twin MAE Matcher (`tmdb_client.py`):** Added `reference_bytes`, `placement`, and `max_mae=25.0` matching across `w92` TMDb textless candidates so localized posters never swap to zoomed-out IMAX frames or unrelated teasers (e.g., Sorting Hat).
2. **Mislabeled Textless Cleanup + 2x Studio Typography (`poster_localizer.py`):** Added mislabeled-textless guard (`Sijjin 8`), `_inpaint_boxes` with soft edge blending, `2x` supersampled `chiseled`/`metallic` 3D bevels, anti-aliased `rim_color` outlines, trailing `accent_color` (e.g., blood-red `8`), 2-tier subtitles, `safety_tolerance="5"`, and 7 new OFL fonts in `backend/app/assets/fonts/`.
3. **Live DB Update & Verification:** Localized and updated 5 live records (`Movie #917 Sijjin 8`, `Movie #810 Garri Potter 1`, `Movie #827 Qasoskorlar 4`, `Series #1120 Shogun`, `Series #1125 Institut`) in Telegram + PostgreSQL + cleared Redis cache.

## Changed files
- `backend/app/infrastructure/external/tmdb_client.py` - Parallel `w92` MAE textless twin matching
- `backend/app/infrastructure/external/poster_localizer.py` - Mislabeled textless guard, `_inpaint_boxes`, 2x supersampled 3D bevel/rim/accent/subtitle renderer, `safety_tolerance="5"`
- `backend/app/assets/fonts/*` - Added `PirataOne-Regular.ttf`, `CinzelDecorative-Bold.ttf`, `Anton-Regular.ttf`, `LuckiestGuy-Regular.ttf`, `Almendra-Bold.ttf`, `Metamorphous-Regular.ttf`, `BebasNeue-Regular.ttf`
- `backend/tests/test_poster_localizer.py` - Added 3 regression tests (`twin MAE`, `mislabeled textless cleanup`, `gothic chiseled + red accent`)

## check output
```text
All checks passed! (ruff check)
27 passed, 1 warning in 3.51s (test_poster_localizer.py, test_poster_triggers.py, test_posters_storage.py, test_fix_f013_swallowed_exceptions.py)
116 passed in 6.77s (bot/tests/)
i9d0e1f2a3b4 (head) (alembic heads)
```

## Risks and unknowns
- Render needs redeploy from this commit so new movies/series created in production use the upgraded `v5` engine automatically; existing 5 records were updated directly in PostgreSQL.

## Concept to explain to the user
- **Perceptual Twin Matching (`MAE`) + Mislabeled-Asset Verification:** TMDb'dagi eng yuqori ball olgan "matnsiz" poster aslida boshqa kadr bo'lishi yoki ustida baribir xorijiy matn qolib ketgan bo'lishi mumkin; shuning uchun kichik `w92` nusxalarni solishtirib aynan egizagini tanlash va rasmning o'zini qayta tekshirish ikki qavat matn hamda zoom-out xatolarini yo'qotadi.

## Next step
- Refresh the website pages for `#917 (Sijjin 8)`, `#810 (Garri Potter 1)`, `#827 (Qasoskorlar 4)`, `#1120 (Shogun)`, and `#1125 (Institut)` to confirm the live updated posters render cleanly.
