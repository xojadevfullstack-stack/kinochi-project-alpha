# Slice Report: 2026-10-28-f1-s19-cast-crew-drag-and-tmdb-bridge

## What was done
1. `CastCrewSection.tsx` komponentiga desktop foydalanuvchilari uchun chap/o'ng slayd tugmalari (`<` va `>`) hamda sichqoncha orqali sudrab harakatlantirish (mouse drag-to-scroll) imkoniyati qo'shildi.
2. TMDb API orqali ko'prik hosil qilinib, nafaqat aktyorlar, balki ijodiy guruhning asosiy a'zolari (Rejissyor, Muallif, Produser, Operator, Bastakor) oldingi o'rinlarga chiqarildi.
3. Film va serialning barcha qo'shimcha parametrlari (Asl nomi, Ishlab chiqarilgan mamlakat, Studiya, Premyera sanasi, Davomiyligi, Holati, Byudjet, Daromad) chaqirilib, Suratga olish guruhi bilan bitta yagona dizayndagi zamonaviy konteynerga jamlandi.
4. TDD test paketi `test_cast_crew_slider_and_tmdb_bridge.py` yaratilib, to'liq yashil holatga keltirildi.

## Changed files
- `backend/app/infrastructure/external/tmdb_client.py` - Added `get_credits_and_details` with crew prioritization and production details extraction.
- `backend/app/api/v1/movies.py` & `series.py` - Updated `/credits` endpoints to return `{items, details}`.
- `website/components/media/CastCrewSection.tsx` - Added slider controls, mouse drag, and unified TMDb details section.
- `backend/tests/test_cast_crew_slider_and_tmdb_bridge.py` - TDD test suite (3 passing tests).

## check output
```text
backend\tests\test_cast_crew_slider_and_tmdb_bridge.py ...               [100%]
======================== 3 passed, 1 warning in 2.44s =========================
```

## Risks and unknowns
- Agar TMDb API dan ayrim ma'lumotlar (masalan byudjet yoki daromad) mavjud bo'lmasa, tegishli katakchalar interfeysni buzmasdan yashiriladi.

## Concept to explain to the user
- **Mouse Drag-to-Scroll & Unified Card Layout (Sudrab surish va yagona konteyner):** Desktopda foydalanuvchilar trekpad kabi gorizontal sura olmasligi sababli sichqoncha bilan bosib tortish (drag) va tugmalar qo'shiladi; ma'lumotlar bitta divga jamlanganda esa sahifaning vizual yaxlitligi ta'minlanadi.

## Next step
- Foydalanuvchiga natijani taqdim etish va ko'rib chiqishga taklif qilish.
