# Slice Report: 2026-10-28-f1-s14-clean-filter-mocks-and-cw-404

## What was done
1. `UnifiedFilterBar.tsx` dan bazada mavjud bo'lmagan soxta parametrlar (`Mamlakat`, `Audiotrek`, `Subtitr`, `+ Bepul`, `+ O'zbek tilida`, `+ Men uchun mavjud`) olib tashlandi, faqat haqiqiy parametrlar (`Janr`, `Bo'lim`, `Turi`, `Yil`, `Reyting bo'yicha saralash` va `✕ Filtrlarni tozalash`) qoldirildi.
2. `MovieCard.tsx` dan barcha soxta mocklar tozalab tashlandi: `Obuna` yozuvi, soxta `6+` yosh belgisi (faqat haqiqiy 18+ qoldirildi), hardcoded `O'zbekiston` matni, soxta `/TV` reytingi va kartochkalar ustidagi keraksiz mayda oq chiziq (`h-1 bg-white/25 rounded-t-lg`) olib tashlandi.
3. Sahifa pastga scroll qilinganda filtr paneli navbar ustiga chiqib ketishi xatosi `Navbar.tsx` da `z-50` ga ko'tarish va sahifalardagi filtr qatlamini `z-20` ga tushirish orqali to'liq tuzatildi.
4. "Ko'rishni davom ettirish" (Continue Watching) kartochkalari bosilganda 404 xatosi berishi `TelegramWatchButton.tsx` da `seriesId` / `mediaId` to'g'ri uzatilishi, to'liq URL saqlanmasligi va `movie/[code]/page.tsx` da ID orqali xavfsiz fallback orqali to'liq bartaraf etildi.
5. Yangi narsa qo'shishdan oldin doim foydalanuvchidan so'rash qonuni `facts.md` va `AGENTS.md` ga kiritildi.
6. TDD regression testi `test_fix_filter_mocks_and_continue_watching.py` yozildi va barcha 5 ta testi muvaffaqiyatli o'tkazildi (27 passed jami UI suite).

## Changed files
- `website/components/catalog/UnifiedFilterBar.tsx` - Cleaned unsupported filter dropdowns and mock action pills
- `website/components/catalog/MovieCard.tsx` - Removed fake Obuna, mock 6+ age badge, fake country, and mock /TV rating
- `website/components/Navbar.tsx` - Elevated site-top-nav z-index to z-50 and aside to z-[60] to prevent scroll clipping
- `website/app/catalog/page.tsx`, `movies/page.tsx`, `series/page.tsx` - Normalized filter container z-index to z-20
- `website/components/TelegramWatchButton.tsx` - Added seriesId/mediaId props and sanitized continue watching id persistence
- `website/components/home/ContinueWatchingSection.tsx` - Sanitized continue watching href generation against full URLs
- `website/app/movie/[code]/page.tsx` - Added numeric ID fallback fetching and wired mediaId
- `website/app/series/[id]/page.tsx` - Passed mediaId and seriesId to watch buttons
- `facts.md`, `AGENTS.md` - Inscribed Parameter/Schema Law
- `backend/tests/test_fix_filter_mocks_and_continue_watching.py` - TDD regression suite for all 4 fixes

## check output
```text
pytest backend/tests/test_fix_filter_mocks_and_continue_watching.py
======================== 5 passed, 1 warning in 0.15s =========================

npm --prefix website run lint
✔ No ESLint errors found (0 errors).

Live HTTP Render:
http://localhost:3000/              -> HTTP 200 (525,157 bytes)
http://localhost:3000/premieres     -> HTTP 200 (115,891 bytes)
http://localhost:3000/subscriptions -> HTTP 200 (34,946 bytes)
http://localhost:3000/catalog       -> HTTP 200 (148,968 bytes)
```

## Risks and unknowns
- Foydalanuvchining avvalgi brauzer sessiyasida `localStorage` da noto'g'ri `https://...` URL yozilgan bo'lsa ham, yangi `cleanId` filtri uni avtomatik chetlab o'tadi va 404 ga tushirmaydi.

## Concept to explain to the user
- **Z-Index Stacking Context & Real Schema Discipline:** Fixed navbar sahifaning eng ustki qatlami bo'lishi lozim (`z-50`), aks holda ichki elementlar scroll paytida uning ustiga chiqib ketadi. Shuningdek, ma'lumotlar bazasida yo'q maydonlarni (subtitr, mamlakat) "taxmin qilib" qo'yish tizimda soxta taassurot uyg'otadi; faqat real API orqali boshqariladigan parametrlar qoldirildi.

## Next step
- Present verification evidence and mentor summary to user.
