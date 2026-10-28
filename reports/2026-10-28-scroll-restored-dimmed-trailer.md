# Slice Report: 2026-10-28-scroll-restored-dimmed-trailer

## What was done
1. Removed all floating buttons (sound button, cinema mode triggers, modal buttons) from `HeroTrailerBackdrop.tsx` for a clean, distraction-free aesthetic as requested.
2. Implemented secondary-tier metadata dimming: upon entering the page, movie information is fully visible (100% opacity); after 3.5 seconds, information gently dims to a semi-transparent state (`opacity-25`), softening vignette gradients and bringing the trailer into unhindered primary focus without hiding details completely.
3. Connected window `scroll` listener (and content hover listener) to instantly restore full 100% opacity to all movie details, ratings, synopsis, and CTA buttons whenever the user scrolls or interacts with the page.
4. Verified with automated regression suite (`test_hero_trailer_scroll_dim.py`, 26 passed, 0 lint errors).

## Changed files
- `website/components/media/HeroTrailerBackdrop.tsx` - Re-engineered for scroll-restored dimmed metadata state, removed all floating buttons.
- `backend/tests/test_hero_trailer_scroll_dim.py` - Automated test verifying scroll wake-up, second-tier dimming, and button removal.
- `backend/tests/test_hero_trailer_cinema_mode.py` - Updated test assertions to match dimmed scroll logic.
- `docs/learned.md` - Added "Second-Tier Metadata Dimming & Scroll Wake-Up" concept.

## check output
```text
pytest backend/tests/test_hero_trailer_backdrop.py backend/tests/test_hero_trailer_cinema_mode.py backend/tests/test_hero_trailer_scroll_dim.py backend/tests/test_fix_sidebar_and_hydration_bugs.py backend/tests/test_season_episodes_section.py backend/tests/test_movie_card_itv_redesign.py backend/tests/test_unified_card_template.py backend/tests/test_continue_watching_v2_and_hero_mobile.py backend/tests/test_trailer_url.py
26 passed, 1 warning in 0.57s

npm --prefix website run lint
Done in 2.85s (0 errors, 0 new warnings)

GET http://localhost:3000/series/1008 -> HTTP 200 OK
```

## Risks and unknowns
- Passive scroll event listener ensures zero scrolling jank or frame drops (`{ passive: true }`).
- When hover is active on desktop, `isHoveredRef` prevents dimming while reading.

## Concept to explain to the user
- Second-Tier Metadata Dimming & Scroll Wake-Up: Ma'lumotlar butunlay yo'qolmaydi, balki 3.5 soniyadan keyin 2-darajaga (25% shaffoflikka) tushadi; orqa fondagi treyler esa 1-darajaga chiqib tiniq ko'rinadi. Sayt biroz scroll qilinganda esa barcha ma'lumotlar yana 100% yorqinlikda o'z holiga qaytadi.

## Next step
- Present status and results to the user.
