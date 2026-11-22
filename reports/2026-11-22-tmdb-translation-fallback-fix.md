# Slice Report: 2026-11-22-tmdb-translation-fallback-fix

## What was done
1. `translator.py` dagi ruscha tavsifni `cyrillic_to_latin` bilan lotin harflariga ko'chirib (`V budushem...`) soxta `True` qaytarish hamda CJK `original_title` (`星河入梦`) ni o'zbekcha nom sifatida qaytarish xatolari tuzatildi; qo'shimcha bepul fallbacklar (`clients5.google.com`, `api.mymemory.translated.net`) qo'shildi.
2. `tmdb_client.py` (`get_details`) da `title_en` `orig_title` bilan soya ostida qolib ketishi tuzatilib `en-US` ma'lumotidan to'g'ri olinadigan qilindi; `content_lookup.py` `en_title` ni tarjimon va javobga uzatdi.
3. `admin-panel` (`tmdbFormHelpers.mjs`, `movies/page.tsx`, `series/page.tsx`) tarjima muvaffaqiyatsiz bo'lsa (`is_translated === false`) mavjud sarlavha/ta'rifni ustidan yozmaydigan qilindi va `🇬🇧 Inglizcha` sarlavha varianti qo'shildi.

## Changed files
- `backend/app/infrastructure/external/translator.py` - Script-aware fallback, `clients5`/`mymemory` zaxirasi, `en_title` qo'llab-quvvatlovi.
- `backend/app/infrastructure/external/tmdb_client.py` - `title_en` ni `en_data` dan to'g'ri olish (+ avvalgi `genre_ids`/`is_tv_pref` yaxshilanishi).
- `backend/app/api/v1/content_lookup.py` - `en_title` ni `translate_title_to_uzbek` va javobga uzatish.
- `backend/tests/test_translation.py` - 3 ta yangi regressiya testi.
- `admin-panel/lib/tmdbFormHelpers.mjs` - `isTitleTranslated`/`isDescriptionTranslated` himoyasi.
- `admin-panel/tests/tmdbFormHelpers.test.mjs` - tarjima muvaffaqiyatsiz bo'lganda mavjud matnni saqlash testi.
- `admin-panel/app/movies/page.tsx` & `admin-panel/app/series/page.tsx` - `🇬🇧 Inglizcha` variant tugmasi va tarjima xatoligi ogohlantirishi.
- `STATE.md`, `docs/learned.md` - Slice yozuvlari.

## check output
```text
> backend\.venv\Scripts\python.exe -m pytest backend/tests/test_translation.py backend/tests/test_content_lookup_translate.py backend/tests/test_movie_service.py backend/tests/test_kinochilar_adapter_fixtures.py -q
25 passed, 2 warnings in 4.41s

> backend\.venv\Scripts\python.exe -m pytest backend/tests/test_anime_matching_fixes.py -q
4 passed, 1 warning in 1.46s

> node --test admin-panel/tests/tmdbFormHelpers.test.mjs
# tests 3, pass 3, fail 0

> .\admin-panel\node_modules\.bin\tsc.cmd -p admin-panel\tsconfig.json --noEmit
(exit code 0)

> npm --prefix admin-panel run build
 ✓ Generating static pages (22/22)
(exit code 0)

> node --test website/tests/breadcrumbHelpers.test.mjs
# tests 3, pass 3, fail 0

> bot\.venv\Scripts\python.exe -m pytest bot/tests/ -q
106 passed in 11.41s
```

## Risks and unknowns
- Render serverida `GEMINI_API_KEY` kvotasi tugagan yoki `translate.googleapis.com` bloklangan bo'lsa ham yangi `clients5`/`mymemory` va UI himoyasi ishlaydi, lekin Render deploy tugagach `1359005` (`Per Aspera Ad Astra`) da jonli sinov o'tkazish zarur.
- Windows'da `make` o'rnatilmaganligi sababli tekshiruvlar alohida buyruqlar bilan bajarildi.

## Concept to explain to the user
- **Script-Aware Translation Fallback:** Tarjima xizmati javob bermaganda ruscha matnni shunchaki lotin harflariga almashtirib (`cyrillic_to_latin`) "tarjima qilindi" deb bermaslik, aksincha haqiqiy o'zbek kirillini ruschadan ajratish va tarjima bo'lmaganda eski yaxshi matnni saqlab qolish.
- **O'xshatish:** Tarjimon kelmay qolganda ruscha matnni o'zbek harflari bilan ko'chirib yuborish o'rniga zaxira tarjimonni chaqirish yoki avvalgi to'g'ri matnga tegmaslik.

## Next step
- Render va Vercel deploy yangilangach `1359005` filmida `"To'ldirish"` tugmasini jonli tekshirish.
