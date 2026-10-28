# Slice Report: 2026-10-28-cinematic-red-design-standard

## What was done
1. Enforced the Cinematic Red Design Standard (`#E50914` / Primary Red) across the entire platform, eliminating all yellow/amber misuses on buttons, hover states, card titles, borders, and active tabs.
2. Inscribed strict Anti-Pattern laws in `design.md`, `AGENTS.md`, `facts.md`, and `docs/failures.md` restricting `rating-gold` strictly to IMDb/Kinopoisk ratings.
3. Added automated regression assertions in `test_season_episodes_section.py` and `test_movie_card_itv_redesign.py`, verified GREEN with zero lint errors.

## Changed files
- `design.md` - Added section 1.1 with explicit Anti-Pattern laws forbidding yellow on CTA, hover, active tabs, and titles.
- `AGENTS.md` - Inscribed Cinematic Red Design Standard Law under Core Rules.
- `facts.md` - Inscribed Cinematic Red Design Standard invariant.
- `website/components/media/SeasonEpisodesSection.tsx` - Converted active season tab to Primary Red (`bg-primary`), episode hover to red border/icon/number, and section indicator to red bar.
- `website/components/catalog/MovieCard.tsx` - Replaced `group-hover:text-rating-gold` with `group-hover:text-primary` to fix title turning yellow on hover (e.g., "Kalmar O'yini").
- `website/components/home/MediaMarqueeSection.tsx` - Replaced yellow hover and section indicator with Primary Red.
- `website/components/media/CastCrewSection.tsx` - Converted actor photo hover border and name hover text to Primary Red.
- `website/components/LiveSearch.tsx` - Changed request link hover to Primary Red.
- `website/components/SearchClientView.tsx` - Replaced yellow CTA buttons, search focus ring, and spinner with Primary Red.
- `website/components/RequestMovieModal.tsx` - Replaced yellow submit buttons and active pills with Primary Red.
- `website/components/CollectionTimelineView.tsx` - Converted amber timeline badges and active cards to Primary Red.
- `website/components/ExternalSearchSection.tsx` - Replaced yellow request buttons with Primary Red.
- `website/app/subscriptions/page.tsx` - Replaced series tab yellow borders and hover with Primary Red.
- `website/app/actors/page.tsx` - Replaced actor card yellow hover and filmography order buttons with Primary Red.
- `website/app/requests/page.tsx` - Replaced yellow tabs, submit buttons, and search focus ring with Primary Red.
- `website/app/page.tsx` - Converted section header indicator bars to Primary Red.
- `backend/tests/test_season_episodes_section.py` - Added assertions ensuring active season tab and episode hover use Primary Red, never yellow.
- `backend/tests/test_movie_card_itv_redesign.py` - Added assertion ensuring MovieCard title hover does not use rating-gold.
- `docs/failures.md` - Logged Failure 005 (Color Palette Bleed & Rating Gold Misuse).
- `STATE.md` - Updated project state with slice F1-S25.

## check output
```text
> website@0.1.0 lint
> next lint
Done in 2.6s (0 errors, clean)

backend\.venv\Scripts\python.exe -m pytest backend/tests/test_season_episodes_section.py backend/tests/test_movie_card_itv_redesign.py
======================== 5 passed, 1 warning in 0.19s =========================
```

## Risks and unknowns
- Low risk: Only CSS styling classes were modified to adhere to the master design specification. Component structure and event handlers remain completely untouched.

## Concept to explain to the user
- **Dizayn Tokenlari va Vizual Qat'iyatlik (Design Tokens & Invariants):** Katta media tizimlarda bitta rang (masalan, reyting sariq rangi) boshqa joylarga (tugmalarga yoki hoverga) tarqalib ketmasligi uchun "Anti-pattern" qonuni qat'iy kodlashtiriladi va avtotestlar orqali himoyalanadi.

## Next step
- Receive user feedback on the updated visuals.
