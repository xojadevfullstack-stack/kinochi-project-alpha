# Slice Report: 2026-10-28-crop-youtube-ui-and-zero-gap-backdrop

## What was done
1. Cropped all YouTube UI (channel logo "Trailer Blend", video title, and center pause icons) out of `MovieCard.tsx` using responsive over-scan scaling (`w-[300%] h-[140%] pointer-events-none`) with `fs=0` and `disablekb=1`, rendering a pristine native video preview on desktop hover and mobile hold.
2. Eliminated the top black gap in `HeroTrailerBackdrop.tsx` (shown in Image 4) by extending the background layer upwards (`-top-24 sm:-top-28 md:-top-32`) under the fixed navbar and scaling the iframe (`scale-125 md:scale-115`), seamlessly gluing the video to the top edge and hiding YouTube headers on both mobile and desktop.
3. Verified with automated regression suite (`test_youtube_clean_and_hero_gap.py`, 26 passed, 0 lint errors).

## Changed files
- `website/components/catalog/MovieCard.tsx` - Added oversized over-scan container cropping YouTube channel avatars and titles.
- `website/components/media/HeroTrailerBackdrop.tsx` - Extended background container behind top navbar, scaled viewport to eliminate top gaps and crop YouTube UI.
- `backend/tests/test_youtube_clean_and_hero_gap.py` - Automated test suite verifying YouTube UI cropping and zero gap.
- `docs/learned.md` - Added "Iframe Over-Scanning & Zero-Gap Fluid Backdrop" concept.

## check output
```text
pytest backend/tests/test_youtube_clean_and_hero_gap.py backend/tests/test_card_trailer_hover.py backend/tests/test_hero_trailer_scroll_dim.py backend/tests/test_hero_trailer_backdrop.py backend/tests/test_hero_trailer_cinema_mode.py backend/tests/test_movie_card_itv_redesign.py backend/tests/test_season_episodes_section.py backend/tests/test_unified_card_template.py backend/tests/test_trailer_url.py
26 passed, 1 warning in 0.53s

npm --prefix website run lint
Done in 2.85s (0 errors, 0 new warnings)

GET http://localhost:3000/series/1008 -> HTTP 200 OK
```

## Risks and unknowns
- Scaling YouTube iframes pushes standard controls offscreen, perfectly suiting ambient/preview looping playback.
- If a user opens the modal player via the action bar, `TrailerModal` retains full standard interactive controls.

## Concept to explain to the user
- Iframe Over-Scanning: YouTube o'zining kanali logotipi va nomini video tepasida ko'rsatishini oldini olish uchun video konteyneri kartochka chegarasidan 140%-300% kattalashtirilib, ortiqcha logotiplar ko'rinmas qismga chiqarib yuborildi.

## Next step
- Present status and results to the user.
