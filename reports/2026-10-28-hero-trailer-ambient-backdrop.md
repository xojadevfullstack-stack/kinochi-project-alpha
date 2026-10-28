# Slice Report: 2026-10-28-hero-trailer-ambient-backdrop

## What was done
1. Created `HeroTrailerBackdrop.tsx` client component that renders YouTube/MP4 trailers as an ambient looping background with protective dark vignette gradients, floating sound toggle, and instant LCP poster image fallback.
2. Removed bulky standalone "Treyler" sections from both `website/app/series/[id]/page.tsx` and `website/app/movie/[code]/page.tsx` (eliminating the forbidden rating-gold heading bar and freeing valuable page space).
3. Added an ergonomic "TREYLER" modal trigger button to the primary hero action button group and verified with TDD test suite (`test_hero_trailer_backdrop.py`, 3 passed).

## Changed files
- `website/components/media/HeroTrailerBackdrop.tsx` - Ambient video background component with aspect-ratio cover, vignette gradients, and audio toggle.
- `website/components/TrailerModal.tsx` - Added `variant="button"` support for trigger buttons in hero action bars.
- `website/app/series/[id]/page.tsx` - Replaced static background with `HeroTrailerBackdrop`, added hero trailer button, deleted standalone trailer section.
- `website/app/movie/[code]/page.tsx` - Replaced static background with `HeroTrailerBackdrop`, added hero trailer button, deleted standalone trailer section.
- `backend/tests/test_hero_trailer_backdrop.py` - Automated regression test ensuring component integration and deletion of bulky standalone sections.
- `docs/learned.md` - Added "Ambient Video Backdrop & Vignette Layering" concept.
- `docs/decisions.md` - Added ADR-008.

## check output
```text
pytest backend/tests/test_hero_trailer_backdrop.py backend/tests/test_fix_sidebar_and_hydration_bugs.py backend/tests/test_season_episodes_section.py backend/tests/test_movie_card_itv_redesign.py backend/tests/test_unified_card_template.py backend/tests/test_continue_watching_v2_and_hero_mobile.py backend/tests/test_trailer_url.py
22 passed, 1 warning in 0.49s

npm --prefix website run lint
Done in 2.92s. (0 errors, 0 new warnings)

Web live check:
http://localhost:3000/series/1008 -> HTTP 200 OK
```

## Risks and unknowns
- Some aggressive adblockers or privacy extensions may block YouTube iframe scripts from running; in such cases, `HeroTrailerBackdrop` gracefully falls back to the high-resolution poster backdrop without crashing.
- Autoplay on iOS Safari strictly requires muted playback; this is guaranteed by our `mute=1` param and `muted={true}` attribute.

## Concept to explain to the user
- Ambient Video Backdrop & Vignette Layering: Kinoteatr foysida afishaning orqasidagi devorda shovqinsiz videorolik aylanib turishi kabi, asosiy afisha va yozuvlar yorqin qora vual (gradient) ustida tiniq ko'rinadi va foydalanuvchiga Netflix darajasidagi atmosferani beradi.

## Next step
- Present status and results to the user.
