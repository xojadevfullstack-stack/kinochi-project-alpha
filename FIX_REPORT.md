# FIX_REPORT.md — Audit Topilmalarini Bartaraf Etish Hisoboti

Ushbu hisobot `AUDIT_FINDINGS.md` hujjatidagi barcha 17 ta topilmaning tuzatilishi, test natijalari va qolgan qoldiq xatarlarni (residual risk) to'liq jamlaydi.

| Finding ID | Severity | Status | Commit | Regression Test | Residual Risk |
|---|---|---|---|---|---|
| **F-001** | CRITICAL | FIXED | `dc5fbdd` | `backend/tests/test_fix_f011_cors_reflection.py`, `backend/tests/test_fix_f001_ingest_pusu.py` | Past (Kurtlar Vadisi import skripti endi to'liq `pre_check` va til tekshiruvidan o'tadi) |
| **F-002** | CRITICAL | FIXED | `3ef991f` | `backend/tests/test_fix_f002_pipeline_pre_check.py` | Past (Sifatsiz/nuqsonli elementlar pipeline'ni buzmaydi, `rejected_items` ga yoziladi) |
| **F-003** | CRITICAL | FIXED | `7949101` | `backend/tests/test_fix_f003_series_upload_gate.py` | Yo'q (Ota serial faqat `final_check` muvaffaqiyatli bo'lsagina `published` holatiga o'tadi) |
| **F-004** | HIGH | NEEDS-OWNER | `082e129` | `git grep "kinochi_db_user:"` (0 matches) | O'rta (Kod tozalandi, lekin eski commitdagi Neon PostgreSQL paroli DB egasi tomonidan Neon konsolida rotatsiya qilinishi shart) |
| **F-005** | HIGH | FIXED | `8cb31a8` | `backend/tests/test_fix_f005_default_languages.py` | Yo'q (API, Bot va Admin Paneldagi qattiq kodlangan "Asosiy" placeholderi "O'zbekcha" ga o'tkazildi) |
| **F-006** | HIGH | FIXED | `1185a5d` | `backend/tests/test_fix_f006_seasons_publish_status.py` | Yo'q (Ommaviy `GET /series/{id}/seasons` faqat nashr qilingan seriallar uchun ishlaydi, aks holda 404) |
| **F-007** | HIGH | FIXED | `39e5c77` | `backend/tests/test_fix_f007_collections_leak.py` | Yo'q (To'plamlar va kontekst yo'llarida nashr etilmagan pending/hidden kontentlar sizib chiqishi yopildi) |
| **F-008** | HIGH | FIXED | `732d5e3` | `backend/tests/test_fix_f008_tmdb_concurrency.py` | Past (Additiv Alembic migratsiyasi `d4e5f6a1b2c3` va `pg_advisory_xact_lock` joriy qilindi; prod DB da upgrade kutilmoqda) |
| **F-009** | MEDIUM | FIXED | `47a8bc9` | `backend/tests/test_fix_f009_script_bypass_flags.py` | Yo'q (Barcha DB-modifikatsiya skriptlarida `--i-know-this-bypasses-gate` bayrog'i majburiy qilindi) |
| **F-010** | MEDIUM | FIXED | `27177e5` | `backend/tests/test_fix_f010_reports_system.py` | Past (Additiv migratsiya `f1a2b3c4d5e6` bilan `telegram_user_id` ustuni qo'shildi; 5 ta shikoyatda media avto-yashiriladi) |
| **F-011** | MEDIUM | FIXED | `e0ec104` | `backend/tests/test_fix_f011_cors_reflection.py` | Yo'q (500 xatoliklarda ixtiyoriy domenlar uchun CORS reflection yopildi, faqat ruxsat etilgan domenlar o'tadi) |
| **F-012** | MEDIUM | FIXED | `b36c561` | `backend/tests/test_fix_f012_ssl_verification.py` | Past (Scraper modullarida `ssl=False` olib tashlandi; sertifikati buzilgan saytlar xavfsizlik uchun bloklanadi) |
| **F-013** | MEDIUM | FIXED | `54d4201` | `backend/tests/test_fix_f013_swallowed_exceptions.py` | Yo'q (Muhim modullardagi 91 ta yashirin `except ...: pass` bloklari `logger.debug/warning` ga almashtirildi) |
| **F-014** | LOW | FIXED | `7979b6f` | `npm run build` in `admin-panel` (19/19 sahifalar muvaffaqiyatli qurildi) | Yo'q (Admin panelda `/rejected` sahifasi, qayta urinish va qora ro'yxatga olish tugmalari yaratildi) |
| **F-015** | LOW | FIXED | `319d37c` | `git log --oneline` solishtiruvi | Yo'q (`BUILD_PROGRESS.md` dagi barcha commit identifikatorlari git log bilan 100% sinxronlandi) |
| **F-016** | LOW | FIXED | `d267d85` | `backend/tests/test_fix_f016_cyrillic_slug.py` | Yo'q (`to_slug` va `to_stem_slug` da kirill yozuvi o'zbek/rus qoidalari bo'yicha to'liq transliteratsiya qilinadi) |
| **F-017** | LOW | FIXED | `a892fce` | `backend/tests/test_fix_f017_single_instance_lock.py` | Yo'q (Scraper CLI da `ScraperCliLock` va PID nazorati orqali bir vaqtda bir nechta jarayon ishga tushishi to'xtatildi) |
