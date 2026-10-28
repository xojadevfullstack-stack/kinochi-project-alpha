# Slice Report: 2026-10-28-hero-inactivity-cinema-mode

## What was done
1. Upgraded `HeroTrailerBackdrop.tsx` into a full Hero controller accepting `children`, with a smart 4.5s idle inactivity timer that auto-transitions the hero into unblurred, full-clarity "Kinoteatr Rejimi" (Cinema Mode).
2. Implemented seamless interaction wake-up: moving the mouse, touching the screen, or hovering over content instantly restores all foreground details (poster, title, synopsis, CTA buttons) and protective gradients.
3. Added accessible cinema mode controls: a floating bar with movie title, "Ma'lumotlarni ko'rsatish" button, sound toggle (`volume_up` / `volume_off`), and manual "Treylerni ko'rish" trigger in normal mode.
4. Wrapped hero content in `website/app/series/[id]/page.tsx` and `website/app/movie/[code]/page.tsx` inside `<HeroTrailerBackdrop>...</HeroTrailerBackdrop>`, verified with TDD test suite (`test_hero_trailer_cinema_mode.py`, 2 passed).

## Changed files
- `website/components/media/HeroTrailerBackdrop.tsx` - Enhanced with inactivity timer, cinema mode state, user activity listeners, gradient fading, and cinema mode controls.
- `website/app/series/[id]/page.tsx` - Wrapped hero content container inside `HeroTrailerBackdrop`.
- `website/app/movie/[code]/page.tsx` - Wrapped hero content container inside `HeroTrailerBackdrop`.
- `backend/tests/test_hero_trailer_cinema_mode.py` - TDD regression tests asserting cinema mode capabilities and content wrapping.
- `docs/learned.md` - Added "Smart Idle Inactivity Transition & Cinema Mode" concept.

## check output
```text
pytest backend/tests/test_hero_trailer_backdrop.py backend/tests/test_hero_trailer_cinema_mode.py backend/tests/test_fix_sidebar_and_hydration_bugs.py backend/tests/test_season_episodes_section.py backend/tests/test_movie_card_itv_redesign.py backend/tests/test_unified_card_template.py backend/tests/test_continue_watching_v2_and_hero_mobile.py backend/tests/test_trailer_url.py
25 passed, 1 warning in 0.54s

npm --prefix website run lint
Done in 2.85s (0 errors, 0 new warnings)

GET http://localhost:3000/series/1008 -> HTTP 200 OK
```

## Risks and unknowns
- On mobile devices where hover is absent, any tap on the cinema mode backdrop acts as an immediate wake-up signal returning full details.
- Audio autoplay policy remains strictly respected: videos start muted, sound toggles cleanly via user gesture.

## Concept to explain to the user
- Smart Idle Inactivity Transition & Cinema Mode: Foydalanuvchi ma'lumotlarni o'qib bo'lgach (4.5 soniya harakatsizlikda), matnlar xira bo'lib yo'qoladi va treyler 100% tiniq bo'lib ochiladi. Sichqoncha qimirlashi yoki ekranga teginish bilan barcha ma'lumotlar bir zumda yana joyiga qaytadi.

## Next step
- Present status and results to the user.
