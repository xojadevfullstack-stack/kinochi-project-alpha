# Slice Report: 2026-10-28-f1-s06-moviecard-split-redesign

## What was done
1. Redesigned `MovieCard.tsx` following modern iTV / Kinopoisk split-card ergonomics: separated the poster container (`rounded-2xl`) from the textual labels underneath.
2. Positioned media title and green `Obuna` status cleanly below the poster image.
3. Implemented progressive disclosure hover drawer revealing metadata (`Year, Country, Genre`) and multi-rating metrics (`IMDb`, `K` for TMDB/Kinopoisk, and `/TV` for platform score).
4. Preserved core identifiers: `#CODE` badge for Telegram bot lookup and age limit capsules (`6+`, `16+`, `18+`).
5. Created TDD test `backend/tests/test_movie_card_itv_redesign.py` (verified RED then GREEN).

## Changed files
- `website/components/catalog/MovieCard.tsx` - Complete card restructure with split layout and hover overlay
- `backend/tests/test_movie_card_itv_redesign.py` - TDD regression assertion suite

## check output
```text
backend/tests/test_movie_card_itv_redesign.py .                          [100%]
backend/tests/test_website_mediaplus_ui.py ..                            [100%]
======================== 3 passed, 1 warning in 0.22s =========================
npm --prefix website run lint: exit code 0
```

## Risks and unknowns
- Touchscreen devices do not trigger CSS hover; essential information (Title and Obuna status) is kept persistently visible beneath the poster so mobile users miss zero context.

## Concept to explain to the user
- Progressive Disclosure: Asosiy ma'lumotlarni ko'zga tashlanadigan qilib qo'yib, ikkinchi darajali batafsil ma'lumotlarni faqat sichqoncha borganda ko'rsatish orqali ekranni toza saqlash.

## Next step
- Implement iTV-style multi-row continuous infinite marquee section.
