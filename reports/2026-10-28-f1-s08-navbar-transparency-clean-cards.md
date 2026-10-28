# Slice Report: 2026-10-28-f1-s08-navbar-transparency-clean-cards

## What was done
1. Upgraded `Navbar.tsx` styling to modern translucent glassmorphism (`bg-black/20 backdrop-blur-md` and `bg-black/60 backdrop-blur-xl` on scroll) letting media heroes shine through.
2. Removed `#CODE` and `SERIAL` badges from all movie and series cards across `MovieCard.tsx`, `page.tsx`, `ContinueWatchingSection.tsx`, and `MediaMarqueeSection.tsx`.
3. Created TDD test suite `backend/tests/test_navbar_transparency_and_clean_cards.py` (asserted RED, then GREEN).

## Changed files
- `website/components/Navbar.tsx` - Replaced solid obsidian header background with translucent glassmorphic blur
- `website/components/catalog/MovieCard.tsx` - Removed code and serial badges from poster container
- `website/app/page.tsx` - Removed code and serial overlays from home page sliders
- `website/components/home/ContinueWatchingSection.tsx` - Removed code and serial badges
- `website/components/home/MediaMarqueeSection.tsx` - Removed code badge
- `backend/tests/test_navbar_transparency_and_clean_cards.py` - TDD regression tests

## check output
```text
backend\tests\test_navbar_transparency_and_clean_cards.py ..             [100%]
npm --prefix website run lint: 0 errors (exit code 0)
Live render check: HTTP 200 OK
```

## Risks and unknowns
- Without `#CODE` on the card surface, users looking for the exact code for the Telegram bot can still find it inside the movie details page (`/movie/[code]`) or in search results.

## Concept to explain to the user
- Glassmorphic Translucency & Poster Minimalism: Kartochkalarni keraksiz matnli nishonlardan xoli qilib, rasmni toza ko'rsatish va navbarni orqadagi rasm bilan uyg'unlashtirish.

## Next step
- Implement iTV-style horizontal filter bar (`UnifiedFilterBar.tsx`).
