stage 1 DONE 35bbced
stage 2 DONE f5f1824
stage 3 DONE 2709dd7
stage 4 DONE ec4255c
stage 5 DONE cb7c187
stage 6 DONE 52e2441
stage 7 DONE 07872cc
stage 8 DONE d598305

## OPEN: uzmovi code
1. Aniq kod manbai (pipeline:864-877, 4189): payload.bot_code / payload.code -> item.source_id -> id prefiksi "uzmovi_<raqam>"; source_id = sayt URL'idagi /(\d+)-slug.html raqami (site_parser.py:87,161).
2. Kod raqamli bo'lmasa/yo'q bo'lsa: serial yo'li (pipeline:895-900) va _fetch_uzmovie_video (pipeline:4190-4197) status needs_review, reason "no_exact_code" qo'yadi, None/False qaytaradi, nom bo'yicha qidirmaydi (kodda ishlaydi; ishga tushirib sinalmadi).
3. Uzmovi sahifa HTML'ida bot kodi/deep-link izlanmaydi: site_parser regex'lari faqat href /(\d+)-slug.html, reyting va serial kalit so'zlarini qidiradi (t.me / ?start= / bot_code uchun grep natijasi bo'sh).
4. UNKNOWN: sayt URL raqami UzmovieTV_Bot kodiga teng ekani kodda tasdiqlanmagan; payload.bot_code'ni hech bir parser to'ldirmaydi (git grep: faqat o'qiladi).
5. Xavf: raqam bot kodiga teng bo'lmasa bot noto'g'ri video yuboradi yoki "topilmadi" deydi (cross-title xavfi, final_check duration/runtime orqali qisman ushlanadi).
6. Keyingi qadam (odam): 2-3 ta real uzmovi sahifasi va botda kod mosligini qo'lda tekshirish; mos kelmasa parser'ga haqiqiy bot kodini olish qo'shish.

## QOLDI (C): Postgres tekshiruvi o'tkazilmadi
Docker daemon ishlamaydi (dockerDesktopLinuxEngine pipe topilmadi). alembic upgrade/downgrade va backend/tests/test_ingest_claim_postgres.py (TEST_POSTGRES_URL bilan) Docker ishga tushgach qo'lda yurgiziladi.

## AUDIT & GUARDS (#1-#6) DONE
- #1 Alembic `c011ec7100`: `collections(id)` ga FK qiladi; `collections` migratsiyalarda yaratilmagan (`main.py:95` `create_all` orqali yaratilgan). Tavsiya: (a) tarixiy migratsiyalarga tegmaslik.
- #2 `ingest_items` offline SQL (`f1322da82a96:9c8d7e6f5a4b --sql`): `IngestItemModel` bilan farq yo'q; single head `9c8d7e6f5a4b`.
- #3 Guard `UZMOVI_BOT_CODE_VERIFIED` (default `False`): commit `3d285a1` (`uzmovi_code_unverified` -> `needs_review`).
- #4 Guard `SCRAPER_ENABLED` (default `False`): commit `3bc154f` (CLI, ProcessManager, Admin API bloklandi; `--help`/`--stats` ishlaydi).
- #5 Uncommitted fayllar auditi bajarildi; `.gitignore` ga `*.dump` commit qilindi (`abadfb1`).
- #6 `test_ingest_claim_postgres.py`: localhost + `test` DB nomi talabi va vaqtinchalik `ingest_claim_<hex>` sxema izolyatsiyasi (`8ae094c`).

