# MUSTAQIL TEKSHIRUV HISOBOTI: KAIJU NO. 8 & BOT/BACKEND FIX (C5 / F1-S69)

**Tekshiruvchi roli:** Mustaqil auditor (Independent Auditor)  
**Sana:** 2026-11-10  
**Obyekt:** Kaiju No. 8 (Series ID: 1026) ma'lumotlari, s_1024 seriali va bot/backend kechikish hamda timeout arxitekturasi  
**Holat:** Kodga tegilmadi; barcha tekshiruvlar `tests/audit_kaiju/` dagi testlar, prod DB (SELECT/EXPLAIN) va Telethon (Read-Only) orqali o'tkazildi.

---

## 1. Da'volar va Haqiqiy Dalillar Jadvali

| # | Da'vo (C5 hisobotidagi iddao) | Xulosa | Haqiqiy Dalil va Terminal Isboti |
|---|---|:---:|---|
| **D1** | Kaiju No. 8 (Series 1026, Season 1307) qismlari 1 dan 12 gacha to'g'ri tartibda, soxta 13-23 qismlar yo'q | **TASDIQLANDI** | `audit_k6_kaiju_data.py`: Bazada jami 12 ta qism mavjud (`Ep 1..12`). Storage kanaldagi xabarlar (msg 2733, 2699-2705, 2713-2715, 2734) 100% unikal `doc_id` ga ega, davomiyligi 23:39 - 23:40. O'chirilgan 13-19 qismlar bo'yicha bazada birorta ham yetim yozuv (orphan translations/history/reports) qolmagan. |
| **D2** | B-Tree indeksi `ix_episodes_code` orqali qism qidirish tezligi 11.6s dan 1.72s (iliq 150ms) ga tushdi | **QISMAN** | `test_k3_prod_explain.py`: Prod DB da `EXPLAIN (ANALYZE)` ko'rsatkichida indeksli qidiruv **0.055 ms** va 3 ta buffer hit oldi (`Index Scan using ix_episodes_code`). Iliq holatda API 150ms ga tushdi. Biroq sovuq startda Neon DB uyg'onishi 1.72 soniya oladi, bu esa loyihaning dastlabki `<500ms` qabul mezoniga to'liq mos kelmaydi (sovuq startda 500ms dan oshadi). |
| **D3** | `bot/services/api_client.py` timeouti 25s ga ko'tarildi va `APIConnectionError` orqali "topilmadi" xatosi yo'qotildi | **QISMAN** | Timeout 25s ga oshirilgan va `APIConnectionError` joriy qilingan. Ammo botda bu xatolik FAQAT `bot/handlers/browsing.py` dagi 3 ta funksiyada tutib qolingan. `episode.py`, `search.py`, `catalog.py`, `translation_callback.py`, `start.py` va `code_resolver.py` da bu xatolik tutib qolinmagan va 500/502 server xatoliklari hamon `None` ga aylanib, foydalanuvchiga yolg'on "topilmadi" deb ko'rsatiladi. |
| **D4** | Bot va Backend `run.py` qayta ishga tushirildi va live bot yangi kodda ishlamoqda | **QISMAN** | `run.py` lokal Windows tizimida (PID 24468) ishga tushirilgan, Render da emas. Konfiguratsiyadagi haqiqiy username `@kinochi_mvp_bot` (Bot ID: 8865618534). Hisobotdagi `@MediaPlusOfficialBot` uning username'i emas, balki display name (First Name) dir. |
| **D5** | Barcha testlar to'liq o'tmoqda (`make check`, pytest) | **YOLG'ON** | `bot/tests/` 96 ta testdan o'tadi (`python -m pytest bot/tests/`). Biroq backend to'liq test suite'ida `run.py:116` dagi `while True: await asyncio.sleep(3600)` kodi sababli `test_bot_supervision_and_health.py::test_supervised_run_bot_retries_and_exits_nonzero` cheksiz CPU tsikliga tushib qoladi (hang). Shuningdek `test_alembic_migrations_clean_db.py` da nisbiy yo'l xatosi tufayli test yiqiladi (`alembic.util.exc.CommandError: Path doesn't exist: backend\alembic`). `make check` buyrug'i esa Windows da `make` utilitasi yo'qligi sababli ishlamaydi. |
| **D6** | Ish commit qilingan va loyiha xavfsiz git holatida | **YOLG'ON** | Ish `main` branchda emas, `filters/fix-all` branchida turibdi. 46 ta fayl bo'yicha jami **7,336 qator qo'shilgan va 6,044 qator o'chirilgan** o'zgarishlar commit qilinmasdan turibdi. C5 bo'yicha hech qanday git commit amalga oshirilmagan. |

---

## 2. Aniqlangan Kamchiliklar va Xatolar (Bugs)

### KAIJU-001: 5xx va Server Xatoliklari `None` ga Aylanib, Yolg'on "Topilmadi" Xatosi Chiqishi
- **Og'irlik darajasi:** `HIGH`
- **Fayl va qator:** `bot/services/api_client.py:51-53`, `bot/services/api_client.py:96-98`
- **Qadamlar:**
  1. Backend API 500 (Internal Server Error) yoki 502/503 qaytarganda `response.raise_for_status()` chaqiriladi.
  2. U `httpx.HTTPStatusError` tashlaydi, bu esa `except httpx.HTTPError:` blokida tutilib, to'g'ridan-to'g'ri `return None` qaytaradi.
  3. Bot handlerlari `None` ni 404 (kontent bazada yo'q) deb hisoblaydi va foydalanuvchiga `"⚠️ Bu kino topilmadi"` yoki `"⚠️ Bu qism topilmadi"` deb yolg'on xabar beradi.
- **Dalil:** `tests/audit_kaiju/test_k5_bot_error_handling.py::test_k5_api_client_500_swallowed_as_none` testi buni 100% isbotladi (PASSED).
- **Tavsiya:** `api_client` ichida HTTP 404 holatini aniq ajratib, 5xx server xatolarida `None` emas, balki `APIServerError` xatoligini ko'tarish va botda server xatosi haqida to'g'ri xabar berish.

---

### KAIJU-002: `callback.answer()` Chaqiruvining Kechikishi va Telegram Query Timeout Xavfi
- **Og'irlik darajasi:** `HIGH`
- **Fayl va qator:** `bot/handlers/browsing.py:35-39`, `bot/handlers/browsing.py:61-65`
- **Qadamlar:**
  1. Foydalanuvchi "1-qism" tugmasini bosadi.
  2. Handler darhol `await api_client.get_episode_by_code(code)` ni chaqiradi (timeout 25 soniya).
  3. `callback.answer()` esa `finally:` blokida — ya'ni so'rov to'liq tugagandan KEYIN chaqiriladi.
  4. Agar baza sovuq startda yoki tarmoq sekin bo'lsa (10-20 soniya), Telegram'ning callback query muddati tugaydi va Telegram `Bad Request: query is too old` xatosini tashlaydi.
  5. Foydalanuvchi ekranda tugma ustida aylanuvchi doira (spinner) qotib qoladi va foydalanuvchi javob kelmadi deb tugmani qayta-qayta bosadi.
- **Dalil:** `tests/audit_kaiju/test_k5_bot_error_handling.py::test_k5_callback_answer_delayed_after_api_call` testi buni isbotladi (PASSED).
- **Tavsiya:** `callback.answer()` chaqiruvini har doim og'ir I/O yoki API so'rovlaridan OLDIN bajarish kerak.

---

### KAIJU-003: `APIConnectionError` Faqat 3 ta Handlerda Tutilgan, Qolgan Barcha Handlerlar Himoyasiz
- **Og'irlik darajasi:** `HIGH`
- **Fayl va qator:** 
  - `bot/handlers/episode.py:16-19`
  - `bot/handlers/catalog.py:392-395`
  - `bot/handlers/search.py:142-148, 165-170`
  - `bot/handlers/translation_callback.py:32-35, 44-47`
  - `bot/utils/code_resolver.py:186, 211, 234, 240`
- **Qadamlar:**
  1. Foydalanuvchi qidiruvdan, katalogdan yoki to'g'ridan-to'g'ri `#code` yuborib qism ochganda `code_resolver` yoki `episode.py` ishlaydi.
  2. Ushbu fayllarda `APIConnectionError` uchun `try/except` mavjud emas.
  3. Natijada timeout yuz berganda `APIConnectionError` tutib qolinmaydi va xatolik dispatcherga chiqib ketadi yoki `None` qaytib, soxta "topilmadi" xabari chiqadi.
- **Dalil:** `code_resolver.py` va `bot/handlers/episode.py` kodlarida `APIConnectionError` import qilinmagan va tutilmagan.
- **Tavsiya:** Barcha bot handlerlariga yagona global middleware yoki `code_resolver` darajasida markazlashtirilgan timeout/connection error himoyasini kiritish.

---

### KAIJU-004: `run.py` dagi `while True: await asyncio.sleep(3600)` Sababli Test Suite Qotib Qolishi
- **Og'irlik darajasi:** `MEDIUM`
- **Fayl va qator:** `run.py:116-117`
- **Qadamlar:**
  1. `run.py` ichidagi `supervised_run_bot` da bot qayta ishga tushirish limitidan oshganda (`attempts >= max_attempts`) jarayon o'lmasligi uchun quyidagi kod yozilgan:
     ```python
     while True:
         await asyncio.sleep(3600)
     ```
  2. `backend/tests/test_bot_supervision_and_health.py` testi esa `asyncio.sleep` ni `AsyncMock` bilan almashtiradi (mock qiladi).
  3. `AsyncMock` darhol qaytgani sababli `while True:` cheksiz tsiklga aylanadi va 100% CPU sarflab, pytest jarayonini butunlay muzlatib qo'yadi.
- **Dalil:** `task-570` va `task-729` vazifalari aynan 89-testda (PID 42704, CPU 396s) qotib qolganligi terminal monitoringida isbotlandi.
- **Tavsiya:** `while True:` o'rniga bitta to'xtatuvchi `asyncio.Event()` kutish yoki tsikldan `return` orqali chiqish.

---

### KAIJU-005: Serial va Qismlar Keshining Invalidatsiya Qilinmasligi (`cache:episode:*`)
- **Og'irlik darajasi:** `MEDIUM`
- **Fayl va qator:** `backend/app/core/cache.py:147-156`, `backend/app/api/v1/series.py:566-660`
- **Qadamlar:**
  1. Admin yangi qism qo'shganda (`POST /seasons/{id}/episodes`), qismni yangilaganda (`PUT /episodes/{id}`) yoki o'chirganda (`DELETE /episodes/{id}`), `series.py` hech qanday kesh tozalash chaqiruvini bajarmaydi.
  2. Bundan tashqari, `app/core/cache.py:147` dagi `invalidate_media_cache("series")` faqat `cache:series:*` ni o'chiradi, lekin yangi kiritilgan `cache:episode:detail:*` kalitlarini o'chirmaydi.
  3. Oqibatda qism o'chirilsa yoki fayli yangilansa ham, 60 soniya davomida bot va foydalanuvchilar eski keshni ko'rib turadi.
- **Dalil:** `backend/app/api/v1/series.py` 566-660 qatorlarida `delete_cache_pattern` chaqiruvlari mavjud emas.
- **Tavsiya:** `create_episode`, `update_episode`, `delete_episode` endpointlariga `delete_cache_pattern("cache:episode:*")` va `delete_cache_pattern("cache:series:*")` chaqiruvlarini kiritish.

---

### KAIJU-006: Prod Ma'lumotlarini O'zgartirishda Zaxira Nusxa (Backup/Dump) Olinmaganligi
- **Og'irlik darajasi:** `MEDIUM`
- **Fayl va qator:** `<conversation_dir>/scratch/reindex_kaiju.py`
- **Qadamlar:**
  1. Agent live prod ma'lumotlar bazasida `DELETE FROM episodes` va `UPDATE episodes` buyruqlarini zaxira nusxasiz bajargan.
  2. Hech qanday `pg_dump` yoki vaqtinchalik backup jadvali (`CREATE TABLE episodes_backup_...`) yaratilmagan.
  3. Skript repoga kiritilmagan (faqat agentning shaxsiy scratch katalogida saqlangan).
- **Dalil:** `scratch/reindex_kaiju.py` da faqat `DELETE` va `UPDATE` mavjud, hech qanday snapshot yoki tranzaksion orqaga qaytarish logikasi yo'q.
- **Tavsiya:** Kelgusida prod bazadagi ma'lumotlarni o'zgartirishdan oldin har doim `pg_dump` yoki tegishli jadvallarning snapshot nusxasi olinishi shart.

---

### KAIJU-007: Bot Nomi va Identifikatsiyasi Chalkashligi (@MediaPlusOfficialBot vs @kinochi_mvp_bot)
- **Og'irlik darajasi:** `LOW`
- **Fayl va qator:** `bot/config.py`, C5 hisoboti matni
- **Qadamlar:**
  1. C5 agenti o'z hisobotida foydalanuvchiga botni `@MediaPlusOfficialBot` da tekshirishni yozgan.
  2. Aslida konfiguratsiyadagi `BOT_TOKEN` orqali `get_me()` tekshirilganda:
     - `Bot ID:` 8865618534
     - `Bot Username:` `@kinochi_mvp_bot`
     - `Bot First Name:` `MediaPlusOfficialBot`
- **Dalil:** `get_me()` xom natijasi: `Bot Username: kinochi_mvp_bot`.
- **Tavsiya:** Hisobotlarda va foydalanuvchi yo'riqnomalarida faqat haqiqiy username (`@kinochi_mvp_bot`) ko'rsatilishi kerak.

---

## 3. Foydalanuvchi Qo'lda Bajarishi Kerak Bo'lgan Amallar

1. **Telegram Botda Haqiqiy Username orqali Tekshirish:**
   - Botni `@MediaPlusOfficialBot` emas, balki rasmiy username `@kinochi_mvp_bot` orqali oching.
   - `/start` bosing va `s_1026` (Kaiju No. 8) hamda `s_1024` seriallarini ochib, qismlar tugmalari to'liq ketma-ketlikda (1..12) chiqayotganini ko'ring.
2. **Lokal `run.py` Jarayonini O'chirish (Agar Render deploy qilingan bo'lsa):**
   - Agar Render platformasida bot ishga tushirilgan bo'lsa, lokal kompyuterda `run.py` ni to'xtating (chunki bitta bot tokenida ikkita joydan polling qilinsa, `TelegramConflictError` yuz beradi).
3. **Git Branch Holatini Tartibga Solish:**
   - Hozirgi barcha ishlar `filters/fix-all` branchida commit qilinmasdan turibdi. Mustaqil tekshiruv xulosalariga ko'ra, tasdiqlangan qismlarni alohida atomik commit qilish lozim.

---

## 4. Yakuniy Qaror: SHARTLI (CONDITIONALLY ACCEPTED)

### Qaror Mezoni:
- **Nima uchun ISHONCHLI emas?** 
  - To'liq backend test suite qotib qolmoqda (`run.py` dagi infinite loop tufayli).
  - 5xx xatoliklar hali ham botda yolg'on "topilmadi" ga aylanmoqda.
  - `callback.answer()` kechikishi Telegram query timeout xavfini keltirib chiqarmoqda.
  - Barcha ishlar commit qilinmagan va noto'g'ri branchda turibdi.
- **Nima uchun ISHONCHSIZ emas?**
  - Kaiju No. 8 ma'lumotlari haqiqatan ham 100% to'g'ri tiklangan (12 ta qism, unikal fayllar, 24 daqiqalik davomiylik, 0 yetim yozuv).
  - SQL indeksli qidiruv prod DB da isbotlangan: so'rov 11.6 soniyadan **0.055 ms** ga tushgan.
  - Kesh orqali ma'lumot sizib chiqmasligi (`test_k2_admin_pending_series_does_not_leak_to_public`) va mavsumlararo o'tishlar (`test_k4`) to'liq isbotlangan va testlardan o'tgan.
- **Xulosa:**
  Kaiju No. 8 ma'lumotlar bazasi tuzatishi va asosiy SQL indeks tezlashuvi **MUVAFFAQIYATLI**. Biroq botdagi xatoliklarni boshqarish va test suite dagi qotib qolish sababli loyiha holati **SHARTLI (CONDITIONALLY ACCEPTED)** deb baholanadi.

---

## 5. Yangi Audit Testlari Ro'yxati (`tests/audit_kaiju/`)
Auditor tomonidan yaratilgan va loyihada saqlanadigan testlar:
1. `tests/audit_kaiju/test_k2_cache_security.py` — Admin pending keshining public foydalanuvchiga sizmasligi va 404 xatolar keshlanmasligi testi (PASSED).
2. `tests/audit_kaiju/test_k3_prod_explain.py` — Prod DB da `ix_episodes_code` indeksi, `EXPLAIN (ANALYZE)` va registr to'qnashuvi tekshiruvi.
3. `tests/audit_kaiju/test_k4_prev_next_episode.py` — 1-qism, oxirgi qism, mavsumlararo o'tish va bo'shliqli raqamlar bo'yicha navigatsiya testi (PASSED).
4. `tests/audit_kaiju/test_k5_bot_error_handling.py` — 500 xatosining None ga aylanishi va `callback.answer()` kechikishi testi (PASSED).
5. `tests/audit_kaiju/audit_k6_kaiju_data.py` — Prod DB va Telethon storage xabarlari (12 ta qism) to'liq audit skripti.
6. `tests/audit_kaiju/check_1024_storage.py` — s_1024 seriali qismlari storage audit skripti.
