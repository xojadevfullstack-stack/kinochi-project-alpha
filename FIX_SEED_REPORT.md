# FIX_SEED_REPORT.md: Audit Topilmalarini Bartaraf Etish Hisoboti

Ushbu hisobot `AUDIT_SEED.md` auditida aniqlangan barcha topilmalar (SF-001 dan SF-006 gacha) bo'yicha amalga oshirilgan tuzatishlar, testlar va qoldiq xatarlarni jamlaydi.

## Xulosa Jadvali (Summary Table)

| Finding | Status | Commit | Test | Residual Risk |
|---|---|---|---|---|
| **SF-001** (HIGH) | FIXED | `f10b2b7` | `backend/tests/test_audit_fixes.py::test_sf_001_adversarial_matcher_no_substring_false_positive` | Substring bo'yicha soxta ijobiy mosliklar bartaraf etildi (FP=0). O'zbekcha tarjima qilingan sarlavha inglizcha yoki ruscha slug bilan ta'minlanmagan bo'lsa, xavfsiz tarzda rad etiladi (FN). |
| **SF-002** (MEDIUM) | FIXED | `66e9df9` | `backend/tests/test_audit_fixes.py::test_sf_002_empty_title_blacklist_does_not_match_all` | Qoldiq xavf yo'q. Bo'sh sarlavha holatida `LIKE '%%'` hosil bo'lmaydi, faqat to'ldirilgan satrlar qora ro'yxat bo'yicha tekshiriladi. |
| **SF-003** (MEDIUM) | FIXED | `df06752` | `backend/tests/test_audit_fixes.py::test_sf_003_retry_rejected_item_resets_seed_candidate` | Qoldiq xavf yo'q. Admin interfeysida rad etilgan element retry qilinganda `seed_candidates` holati avtomatik ravishda `new` va `attempts=0` ga qaytadi. |
| **SF-004** (MEDIUM) | FIXED | `4e849bc` | `backend/tests/test_audit_fixes.py::test_sf_004_windows_console_unicode_encoding` | Qoldiq xavf yo'q. `sys.stdout` va `sys.stderr` UTF-8 kodirovkasiga qayta sozlandi; Windows konsollarida (cp1251/cp866) emojilar sababli crash yuz bermaydi. |
| **SF-005** (LOW) | FIXED | `94e0c04` | `backend/tests/test_audit_fixes.py::test_sf_005_linter_checks_clean` | Qoldiq xavf yo'q. Ishlatilmagan importlar tozalandi, `ruff check` barcha tekshirilgan fayllarda 0 ta xatolik bilan muvaffaqiyatli o'tadi. |
| **SF-006** (LOW) | FIXED | `76812a6` | `backend/tests/test_reset_media_s8.py::test_s8_reset_media_guard_3_production_blocked` | Qoldiq xavf yo'q. `APP_ENV='production'` bo'lganda bazani tozalash skripti bloklanishi bo'yicha alohida avtomatlashtirilgan regressiya testi mavjud. |

---

## Verifikatsiya Natijalari

1. **compileall**: 
   - `python -m compileall backend scraper scripts` to'liq muvaffaqiyatli yakunlandi (Exit code: 0, xatoliklar: 0).
2. **pytest**:
   - `pytest -rs`: 158 ta test o'tdi (158 passed, 0 failed, 0 skipped in 17.52s).
3. **Bypass Scan**:
   - `scraper/tmdb_top_ingestor.py` va `scripts/reset_media.py` fayllarida `movies`, `series`, `seasons`, `episodes`, `translations` jadvallariga hech qanday to'g'ridan-to'g'ri `INSERT` yoki `UPDATE` yo'qligi tasdiqlandi. Faqat Admission Gate orqali nashr etish amalga oshiriladi.
4. **Matcher Adversarial Set (41 juftlik)**:
   - Jami: 41 juftlik.
   - To'g'ri Ijobiy (TP): 10 ta.
   - To'g'ri Salbiy (TN): 24 ta.
   - Soxta Ijobiy (FP): **0 ta** (False Positive xavfi to'liq bartaraf etildi).
   - Xavfsiz Rad Etish (FN): 7 ta.
5. **Alembic Checks**:
   - Yagona bosh migratsiya: `a1b2c3d4e5f6 (head)`.
   - SQL preview: `alembic upgrade f1a2b3c4d5e6:a1b2c3d4e5f6 --sql` to'liq additiv (`CREATE TABLE seed_candidates`, `CREATE INDEX`).
   - Neon branch tekshiruvi: `needs DB verification` (chunki `TEST_DATABASE_URL` muhit o'zgaruvchisi berilmagan, hard rules bo'yicha SQL preview bilan tasdiqlandi).
6. **Reset Guards**:
   - Guard 1 (`--execute` yo'qligi) -> Dry run rejimi.
   - Guard 2 (`--confirm YES` berilishi) -> Tasdiqsiz ishlamaydi.
   - Guard 3 (`APP_ENV=production`) -> Bloklanadi.
