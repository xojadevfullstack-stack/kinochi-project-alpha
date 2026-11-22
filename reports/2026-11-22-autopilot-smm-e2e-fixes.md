# Slice Report: 2026-11-22-autopilot-smm-e2e-fixes

## What was done
1. 1-sikl (`Autopilot` scraper -> TMDB -> Telegram Storage -> DB) va 2-sikl (`SMM Worker` -> Sparse MP4 download -> Gemini Vision dynamic `blur_boxes` -> 9:16 FFmpeg klipp -> `waiting_approval`) jonli E2E ishga tushirilib, aniqlangan 4 ta real nuqson TDD usulida tuzatildi.
2. `gemini_identify_movie()` (`503` qayta urinish + `gemini-3.5-flash` fallback + majburiy `search_title_en`/`search_title_ru`) hamda `pick_canonical_uzbek_title()` tuzatilib, `Ouk Strit ko'chasining oxiri` (`#3956`, TMDB `1101383`) muvaffaqiyatli nashr qilindi.
3. `smm_clipper.py` / `smm_pipeline.py` da VBR 1080p fayllarda klip oxiri sparse nol baytlarga tushib qolishini bartaraf etuvchi `compute_sparse_byte_range()` (MP4 `stco/co64` bosh+oxir indeksi + oqimli faylga yozish) hamda `smm_worker.py` da xato vazifani `failed` ga ajratish qo'shilib, `clip_2.mp4` (`#3955`) va `clip_3.mp4` (`#3956`) kliplari muvaffaqiyatli yaratildi.

## Changed files
- `scraper/smart_enricher.py` - Gemini `503` retry/fallback, JSON mimeType, majburiy `search_title_en/ru` tarjima yo'riqnomasi va `pick_canonical_uzbek_title()`.
- `scraper/smm_clipper.py` - `compute_sparse_chunk_mb()`, `compute_sparse_byte_range()` (MP4 `stco/co64` start/end offset + 1MB RAM oqimli yozish).
- `scraper/smm_pipeline.py` - qat'iy `25 MB` o'rniga adaptiv sparse segment (`chunk_mb=None`).
- `scraper/smm_worker.py` - `process_generating_job()` xato izolyatsiyasi (`failed`) va `.order_by(SmmClipJobModel.id.asc())`.
- `scraper/smm_publishers/telegram_pub.py` - janrlarni ` • ` bilan toza formatlash.
- `backend/tests/test_smm_clipper.py` - adaptiv chunk va `stco` end-bound byte range testlari.
- `backend/tests/test_smm_worker.py` - xato vazifa navbatni to'sib qo'ymasligi testi.
- `backend/tests/test_smart_enricher_regression.py` - `503` retry, `The End of Oak Street` score va o'zbekcha nomni saqlash testlari.
- `STATE.md`, `docs/learned.md` - holat va o'rganilgan tushunchalar yangilandi.

## check output
```text
Ruff (changed files):
backend\.venv\Scripts\ruff.exe check scraper/smm_clipper.py scraper/smm_pipeline.py scraper/smm_worker.py scraper/smm_publishers/telegram_pub.py backend/tests/test_smm_clipper.py backend/tests/test_smm_worker.py backend/tests/test_smart_enricher_regression.py
-> All checks passed! (Exit code 0)

Alembic:
e5f6a7b8c9d0 (head)

Pytest (SMM + Enricher + Movie + Public routes):
59 passed, 2 warnings in 11.60s

Pytest (Bot full suite):
106 passed in 6.45s
```

## Risks and unknowns
- Render jonli serverida `smm_clip_jobs #2` va `#3` ishga tushmagani sababi Render Logs / Env Vars (`SMM_AUTOPILOT_ENABLED=true`, `SMM_TELEGRAM_STRING_SESSION`) orqali tasdiqlanishi kerak.
- Bugungi tuzatishlar hali `origin/main` ga push qilinmagan (`uploads/smm/clip_2.mp4` va `clip_3.mp4` mahalliy diskda tayyorlangan; Render'da ko'rinishi uchun commit/push qilinib Render worker qayta ishlashi yoki lokal admin/API orqali ko'rish kerak).

## Concept to explain to the user
- **MP4 `stco/co64` Index-Bounded Sparse Windowing:** Katta video faylni to'liq yuklamasdan kerakli sekundlarni kesishda faqat boshlang'ich baytga qarab qat'iy 25 MB olish VBR (o'zgaruvchan bitreyt) sahnalarda oxirgi sekundlarning bo'sh nol baytlarga tushishiga olib keladi; bosh va oxirgi vaqtning `stco/co64` jadvalidagi bayt chegarasini o'qib yuklash xuddi kitobning kerakli bobi qaysi betdan qaysi betgacha ekanini mundarijadan bilib, aynan o'sha sahifalarni butun yirtib olmasdan nusxalashga o'xshaydi.

## Next step
- O'zgarishlarni commit + `origin/main` ga push qilish va Render Env Vars/Logs da `"SMM worker started: enabled=True has_smm_session=True"` ni tasdiqlash.
