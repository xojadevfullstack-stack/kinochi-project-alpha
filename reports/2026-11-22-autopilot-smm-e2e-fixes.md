# Slice Report: 2026-11-22-autopilot-smm-e2e-fixes

## What was done
1. 1-sikl (`Autopilot` scraper -> TMDB -> Telegram Storage -> DB) va 2-sikl (`SMM Worker` -> Sparse MP4 download -> Gemini Vision dynamic `blur_boxes` -> 9:16 FFmpeg klipp -> `waiting_approval`) jonli E2E ishga tushirilib, aniqlangan 4 ta real nuqson TDD usulida tuzatildi.
2. `gemini_identify_movie()` (`503` qayta urinish + `gemini-3.5-flash` fallback + majburiy `search_title_en`/`search_title_ru`) hamda `pick_canonical_uzbek_title()` tuzatilib, `Ouk Strit ko'chasining oxiri` (`#3956`, TMDB `1101383`) muvaffaqiyatli nashr qilindi.
3. `smm_clipper.py` / `smm_pipeline.py` da VBR 1080p fayllarda klip oxiri sparse nol baytlarga tushib qolishini bartaraf etuvchi `compute_sparse_byte_range()` (MP4 `stco/co64` bosh+oxir indeksi + oqimli faylga yozish) hamda `smm_worker.py` da xato vazifani `failed` ga ajratish qo'shilib, `clip_2.mp4` (`#3955`) va `clip_3.mp4` (`#3956`) kliplari muvaffaqiyatli yaratildi.

4. Jonli Admin Panel QA (`https://kinochi-project-alpha-qoqf.vercel.app/smm`) natijasida topilgan tab almashish poyga sharti (`isLatestRequest`), `recut` UI yangilanish kechikishi va Render ephemer diskida `<video>` 404/ORB berish muammosi (`clip_storage_message_id` + `GET /api/v1/smm/jobs/{id}/video` + `BOT_TOKEN` kanal zaxirasi) tuzatildi (`clip_2.mp4` -> `msg_id=5067`, `clip_3.mp4` -> `msg_id=5068`).

## Changed files
- `scraper/smart_enricher.py` - Gemini `503` retry/fallback, JSON mimeType, majburiy `search_title_en/ru` va `pick_canonical_uzbek_title()`.
- `scraper/smm_clipper.py` - `compute_sparse_chunk_mb()`, `compute_sparse_byte_range()` (MP4 `stco/co64` start/end offset + 1MB RAM oqimli yozish).
- `scraper/smm_pipeline.py` - adaptiv sparse segment (`chunk_mb=None`) va `progress_cb` bosqichlari.
- `scraper/smm_worker.py` - xato izolyatsiyasi (`failed`), `clip_storage_message_id` (`BOT_TOKEN` + `send_file` fallback), va ikkala rejimda admin Telegram preview.
- `scraper/smm_publishers/telegram_pub.py` - janrlarni ` • ` bilan formatlash, `send_admin_smm_preview()` (`SEMI_AUTO` tugmalari vs `FULL_AUTO` xabar).
- `backend/app/infrastructure/db/models/smm.py`, `backend/alembic/versions/f6a7b8c9d0e1_add_smm_admin_tg_and_progress.py`, `backend/app/api/v1/smm.py` - `admin_telegram_id`, `progress_pct/progress_stage`, `/smm/progress`, `/smm/bot/jobs/{id}/*`, `/smm/jobs/{id}/video`.
- `bot/handlers/smm_admin.py`, `bot/services/api_client.py`, `bot/main.py` - Telegram inline callback boshqaruvi.
- `admin-panel/app/smm/page.tsx`, `admin-panel/lib/smmHelpers.mjs` - jonli Progress paneli, `Admin Telegram ID`, poyga himoyasi (`isLatestRequest`), `/video` pleyeri.
- Testlar: `test_smm_api.py`, `test_smm_clipper.py`, `test_smm_pipeline_and_telegram_pub.py`, `test_smm_worker.py`, `test_smart_enricher_regression.py`, `bot/tests/test_smm_admin.py`, `admin-panel/tests/smmHelpers.test.mjs`.

## check output
```text
Ruff (changed files): All checks passed!
Alembic: f6a7b8c9d0e1 (head)
Pytest (SMM + Enricher + Movie + Public routes): 66 passed, 2 warnings in 11.39s
Pytest (Bot full suite): 107 passed in 6.51s
Admin Panel (node --test + tsc + next build): 7 passed, 0 failed; 22/22 routes Exit 0
```

## Risks and unknowns
- Render jonli serverida `smm_clip_jobs #2` va `#3` ishga tushmagani sababi Render Logs / Env Vars (`SMM_AUTOPILOT_ENABLED=true`, `SMM_TELEGRAM_STRING_SESSION`) orqali tasdiqlanishi kerak.
- Bugungi tuzatishlar hali `origin/main` ga push qilinmagan (`uploads/smm/clip_2.mp4` va `clip_3.mp4` mahalliy diskda tayyorlangan; Render'da ko'rinishi uchun commit/push qilinib Render worker qayta ishlashi yoki lokal admin/API orqali ko'rish kerak).

## Concept to explain to the user
- **MP4 `stco/co64` Index-Bounded Sparse Windowing:** Katta video faylni to'liq yuklamasdan kerakli sekundlarni kesishda faqat boshlang'ich baytga qarab qat'iy 25 MB olish VBR (o'zgaruvchan bitreyt) sahnalarda oxirgi sekundlarning bo'sh nol baytlarga tushishiga olib keladi; bosh va oxirgi vaqtning `stco/co64` jadvalidagi bayt chegarasini o'qib yuklash xuddi kitobning kerakli bobi qaysi betdan qaysi betgacha ekanini mundarijadan bilib, aynan o'sha sahifalarni butun yirtib olmasdan nusxalashga o'xshaydi.

## Next step
- O'zgarishlarni commit + `origin/main` ga push qilish va Render Env Vars/Logs da `"SMM worker started: enabled=True has_smm_session=True"` ni tasdiqlash.
