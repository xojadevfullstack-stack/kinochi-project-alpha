# Slice Report: 2026-10-28-f1-s17-unified-card-template

## What was done
1. Barcha joylarda (Davom ettirish, Asosiy sahifa, Katalog) kartochka dizayni va ma'lumotlar formati yagona `MovieCard` shabloniga keltirildi: yagona standart `[IMDb] {rating}` ko'rsatkichi, `{yil} • {janr}` tavsifi va hover animatsiyasi.
2. `ContinueWatchingSection.tsx` ichida eski va yangi saqlangan elementlar uchun avtomatik ma'lumot boyitish (auto-enrichment) qo'shildi — Chernobildan boshlab barcha serial/kinolar o'z yili, janri va reytingi bilan bir xil ko'rinadi.
3. `TelegramWatchButton.tsx` orqali ko'rish boshlanganda barcha kerakli parametrlar (`releaseYear`, `imdbRating`, `genres`) saqlanadigan qilindi va 3 ta yangi TDD regressiya testi yozildi.

## Changed files
- `website/components/catalog/MovieCard.tsx` - Standardized unified IMDb rating presentation across all cards.
- `website/components/home/ContinueWatchingSection.tsx` - Added auto-enrichment effect to populate missing year, genre, rating for legacy items.
- `website/components/TelegramWatchButton.tsx` - Persisted releaseYear, imdbRating, and genres to localStorage.
- `website/app/movie/[code]/page.tsx` - Passed card metadata to watch button.
- `website/app/series/[id]/page.tsx` - Passed card metadata to watch buttons for both main and episode lists.
- `backend/tests/test_unified_card_template.py` - TDD regression test suite for unified card template (3 passing tests).

## check output
```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Администратор\Desktop\kino bot project\kinochi project\backend
configfile: pyproject.toml
collected 3 items

backend\tests\test_unified_card_template.py ...                          [100%]
======================== 3 passed, 1 warning in 0.13s =========================
```

## Risks and unknowns
- Agar internet juda sekin bo'lsa yoki backend server javob bermasa, Continue Watching kartochkasi avval faqat nomi bilan chiqadi va ma'lumot yuklanishi bilan to'liq parametrlar paydo bo'ladi (graceful degradation).

## Concept to explain to the user
- **Single Source of Truth (Yagona haqiqat manbasi):** Bir xil ma'lumotni 3 xil joyda 3 xil alohida kartochka qilib chizmasdan, hamma joyda bitta yagona `MovieCard` komponentidan foydalanish. Bu barcha sahifalarda dizayn va parametrlarning 100% bir xilligini ta'minlaydi.

## Next step
- Foydalanuvchiga natijani taqdim etish va yangi talablar bo'yicha yo'l-yo'riq olish.
