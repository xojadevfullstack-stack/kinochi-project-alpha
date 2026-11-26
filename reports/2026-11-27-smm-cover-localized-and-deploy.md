# Slice Report: 2026-11-27-smm-cover-localized-and-deploy

## What was done
1. `docs/decisions.md` ga `ADR-010` (Poster Localization v7 standarti) kiritildi; `poster_localizer.py` da o'zbekcha Unicode apostroflar (`ʻ`, `ʼ`, `‘`, `’`) shrift tofu-qutichasi (`[]`) bermasligi uchun `_sanitize_font_text` hamda raqam aksent ajratgichi aniqlandi (`69 passed`).
2. `scraper/smm_pipeline.py` (`_fetch_poster_bytes`) dagi noto'g'ri import va `/api/v1/posters/tg/` to'liq URL tekshiruvi tuzatildi; `scraper/smm_worker.py` (`_ensure_localized_poster_url`) har bir ijtimoiy tarmoq video coverini yaratishdan oldin tarjima qilinmagan posterni avtomatik o'zbekchalashtiradigan qilindi.
3. Jonli DB dagi barcha navbatdagi SMM yozuvlari (`#9..#16`) uchun o'zbekcha posterlar generatsiya qilinib (`Taxtlar o'yini #1119` qayta yangilandi), 7 ta klip yangi cover bilan renderlanishi uchun `generating` (`start_sec` saqlangan) holatga qo'yildi va kod `feat/smm-autopilot` hamda `origin/main` deploy branchiga push qilindi.

## Changed files
- `backend/app/infrastructure/external/poster_localizer.py` - `_sanitize_font_text` va `accent_color` split aniqligi.
- `scraper/smm_pipeline.py` - to'liq Telegram proxy URL dan bevosita `telegram_client.download_file_bytes` o'qish.
- `scraper/smm_worker.py` - `_ensure_localized_poster_url` bilan SMM video cover uchun avtomatik lokalizatsiya.
- `backend/tests/{test_poster_localizer,test_smm_pipeline_and_telegram_pub,test_smm_worker}.py` - apostrof, Telegram cover fetch va avto-lokalizatsiya testlari.
- `docs/decisions.md`, `STATE.md` - ADR-010 va deploy holati.

## check output
```text
All checks passed!
i9d0e1f2a3b4 (head)
backend/tests/{test_smm_pipeline_and_telegram_pub,test_smm_worker,test_poster_localizer,test_poster_triggers,test_posters_storage,test_fix_f013_swallowed_exceptions}.py -> 69 passed in 16.85s
bot/tests/ -> 116 passed in 11.39s
```

## Risks and unknowns
- Render deploy (`origin/main`) ko'tarilgach worker `Job #9..#16` ni birma-bir (`~1–2 min`/klip, chunki `start_sec` allaqachon topilgan) qayta render qiladi; agar biror klip chiqish soati juda yaqin bo'lsa avval `generating` tugab keyin `scheduled` chiqadi.
- `smm_pipeline.py` va `smm_worker.py` da avvaldan uncommitted turgan boshqa o'zgarishlar (masalan SMM retention/hook) bor edi; faqat shu fayllar `feat/smm-autopilot` / `main` ga qo'shilganda diff hajmi tekshirildi (`origin/main` allaqachon `2a9b054` da).

## Concept to explain to the user
- **Unicode Apostrophe Sanitization & Pre-Cover Localization Hook**: Shrift faylida kam uchraydigan `U+02BB` (`ʻ`) belgisi bo'lmasa rasmga to'rtburchak (`[]`) chiqadi; uni oddiy `'` ga normallashtirish muammoni hal qiladi, `_ensure_localized_poster_url` esa ijtimoiy tarmoq klipi chizilishidan oldin inglizcha posterni avtomatik o'zbekchaga o'giradi.

## Next step
- Render deploy tugagach `SMM` bo'limidan yangilangan o'zbekcha coverli kliplar chiqishini kuzatish.
