# Hisobot: Autopilot Yangi Manbalar va Sifat Qo'riqchilari Integratsiyasi (C12)

Ushbu hisobot `feat/autopilot-sources` branchida Uzmovi va Kinochilar adapterlarini yakunlash, sifat qo'riqchilarini `admission_gate.final_check` tizimiga ulash va avval skip qilingan PostgreSQL integratsiya testlarini to'liq yashil holatga keltirish bo'yicha amalga oshirilgan ishlarni xujjatlashtiradi.

---

## 1. Nima qo'shildi (What was added)

1. **5 ta Sifat Qo'riqchisi (`final_check`)**:
   - `runtime_mismatch`: TMDb davomiyligi bilan video davomiyligi solishtiruvi (tolerantlik konfiguratsiyasi `config.MOVIE_RUNTIME_TOLERANCE_PERCENT = 10` ga qat'iylashtirildi).
   - `season_episode_conflict`: Fayl nomi, tavsif (caption) va berilgan mavsum/qism raqamlari mosligi tekshiruvi.
   - `episode_count_exceeds_tmdb`: Mavsumdagi qism raqami TMDb rasmiy qismlar sonidan oshib ketmasligi tekshiruvi.
   - `duplicate_file_unique_id`: Telegram `file_unique_id` bo'yicha bazada takroriy fayllarni aniqlash.
   - `file_id_dead`: Telegram bot orqali `file_id` ning tirikligi (fayl serverda mavjudligi) ni tekshirish.

2. **Sifat Qoidasi (Needs Review Invarianti)**:
   - Sifat qo'riqchilaridan birortasi nuqson topsa, element **avtomatik nashr etilmaydi**, hech qanday ma'lumot o'chirilmaydi; element xavfsiz holda `needs_review` holatiga o'tkaziladi.

3. **Uzmovi Adapteri (`scraper/site_parser.py`) va Offline Fixture Testlari**:
   - `backend/tests/test_uzmovi_adapter_fixtures.py` (7 ta test):
     * To'g'ri element ekstraksiyasi
     * Serial turini aniqlash
     * Kaiju qism raqami siljishini inkor etish (`season_episode_conflict`)
     * Noto'g'ri fayl / davomiylik yo'qligini rad etish
     * Takroriy (dublikat) elementni ushlash
     * Sahifalash tugashini to'g'ri qayta ishlash
     * Manba o'chiq / tarmoq xatosi (HTTP 500) bo'lganda graceful handling

4. **Kinochilar Adapteri (`scraper/kinochilar_parser.py`) va Offline Fixture Testlari**:
   - `backend/tests/test_kinochilar_adapter_fixtures.py` (8 ta test):
     * To'g'ri kino/serial kartochkasi ekstraksiyasi
     * Bot `start_hash` ekstraksiyasi (`kinochilar_fast_bot?start=<hash>`)
     * Zamonaviy CDN iframeli / hash yo'q sahifalarda xavfsiz `None` qaytarish
     * Qism siljishi (Kaiju holati) bo'yicha rad etish
     * Noto'g'ri fayl / davomiylik yo'qligini rad etish
     * Dublikatni rad etish
     * Sahifalash tugashi
     * Manba o'chiq bo'lganda sokin to'xtash

5. **Lokal PostgreSQL Integratsiya Testlari Tiklandi**:
   - `backend/tests/pg/test_real_postgres_integration.py` ichidagi 8 ta avval skip qilingan test lokal PostgreSQL (`kinochi_test_db`) orqali to'liq ishga tushirildi va o'tdi.

---

## 2. Sifat Qo'riqchilari Jadvali

| # | Qo'riqchi Nomi | Joylashgan Joyi | Tekshiruv Sharti / Defekt Kodi | Test Fayli |
|---|---|---|---|---|
| 1 | **Runtime Mismatch (±10%)** | `backend/app/core/admission_gate.py` | TMDb runtime va fayl davomiyligi farqi 10% dan oshsa (`runtime_mismatch`) | `test_admission_gate_quality_guards.py::test_final_check_runtime_tolerance_10_percent` |
| 2 | **Fayl nomi & Qism mosligi** | `backend/app/core/admission_gate.py` | Fayl nomi/captiondagi qism raqami `episode_number` ga mos bo'lmasa (`season_episode_conflict`) | `test_admission_gate_quality_guards.py::test_final_check_episode_filename_and_caption_consistency` |
| 3 | **TMDb Qismlar Soni Chegarasi** | `backend/app/core/admission_gate.py` | Qism raqami TMDb rasmiy faslidagi jami qismlar sonidan katta bo'lsa (`episode_count_exceeds_tmdb`) | `test_admission_gate_quality_guards.py::test_final_check_episode_count_exceeds_tmdb_season` |
| 4 | **Dublikat file_unique_id** | `backend/app/core/admission_gate.py` | Bir xil Telegram fayli bazada allaqachon mavjud bo'lsa (`duplicate_file_unique_id`) | `test_admission_gate_quality_guards.py::test_final_check_duplicate_file_unique_id` |
| 5 | **File ID Tirikligi (Liveness)** | `backend/app/core/admission_gate.py` | Telegram serverida fayl o'chib ketgan yoki file_id eskirgan bo'lsa (`file_id_dead`) | `test_admission_gate_quality_guards.py::test_final_check_file_id_liveness` |

---

## 3. Testlar: Oldin va Keyin

| Test To'plami | Oldin | Keyin | Holati |
|---|:---:|:---:|:---:|
| `test_admission_gate_quality_guards.py` | 0 (yo'q edi) | **5 passed** | ✅ YANGI |
| `test_uzmovi_adapter_fixtures.py` | 0 (yo'q edi) | **7 passed** | ✅ YANGI |
| `test_kinochilar_adapter_fixtures.py` | 0 (yo'q edi) | **8 passed** | ✅ YANGI |
| `test_real_postgres_integration.py` (Real PG) | 8 SKIPPED | **8 passed** | ✅ TIKLANDI |
| `test_autopilot_rebuild.py` | 10 passed | **10 passed** | ✅ REGRESSION YO'Q |
| `test_audit_media_quality_100.py` | 2 passed | **2 passed** | ✅ SOG'LOM |
| `test_anime_catalog_titles_and_kaiju.py` | 3 passed | **3 passed** | ✅ SOG'LOM |
| `test_run_scraper_flood_wait.py` | 3 passed | **3 passed** | ✅ SOG'LOM |
| `test_bot_flood_wait_guard.py` | 4 passed | **4 passed** | ✅ SOG'LOM |
| `test_scraper_queue_endpoint.py` | 4 passed | **4 passed** | ✅ SOG'LOM |
| **JAMI AUTOPILOT SUITE** | **34 passed, 8 skipped** | **54 passed, 0 skipped** | **100% YASHIL** |

### Test Natijasi Xom Dalili (Raw Terminal Evidence):
```text
backend\tests\test_admission_gate_quality_guards.py::test_final_check_runtime_tolerance_10_percent PASSED [  1%]
backend\tests\test_admission_gate_quality_guards.py::test_final_check_episode_filename_and_caption_consistency PASSED [  3%]
backend\tests\test_admission_gate_quality_guards.py::test_final_check_episode_count_exceeds_tmdb_season PASSED [  5%]
backend\tests\test_admission_gate_quality_guards.py::test_final_check_duplicate_file_unique_id PASSED [  7%]
backend\tests\test_admission_gate_quality_guards.py::test_final_check_file_id_liveness PASSED [  9%]
backend\tests\test_uzmovi_adapter_fixtures.py::test_uzmovi_valid_item_extraction PASSED [ 11%]
backend\tests\test_uzmovi_adapter_fixtures.py::test_uzmovi_series_type_detection PASSED [ 12%]
backend\tests\test_uzmovi_adapter_fixtures.py::test_uzmovi_kaiju_episode_shift_rejection PASSED [ 14%]
backend\tests\test_uzmovi_adapter_fixtures.py::test_uzmovi_invalid_file_missing_duration_rejection PASSED [ 16%]
backend\tests\test_uzmovi_adapter_fixtures.py::test_uzmovi_duplicate_rejection PASSED [ 18%]
backend\tests\test_uzmovi_adapter_fixtures.py::test_uzmovi_pagination_end PASSED [ 20%]
backend\tests\test_uzmovi_adapter_fixtures.py::test_uzmovi_source_down_graceful_handling PASSED [ 22%]
backend\tests\test_kinochilar_adapter_fixtures.py::test_kinochilar_valid_item_extraction PASSED [ 24%]
backend\tests\test_kinochilar_adapter_fixtures.py::test_kinochilar_start_hash_extraction PASSED [ 25%]
backend\tests\test_kinochilar_adapter_fixtures.py::test_kinochilar_modern_page_without_hash_returns_none PASSED [ 27%]
backend\tests\test_kinochilar_adapter_fixtures.py::test_kinochilar_kaiju_episode_shift_rejection PASSED [ 29%]
backend\tests\test_kinochilar_adapter_fixtures.py::test_kinochilar_invalid_file_missing_duration_rejection PASSED [ 31%]
backend\tests\test_kinochilar_adapter_fixtures.py::test_kinochilar_duplicate_rejection PASSED [ 33%]
backend\tests\test_kinochilar_adapter_fixtures.py::test_kinochilar_pagination_end PASSED [ 35%]
backend\tests\test_kinochilar_adapter_fixtures.py::test_kinochilar_source_down_graceful_handling PASSED [ 37%]
backend\tests\test_autopilot_rebuild.py::test_status_transitions_valid_and_invalid PASSED [ 38%]
backend\tests\test_autopilot_rebuild.py::test_ingest_service_dedup_claim_and_recover_stale PASSED [ 40%]
backend\tests\test_autopilot_rebuild.py::test_final_check_duration_mandatory_and_source_key PASSED [ 42%]
backend\tests\test_autopilot_rebuild.py::test_extract_part_number_and_duplicate_checker PASSED [ 44%]
backend\tests\test_autopilot_rebuild.py::test_blacklist_boundary_check PASSED [ 46%]
backend\tests\test_autopilot_rebuild.py::test_routing_and_m3_no_cross_source_fallback PASSED [ 48%]
backend\tests\test_autopilot_rebuild.py::test_auto_index_m4_scraper_account_guard PASSED [ 50%]
backend\tests\test_autopilot_rebuild.py::test_pipeline_m1_m2_no_db_write_on_failed_upload_or_missing_s1e1 PASSED [ 51%]
backend\tests\test_autopilot_rebuild.py::test_html_card_parsers_extract_exact_source_id PASSED [ 53%]
backend\tests\test_autopilot_rebuild.py::test_verify_season_episode_consistency_both_arg_styles PASSED [ 55%]
backend\tests\test_audit_media_quality_100.py::test_tmdb_client_includes_multilingual_videos_param PASSED [ 57%]
backend\tests\test_audit_media_quality_100.py::test_series_with_trailer_is_100_percent_healthy PASSED [ 59%]
backend\tests\test_anime_catalog_titles_and_kaiju.py::test_anime_title_map_canonical_entries PASSED [ 61%]
backend\tests\test_anime_catalog_titles_and_kaiju.py::test_kaiju_sequence_gap_detection_and_consecutive_flow PASSED [ 62%]
backend\tests\test_anime_catalog_titles_and_kaiju.py::test_chainsaw_man_reze_movie_card PASSED [ 64%]
backend\tests\test_run_scraper_flood_wait.py::test_handle_flood_wait_retries_and_sets_status PASSED [ 66%]
backend\tests\test_run_scraper_flood_wait.py::test_recover_stale_in_progress PASSED [ 68%]
backend\tests\test_run_scraper_flood_wait.py::test_series_episode_flood_wait_raises_immediately PASSED [ 70%]
backend\tests\test_bot_flood_wait_guard.py::test_get_flood_wait_seconds_extraction PASSED [ 72%]
backend\tests\test_bot_flood_wait_guard.py::test_handle_bot_flood_wait_short_waits PASSED [ 74%]
backend\tests\test_bot_flood_wait_guard.py::test_handle_bot_flood_wait_long_aborts_without_sleep PASSED [ 75%]
backend\tests\test_bot_flood_wait_guard.py::test_run_item_catches_bot_flood_wait_and_fails_fast PASSED [ 77%]
backend\tests\test_scraper_queue_endpoint.py::test_scraper_queue_and_status_handlers_are_async PASSED [ 79%]
backend\tests\test_scraper_queue_endpoint.py::test_scraper_queue_endpoint_returns_items PASSED [ 81%]
backend\tests\test_scraper_queue_endpoint.py::test_scraper_queue_clear_all_not_blocked PASSED [ 83%]
backend\tests\test_scraper_queue_endpoint.py::test_scraper_queue_clear_all_forbids_while_running PASSED [ 85%]
backend\tests\pg\test_real_postgres_integration.py::test_d4e5f6a1b2c3_partial_unique_index_rejects_duplicate PASSED [ 87%]
backend\tests\pg\test_real_postgres_integration.py::test_10_parallel_admits_same_tmdb_id_exactly_one_row PASSED [ 88%]
backend\tests\pg\test_real_postgres_integration.py::test_rejected_items_upsert_increments_attempts PASSED [ 90%]
backend\tests\pg\test_real_postgres_integration.py::test_seed_candidates_unique_kind_tmdb_id PASSED [ 92%]
backend\tests\pg\test_real_postgres_integration.py::test_gate_promotes_pending_to_published_only_through_gate PASSED [ 94%]
backend\tests\pg\test_real_postgres_integration.py::test_public_read_paths_hide_pending_and_hidden PASSED [ 96%]
backend\tests\pg\test_real_postgres_integration.py::test_reset_media_on_branch_guards_and_execution PASSED [ 98%]
backend\tests\pg\test_real_postgres_integration.py::test_raw_insert_without_publish_status_defaults_to_pending PASSED [100%]

====================== 54 passed, 58 warnings in 26.35s =======================
```

---

## 4. Screenshotlardagi Xatoliklar Holati Audit (Foydalanuvchi rasmlari)

1. **Rasm 1 (`Iblislar qotili: Cheksiz poyezd` - 45:14 muzlashi)**:
   - `@asilmediabot` yuborgan "41 daqiqadan so'ng urinib ko'ring" xabariga ko'r-ko'rona 2465s uxlash o'rniga, `FloodWait 120s` o'chirgichi qo'yildi va muammo to'liq bartaraf etilgan (`test_bot_flood_wait_guard.py`).
2. **Rasm 2, 3, 4, 5 (Nomi xato anime kartochkalari va hoverdagi qizil yozuvlar)**:
   - Website kartochkalarida `Cinematic Red` qoidasiga ko'ra sichqoncha ustiga borganda (hover) sarlavha `#E50914` qizil rangga o'tadi (`group-hover:text-primary`).
   - Xom scraperdan kelgan noto'g'ri nomlar `smart_enricher.py` (`ANIME_TITLE_MAP`) orqali rasmiy kanonik nomlarga bog'langan:
     * `Qilich o'nlay magistrlari` -> **`Qilich san'ati onlayn`** (Sword Art Online, Series #1025)
     * `Kaiju ra 8-son` -> **`Kaiju: 8-son`** (Series #1026, 12 ta ketma-ket qism tartibi tiklangan)
     * `Kelajak kundlami` -> **`Kelajak kundaligi`** (Mirai Nikki, Series #1023)
     * `U dunyo zugaylari` -> **`U dunyo tsugaylari`** (Yomi no Tsugai, Series #1013)
     * `Solo Leveling` -> **`Yakkaxon daraja oshirish (Solo Leveling)`** (Series #1015)
     * `Chainsaw Man: Reze arc` -> Serial emas, **Film kartochkasi** (#842, TMDb: 1218925) sifatida ajratildi.

---

## 5. Jonli Sinovga (LIVE) Tayyorlik Talablari

Jonli sinov (LIVE) faqat foydalanuvchining alohida "LIVE" buyrug'i berilgandagina ishga tushiriladi. Buning uchun zarur shartlar:
1. **Telegram Sessiya va Bot ruxsatlari**: Telethon sessiyasining faolligi va test uchun 3 tadan oshmagan element chegarasi (`limit=3`).
2. **Baza Migratsiyasi**: `9c8d7e6f5a4b` va `b2c3d4e5f6a7` migratsiyalari head holatida bo'lishi (tasdiqlangan).
3. **Admin UI**: Hech qanday o'zgarish kiritilmadi (C8 bilan to'qnashmasligi uchun saqlab qolindi).

---

## 6. Ochiq Masalalar va Xulosalar

- **Kinochilar yangi sahifalari**: `kinochilar.cc` ning yangi DLE sahifalarida Telegram bot deep-linklari (`kinochilar_fast_bot?start=...`) o'rniga tashqi CDN (`stravers.live`) iframe'lari joylashtirilmoqda. Adapter bot havolasi bo'lmagan sahifalarni soxta yozuv yaratmasdan xavfsiz holda `needs_review` qilib chetga suradi.
- **Uzmovi ID nomuvofiqligi**: Saytdagi ID raqamlari botdagi qidiruv kodlariga har doim ham to'g'ridan-to'g'ri to'g'ri kelmaydi. Guard tasdiqlanmagan kodlarni rad etadi.
