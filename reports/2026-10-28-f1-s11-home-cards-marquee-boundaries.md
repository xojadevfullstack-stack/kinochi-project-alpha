# Slice Report: 2026-10-28-f1-s11-home-cards-marquee-boundaries

## What was done
1. Bosh sahifadagi (`website/app/page.tsx`) barcha eski inline kartochkalar yangi iTV/Kinopoisk split-dizayndagi `MovieCard` komponentiga almashtirildi va ortiqcha 125 qator JSX olib tashlandi.
2. `MediaMarqueeSection.tsx` animatsion mozaika sektsiyasi `max-w-full` o'rniga `max-w-container-max mx-auto px-gutter` chegarasiga moslandi, ultra-keng monitorlarda umumiy grid chegarasidan chiqib ketishi bartaraf etildi.
3. TDD testi `test_home_cards_and_marquee_boundaries.py` yozildi va muvaffaqiyatli o'tkazildi (2 passed).

## Changed files
- `website/app/page.tsx` - Replaced legacy inline cards in `MovieRow` and `unifiedRecentItems` with `<MovieCard />`
- `website/components/home/MediaMarqueeSection.tsx` - Constrained section width to `max-w-container-max mx-auto px-gutter`
- `backend/tests/test_home_cards_and_marquee_boundaries.py` - TDD regression test for card component reuse and container boundary constraints

## check output
```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
collected 2 items

backend\tests\test_home_cards_and_marquee_boundaries.py ..               [100%]
======================== 2 passed, 1 warning in 0.13s =========================
```

## Risks and unknowns
- Katta ekranlarda `MovieCard` hover drawerlari silliq ochilishi CSS transform va z-index orqali ta'minlangan, horizontal scroll paytida clipping bo'lmasligi uchun `pt-2 pb-6` padding saqlangan.

## Concept to explain to the user
- **DRY (Don't Repeat Yourself) va Yagona Manba:** Bosh sahifada kartochkalar qaytadan alohida JSX qilib yozilgandi, katalogda esa alohida edi. Biz ularni bitta `MovieCard` ga birlashtirdik. Xuddi bir xil pasport blankasi barcha bo'limlarda bir xil chop etilgani kabi, endi saytning hamma joyida kartochkalar bir xil zamonaviy formatda chiqadi.

## Next step
- Execute Slice F1-S12 (Dedicated Subscriptions Page & Sidebar Pin Persistence Fix).
