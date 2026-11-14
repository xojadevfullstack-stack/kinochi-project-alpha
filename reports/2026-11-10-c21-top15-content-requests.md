# Slice Report: 2026-11-10-c21-top15-content-requests

## What was done
1. Seeded user-requested TOP-15 recommendations into `content_requests` table with enriched TMDb metadata and initial vote distribution.
2. Implemented responsive category filter pills (Barchasi, Anime, Dorama, Kino, Serial, Multfilm) and category badges in website `/requests` page with strict Cinematic Red styling.
3. Corrected misaligned TMDb IDs for True Beauty (112888) and Queen of Tears (215720) with cross-reference logging.

## Changed files
- `website/app/requests/page.tsx` - Added category tabs, filter logic, category badge, and sanitized amber badge to neutral.
- `scratch/seed_top15.py` - Seed utility script executing idempotent upsert for TOP-15 catalog requests.

## check output
```text
next lint:
✔ No ESLint warnings or errors in changed files (website/app/requests/page.tsx clean)

pytest:
======================== 9 passed, 4 warnings in 7.34s ========================
```

## Risks and unknowns
- TMDb poster URLs rely on image.tmdb.org availability in client browser.
- Cached content requests list in Redis (`cache:tmdb:*`) may need up to 2 minutes to refresh on existing edge proxies.

## Concept to explain to the user
- **Database Seeding (Baza urug'lash):** Yangi sahifa yoki funksiya ochilganda foydalanuvchiga bo'sh quti ko'rinmasligi uchun unga boshlang'ich saralangan ma'lumotlarni oldindan kiritib qo'yish (xuddi yangi ochilgan do'konga xaridor kelguncha peshtaxtalarga namunaviy tovarlarni terib qo'yish kabi).

## Next step
- Foydalanuvchi bilan yangi ro'yxatni ko'rib chiqish va bot inline qidiruviga integratsiyani tekshirish.
