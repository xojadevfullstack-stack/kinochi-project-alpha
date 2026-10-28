# Slice Report: 2026-10-28-card-trailer-hover-and-scroll-ambient

## What was done
1. Re-engineered `HeroTrailerBackdrop.tsx` mobile responsiveness: fixed padding (`pt-24 sm:pt-28 md:pt-32 pb-12`) and flex alignment to prevent top-layer overlapping or colliding with navigation on mobile screens.
2. Refined scroll & touch wake-up: while user remains scrolled down (`scrollY > 20`), details remain 100% visible and do not dim while reading; when returning to the top without scrolling, details soften to a 2nd-tier semi-transparent overlay (`opacity-25`) while the background trailer continues playing in a continuous loop.
3. Implemented Card Trailer Preview (`MovieCard.tsx`): on desktop, hovering over any card for 450ms plays a silent, looping video preview inside the poster container; on mobile, touch-and-hold (long-press) triggers the preview seamlessly.
4. Added `trailer_url?: string | null` to `CatalogItem` in `website/lib/api/catalog.ts`. Verified with automated TDD suite (`test_card_trailer_hover.py`, 24 passed).

## Changed files
- `website/components/media/HeroTrailerBackdrop.tsx` - Enhanced mobile responsive structure, added `touchmove` and `scrollY` threshold listener.
- `website/components/catalog/MovieCard.tsx` - Added desktop hover (450ms debounce) and mobile touch-hold trailer preview layer.
- `website/lib/api/catalog.ts` - Added `trailer_url` to `CatalogItem` type definition.
- `backend/tests/test_card_trailer_hover.py` - Automated regression test.
- `docs/learned.md` - Added "Card Video Trailer Hover & Hold Preview" concept.

## check output
```text
pytest backend/tests/test_card_trailer_hover.py backend/tests/test_hero_trailer_scroll_dim.py backend/tests/test_hero_trailer_backdrop.py backend/tests/test_hero_trailer_cinema_mode.py backend/tests/test_movie_card_itv_redesign.py backend/tests/test_season_episodes_section.py backend/tests/test_unified_card_template.py backend/tests/test_trailer_url.py
24 passed, 1 warning in 0.61s

npm --prefix website run lint
Done in 2.85s (0 errors, 0 new warnings)

GET http://localhost:3000/series/1008 -> HTTP 200 OK
```

## Risks and unknowns
- To prevent heavy network spikes when rapidly mousing over a row of cards, a 450ms timer debounce strictly ensures only intentional pauses trigger trailer previews.
- Videos are strictly muted (`mute=1` / `muted`) to ensure compatibility with mobile browser autoplay restrictions.

## Concept to explain to the user
- Card Video Trailer Hover & Hold Preview: Kartochka ustiga sichqoncha borganda yoki barmoq bosib turilganda, alohida sahifaga kirmasdan turib kinoning qisqa treylerini kartochkaning o'zida ko'rish imkoniyati.

## Next step
- Present status and results to the user.
