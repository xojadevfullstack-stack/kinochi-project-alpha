# Slice Report: 2026-10-28-f1-s15-cast-crew-cw-redesign-mobile-hero

## What was done
1. **Suratga olish guruhi (Cast & Crew via TMDb):**
   - `tmdb_client.py` ga `get_credits` metodi qo'shildi (`ru-RU` va `en-US` fallback bilan, rollar: Aktyor, Rejissyor, Ssenariy muallifi, Produser).
   - `movies.py` va `series.py` ga `GET /{id_or_code}/credits` endpointlari qo'shildi va Redis orqali 24 soatga keshlandi.
   - `website/components/media/CastCrewSection.tsx` komponenti yaratildi (doiraviy avatarlar, rasm bo'lmasa oq siluet avatar ikonka, ismlar va rollar bilan gorizontal silliq karusel).
   - `movie/[code]/page.tsx` va `series/[id]/page.tsx` tafsilot sahifalariga ulandi.
2. **"Ko'rishni davom ettirish" (Continue Watching) 404 xatosi va dizayn yangilanishi:**
   - 404 sababi: Seriya kodi (`gb3SGSCj`) yoki epizod ID si (`14946`) bosilganda, backendda serial topilmay 404 qaytarayotgan edi. `series_repository.py` da epizod kodi va ID si orqali uning asosiy serialini avtomatik aniqlash (`fallback`) joriy etildi. `series/[id]/page.tsx` da ham `/series/code/{id}` fallback ulandi.
   - Kartochka uslubi yangilandi: eski qatlam olib tashlandi, markazdagi play ikonkasi va ostidagi qizil progress bar olib tashlandi, platformaning yagona zamonaviy `<MovieCard item={item} statusBadge="in_progress" />` komponentiga o'tkazildi.
3. **Hero Premiere banneridagi poster:**
   - Mobil qurilmalarda butunlay yashiringan (`hidden md:block`) poster responsiv qilindi: telefonda ixcham (`w-36 xs:w-40`), silliq `rounded-2xl` va `order-first` bo'lib, ekranni to'ldirib yubormasdan qulay o'lchamda ko'rinadi.
4. **Admin panel:**
   - Port 3001 da fon rejimida muvaffaqiyatli ishga tushirildi (`http://localhost:3001`, HTTP 200 OK).

## Changed files
- `backend/app/infrastructure/external/tmdb_client.py` - Added get_credits method with localized roles
- `backend/app/api/v1/movies.py` - Added movie credits endpoint
- `backend/app/api/v1/series.py` - Added series credits endpoint
- `backend/app/infrastructure/db/repositories/series_repository.py` - Added episode code & ID resolution fallback for series
- `website/components/media/CastCrewSection.tsx` - Created Cast & Crew circular carousel component
- `website/components/home/ContinueWatchingSection.tsx` - Switched to modern MovieCard, removed play icon & progress bar
- `website/app/page.tsx` - Made hero premiere poster responsive and compact on mobile
- `website/app/movie/[code]/page.tsx` - Integrated CastCrewSection
- `website/app/series/[id]/page.tsx` - Integrated CastCrewSection and code fallback
- `facts.md` - Added admin-panel port 3001 entry
- `backend/tests/test_cast_crew_tmdb.py` - TDD suite for TMDb credits
- `backend/tests/test_continue_watching_v2_and_hero_mobile.py` - TDD suite for CW redesign and hero mobile poster

## Verification output
```text
pytest: 33 passed, 0 failures across 14 test files
next lint: 0 errors
HTTP Live Checks:
- http://localhost:3000/ -> 200 OK
- http://localhost:3000/series/1008 -> 200 OK
- http://localhost:3000/series/gb3SGSCj -> 200 OK (resolved via episode code)
- http://localhost:3000/series/14946 -> 200 OK (resolved via episode ID)
- http://127.0.0.1:8000/api/v1/series/1008/credits -> 200 OK (17 cast & crew members)
- http://localhost:3001/ -> 200 OK (Admin panel)
```
