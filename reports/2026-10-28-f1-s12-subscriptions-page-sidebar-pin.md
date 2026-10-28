# Slice Report: 2026-10-28-f1-s12-subscriptions-page-sidebar-pin

## What was done
1. Mustaqil va to'liq VIP obunalar sahifasi (`website/app/subscriptions/page.tsx`) yaratildi (profilga redirect olib tashlandi, 3 ta VIP tarif kartasi, afzalliklar ro'yxati, Telegram bot aktivatsiya integratsiyasi qo'shildi).
2. `BottomNav.tsx` va `Navbar.tsx` dagi "Obunalar" havolalari mustaqil `/subscriptions` ga ulandi (mobil pastki menyuda Obunalar va Profil bir xil sahifani ochish xatosi butunlay tuzatildi).
3. Desktop sidebarni pin qilib F5 yangilanganda sidebar yo'qolib ketishi va 18rem qora bo'shliq qolish xatosi bartaraf etildi (`isInitializedRef` qo'shildi, localStorage tozalanishdan himoyalandi, `<aside>` da `(sidebarOpen || isPinned)` tekshiruvi joriy qilindi).

## Changed files
- `website/app/subscriptions/page.tsx` - Standalone VIP tariff and subscription plans page with Telegram bot deep-links
- `website/components/BottomNav.tsx` - Routed Obunalar tab to `/subscriptions`, eliminated redundant query param tab state
- `website/components/Navbar.tsx` - Guarded sidebar pin state from localStorage wipe on mount, checked `(sidebarOpen || isPinned)`, updated link to `/subscriptions`
- `backend/tests/test_subscriptions_page_and_sidebar_pin.py` - TDD regression test for standalone page, separate routing, and pin persistence (3 passed)

## check output
```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
collected 3 items

backend\tests\test_subscriptions_page_and_sidebar_pin.py ...             [100%]
======================== 3 passed, 1 warning in 0.13s =========================
```

## Risks and unknowns
- Foydalanuvchi Telegram bot orqali VIP sotib olganda veb sessiya bilan avtomatik sinxronlanishi uchun bot `/start sub_<plan>` orqali webhook bilan akkaunt holatini yangilaydi.

## Concept to explain to the user
- **Hydration State Guard (Saqlangan holat himoyasi):** Sahifa F5 bilan yangilanganda, React komponenti hali xotirani (localStorage) o'qib ulgurmasdan turib boshlang'ich `false` qiymatni saqlashga urinmasligi kerak. Xuddi xonaga kiriboq chiroqni o'chirishdan oldin, ichkarida kimdir bormi-yo'qligini tekshirish (`isInitializedRef`) kabi.

## Next step
- Execute Slice F1-S13 (iTV Horizontal Filter Bar in UnifiedFilterBar.tsx).
