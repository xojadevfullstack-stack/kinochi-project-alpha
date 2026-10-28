# Slice Report: 2026-10-28-f1-s03-navbar-clean

## What was done
1. Cleaned up desktop and drawer navigation menu in `website/components/Navbar.tsx`, removing 21 bloated, dead, and duplicate links (such as `/catalog?category=treyler`, `/tv`, and duplicated genres inside collections).
2. Replaced the nested accordion dropdowns with an elegant, streamlined 8-item primary navigation list (Bosh sahifa, Katalog, Seriallar, Franshizalar & To'plamlar, Premyeralar, Aktyorlar, Obunalar, Kino buyurtma qilish).
3. Created automated TDD test `backend/tests/test_navbar_clean.py` asserting zero dead links and verifying all primary routes.

## Changed files
- `website/components/Navbar.tsx` - Removed dead accordion menus, cleaned state, and streamlined primary links.
- `backend/tests/test_navbar_clean.py` - TDD regression test asserting clean navbar state.

## check output
```text
backend/tests/test_navbar_clean.py .                                     [100%]
1 passed in 0.13s

Combined UI test suite:
3 passed in 0.16s

Next.js Website Lint:
Checked all files, exit code 0.
```

## Risks and unknowns
- Users who previously relied on direct sidebar clicks for niche categories (e.g. Hind kinolari) will now find them cleanly categorized inside the `/catalog` filter bar.

## Concept to explain to the user
- Information Architecture (IA) va Kognitiv yengillik (Hick's Law): Foydalanuvchiga 30 ta chalkash variant o'rniga, 7-8 ta aniq, ishlaydigan yo'nalish berish.

## Next step
- Implement distinct visual styling for movie detail pages: "Franshizaning boshqa qismlari (Xronologiya)" vs "Shu to'plamdagi boshqa filmlar" (`FranchisePartsSection.tsx`).
