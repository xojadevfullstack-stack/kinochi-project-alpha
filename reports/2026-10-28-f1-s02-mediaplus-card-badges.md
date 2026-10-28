# Slice Report: 2026-10-28-f1-s02-mediaplus-card-badges

## What was done
1. Eliminated deceptive hardcoded `"8.5"` rating mock fallback from home page cards in `website/app/page.tsx`, switching to authentic rating or `"N/A"`.
2. Added visual `#CODE` badges (`#{item.code}` or `SERIAL`) across home page carousels (`MovieRow`), recent releases slider (`unifiedRecentItems`), and catalog cards (`MovieCard.tsx`) to bridge web browsing and Telegram bot search.
3. Created automated TDD test `backend/tests/test_website_mediaplus_ui.py` confirming zero hardcoded rating mocks and verified presence of `#CODE` badges.

## Changed files
- `website/app/page.tsx` - Removed `"8.5"` mock fallback and added top-left `#CODE` badges to carousels.
- `website/components/catalog/MovieCard.tsx` - Added `#CODE` badge to catalog grid cards.
- `backend/tests/test_website_mediaplus_ui.py` - TDD regression tests asserting badge and mock-free state.

## check output
```text
backend/tests/test_website_mediaplus_ui.py ..                            [100%]
2 passed in 0.13s

Website Next.js Lint:
Checked all files, exit code 0.

Pytest Bot Suite:
75 passed in 5.70s
```

## Risks and unknowns
- Movies without both `code` and `is_series` flags will display neither `#CODE` nor `SERIAL` badge, gracefully falling back without UI breaks.

## Concept to explain to the user
- Direct Identifiers (To'g'ridan-to'g'ri identifikatorlar): Foydalanuvchiga murakkab qidiruv o'rniga, har bir mahsulotga aniq artikul yoki raqam berish.

## Next step
- Implement quality selector buttons (`480p`, `720p`, `1080p`) when `/start {code}` is invoked in Telegram bot (`MASTER_ROADMAP_MEDIAPLUS_V2.md` Sprint 2).
