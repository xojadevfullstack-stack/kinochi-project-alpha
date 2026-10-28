# Slice Report: 2026-10-28-f1-s13-itv-horizontal-filter-bar

## What was done
1. iTV referencedagi kabi to'liq gorizontal filtr paneli (`website/components/catalog/UnifiedFilterBar.tsx`) ishlab chiqildi.
2. 1-qator: 6 ta zamonaviy iTV dropdown menyusi joylashtirildi (`Janr`, `Mamlakat`, `Reyting bo'yicha saralash`, `Yil`, `Audiotrek`, `Subtitr`).
3. 2-qator: 3 ta interaktiv tezkor toggle chiplari (`+ Bepul`, `+ O'zbek tilida`, `+ Men uchun mavjud`) va barcha filtrlarni bir marta bosishda tozalovchi `✕ Filtrlarni tozalash` tugmasi joylashtirildi.
4. Yangi filtrlash opsiyalari `website/lib/filterConstants.ts` ga qo'shildi (`DEFAULT_COUNTRIES`, `DEFAULT_SORT_OPTIONS`, `DEFAULT_AUDIOTRACKS`, `DEFAULT_SUBTITLES`).
5. TDD testi `test_itv_filter_bar.py` yozildi va muvaffaqiyatli o'tkazildi (1 passed).

## Changed files
- `website/components/catalog/UnifiedFilterBar.tsx` - Replaced bulky accordion with sleek iTV 2-row horizontal filter bar
- `website/lib/filterConstants.ts` - Added country, sort, audio, and subtitle option arrays
- `backend/tests/test_itv_filter_bar.py` - TDD regression test asserting iTV dropdowns, action pills, and clear action

## check output
```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
collected 1 item

backend\tests\test_itv_filter_bar.py .                                   [100%]
======================== 1 passed, 1 warning in 0.12s =========================
```

## Risks and unknowns
- Kichik ekranli mobil telefonlarda gorizontal dropdownlar 2 ustunli ixcham gridga moslashadi va ekran chegarasidan chiqib ketmaydi.

## Concept to explain to the user
- **Micro-Interactions (Mikro-interaksiyalar):** Og'ir akkordeon menyular o'rniga, foydalanuvchiga kerakli parametrlarni (Janr, Mamlakat, Saralash) bir zumda gorizontal qatorda ko'rsatish va bitta bosish bilan filtrlash. Xuddi avtomobil asboblar panelidagi tugmalar kabi — hammasi qo'l ostida va ko'z oldida turadi.

## Next step
- Present verification evidence and mentor summary to user.
