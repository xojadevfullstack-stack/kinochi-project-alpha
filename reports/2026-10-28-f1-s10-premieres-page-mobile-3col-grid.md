# Slice Report: 2026-10-28-f1-s10-premieres-page-mobile-3col-grid

## What was done
1. Created dedicated `website/app/premieres/page.tsx` displaying current premiering movies and series with full filtering and search.
2. Updated `website/components/BottomNav.tsx` and `website/components/Navbar.tsx` so "Premyera" routes cleanly to `/premieres` instead of redirecting to `/movies`.
3. Adjusted mobile catalog grid in `website/components/catalog/CatalogGrid.tsx` and `HistoryGrid.tsx` from 2 columns (`grid-cols-2`) to 3 columns (`grid-cols-3 gap-2.5 sm:gap-4`) matching user reference and modern streaming standards.
4. Created TDD test suite `backend/tests/test_premieres_page_and_mobile_3_col_grid.py` (verified RED, then GREEN).

## Changed files
- `website/app/premieres/page.tsx` - Dedicated server-rendered Premieres page
- `website/components/BottomNav.tsx` - Updated Premyera route from `/movies` to `/premieres`
- `website/components/Navbar.tsx` - Updated Premyera drawer link to `/premieres`
- `website/components/catalog/CatalogGrid.tsx` - Updated mobile grid to 3 columns
- `website/components/history/HistoryGrid.tsx` - Updated mobile grid to 3 columns
- `backend/tests/test_premieres_page_and_mobile_3_col_grid.py` - TDD regression tests

## check output
```text
backend\tests\test_premieres_page_and_mobile_3_col_grid.py ...           [100%]
npm --prefix website run lint: 0 errors (exit code 0)
Live render check:
URL: http://localhost:3000/premieres -> HTTP 200
URL: http://localhost:3000/movies -> HTTP 200
All live pages verified successfully!
```

## Risks and unknowns
- In 3-column mobile grids, screen width is shared across 3 posters; gap was tuned to `gap-2.5` to ensure posters maintain optimal aspect ratio without feeling cramped.

## Concept to explain to the user
- 3-Column Mobile Catalog Density: 2 ta katta rasm o'rniga 3 ta ixcham rasm qo'yish orqali ekranga bir vaqtning o'zida ko'proq film sig'dirish va skroll qilishni kamaytirish.

## Next step
- Implement iTV-style horizontal filter bar in `UnifiedFilterBar.tsx`.
