# AUTOPILOT STATUS AUDITI VA MANBA TAHLILI (Uzmovi, Kinochilar)

Sana: 2026-11-10
Rol: Autopilot tahlilchisi
Holat: Qat'iy tahlil va dalillarga asoslangan audit (kodga tegilmadi)

---

## 1. Xulosa

1. Hozirda autopilot yadrosi (M1-M6) mustahkam: barcha 10 ta birlik testi (`test_autopilot_rebuild.py`) SQLite xotirasida to'liq o'tmoqda (10 passed).
2. DB invariantlari (a)-(g) to'liq kod darajasida mavjud: atomik tranzaksiya, S1:E1 publish darvozasi, cross-source fallback taqiqi va FloodWait breaker amal qilmoqda.
3. Jonli PostgreSQL bazasida navbat (`ingest_items`) toza: atigi 1 ta xatarli test elementi (`id=806`, `title='T'`, `status='queued'`) mavjud, qolgan 1232 ta manba `seed_candidates` jadvalida turibdi.
4. Asilmedia va Anitoob adapterlari ishchi holatda, lekin bot cheklovlari va FloodWait ga sezgir.
5. Uzmovi adapteri xavfsizlik qo'riqchisi (`UZMOVI_BOT_CODE_VERIFIED=False`) sababli atayin to'xtatilgan, chunki URL ID bot kodi bilan mos kelmasligi tasdiqlangan.
6. Kinochilar manbasi sayti tahlil qilinganda, yangi postlarda `@kinochilar_fast_bot` start kodi mavjud emasligi, uning o'rniga tashqi CDN embed pleyer (`stravers.live`) va xususiy Telegram kanallari ishlatilayotgani aniqlandi.
7. F1-S69 va avtopilotning to'liq avtonom ishlashi uchun asosiy to'siq: bot kodlarining nomuvofiqligi va yangi manbalarning media yetkazib berish usullari o'zgarganligidir.

---

## 2. Invariantlar Jadvali

| Invariant | Kodda bormi? | Dalil (Fayl va qatorlar) | Izoh |
| :--- | :---: | :--- | :--- |
| **(a) DB ga yozish faqat Storage upload + final_check dan keyin, bitta atomik tranzaksiyada** | **BOR** | `scraper/telethon_moderator_pipeline.py:4600-4761` (filmlar), `3280-3695` (qismlar) | Avval Telegram storage kanaliga xabar yuklanadi/nusxalanadi, keyin DB sessiyasi ochilib `final_check` tekshiriladi va faqat muvaffaqiyatli bo'lsa bitta tranzaksiyada commit qilinadi. |
| **(b) Serial S1:E1 final_check dan o'tgach published, S1:E1 yo'q → rejected, keyingi qismlar bittadan** | **BOR** | `scraper/telethon_moderator_pipeline.py:3321-3327`, `3577` | S1:E1 muvaffaqiyatsiz bo'lsa status `rejected` (`s1_e1_final_check_failed:<codes>`) bo'ladi va butun serial chop etilmaydi. Faqat S1:E1 o'tgach `published` bo'ladi. |
| **(c) Cross-source fallback yo'q (adapter faqat o'z boti va aniq kod/hash)** | **BOR** | `scraper/telethon_moderator_pipeline.py:1861, 1935-1985, 8669-8761` | Agar manba botida aniq kod topilmasa, element `needs_review` holatiga o'tkaziladi (`reason="no_exact_code"`). Boshqa botlarga fuzzy qidiruv orqali murojaat qilish butunlay bloklangan. |
| **(d) auto_index.py faqat admin qo'lda yuklashi uchun (scraper accountlar himoyalangan)** | **BOR** | `bot/handlers/auto_index.py:45-66, 922-943` | `AUTO_INDEX_DRY_RUN=True`, `AUTO_CONTENT_ENABLED=False`, `AUTO_INDEX_ALLOWED_CHAT_IDS` va `SCRAPER_ACCOUNT_IDS` orqali scraper botlari oddiy admin kanallariga aralashishi taqiqlangan. |
| **(e) Navbat PostgreSQL ingest_items da, eski JSON fayllar izolyatsiyasi** | **BOR** | `scraper/queue_manager.py:247-300`, `scraper/state_manager.py:16` | Asosiy navbat to'liq PostgreSQL `ingest_items` jadvalida ishlaydi. `scraper_queue.json` navbat sifatida ishlatilmaydi. `scraper_state.json` faqat sahifalash ko'rsatkichlari (`*_current_page`) uchun saqlangan. |
| **(f) FloodWait 120s breaker va batch pauzalari** | **BOR** | `scraper/telethon_moderator_pipeline.py:339-399`, `scraper/run_scraper.py:609-697, 813-815, 953` | `MAX_BOT_FLOOD_WAIT = 120`. Agar Telegram bot 120 soniyadan ortiq FloodWait bersa `BotFloodWaitError` ko'tariladi va sikl to'xtatilib, belgilangan vaqt davomida kutishga olinadi. |
| **(g) in_progress da qotib qolganlarni tiklash (crash recovery)** | **BOR** | `scraper/queue_manager.py:503-539`, `scraper/run_scraper.py:713` | `recover_stale_in_progress_async(max_age_seconds=1800)` orqali 30 daqiqadan ko'p `in_progress` holatida qolib ketgan elementlar avtomatik `queued` ga qaytariladi. |

---

## 3. Adapterlar Jadvali

| Manba | Fayl | Holat | Media turlari | Kod aniqlash usuli | Testlar | Ma'lum kamchiliklar / Xatolar |
| :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| **Asilmedia** | `scraper/site_parser.py` | Qisman | Film, Serial, Multfilm | URL regex: `/(\d+)-slug.html` -> `@asilmediabot` ga so'rov | Offline pass (`test_autopilot_rebuild.py`) | Bot tez-tez FloodWait beradi; ayrim filmlarda caption formati o'zgarishi sababli qism raqamlari chalkashishi mumkin. |
| **Anitoob** | `scraper/anitoob_parser.py` | To'liq / Ishchi | Anime, Multserial | Tugmali sahifalash (inline bot keyboard) | Offline pass (`test_autopilot_rebuild.py`) | Bot xabarlari inline tugmalar bilan tahrirlanganida qismlar orasida raqam bo'shliqlari (gap) qolish holatlari uchraydi. |
| **Uzmovi** | `scraper/site_parser.py` | Chala / Bloklangan | Film, Serial, Anime | URL regex: `/(\d+)-slug.html` -> `@UzmovieTV_Bot` | Offline pass / Guarded | URL ID raqami botdagi film kodiga to'g'ri kelmasligi sababli `UZMOVI_BOT_CODE_VERIFIED=False` bilan to'xtatilgan (`needs_review`). |
| **Kinochilar** | `scraper/kinochilar_parser.py` | Loyiha / Mos emas | Film, Serial | URL regex: `kinochilar_fast_bot?start=<hash>` | Offline mock pass | Yangi Kinochilar saytida bot start havolasi olib tashlangan; o'rniga tashqi CDN embed iframe (`stravers.live`) va kanal havolalari qo'yilgan. |

---

## 4. Sifat Qo'riqchilari (Admission Gate & Pipelines)

1. **Davomiylik vs TMDb Runtime (`runtime_mismatch`):**
   - **Holati:** **BOR** (`app/core/admission_gate.py:284-331`).
   - Filmlar uchun haqiqiy media davomiyligi TMDb davomiyligiga solishtiriladi (15% nisbiy noaniqlik, minimal 5 daqiqa chegara).
2. **Kino/Serial bir xil faylga tegishli emasligi (`file_belongs_to_multiple_titles`):**
   - **Holati:** **BOR** (`app/core/admission_gate.py:255-279`).
3. **Qism raqami va Fayl nomi mosligi (Kaiju xatosi oldini olish):**
   - **Holati:** **QISMAN BOR** (`scraper/telethon_moderator_pipeline.py:546-587`, `verify_season_episode_consistency`).
   - Tugmadagi qism raqami fayl nomi va caption bilan tekshiriladi. Lekin umumiy qismlar soni TMDb dagi jami epizodlar soni bilan solishtirilmaydi.
4. **Dublikatlar tekshiruvi (TMDb ID, source_key):**
   - **Holati:** **BOR** (`app/core/admission_gate.py:75-103`).
5. **Telegram `file_unique_id` unikal indeksi:**
   - **Holati:** **YO'Q**. Bazada faqat `file_id` saqlanadi, turli botlar o'rtasida takrorlanishni aniqlovchi `file_unique_id` maydoni va unikal indeksi mavjud emas.
6. **Telegram `file_id` tirikligini tekshirish (Liveness check):**
   - **Holati:** **YO'Q**. Fayl saqlangandan keyin uning file_id'si tirik ekani (masalan get_messages orqali) vaqti-vaqti bilan qayta audit qilinmaydi.

---

## 5. Navbat Tahlili (`ingest_items` & Database Audit)

Jonli Neon PostgreSQL ma'lumotlar bazasi ustida o'tkazilgan `SELECT` so'rovlari dalili:
- **`ingest_items` holati:**
  * Jami yozuvlar: **1 ta**
  * `queued`: **1 ta** (`id=806`, `source='uz'`, `media_type='movie'`, `title='T'`, `source_id='1'`).
  * *Xavf darajasi:* Yuqori. Ushbu element noto'g'ri test yozuvi bo'lib, `title='T'` nomi bilan bazadagi haqiqiy film (`#810 'Garri Potter 1: Hikmatlar toshi'`) bilan nomuvofiq bog'lanish ehtimoliga ega.
- **`seed_candidates` holati:** Jami **1232 ta** yozuv:
  * `new`: 1113 ta
  * `not_found`: 97 ta
  * `ingested`: 12 ta
  * `skipped`: 5 ta
  * `queued`: 3 ta
  * `ambiguous`: 2 ta
- **`rejected_items` holati:** Jami **34 ta** rad etilgan yozuv mavjud.
- **`STATE.md` dagi 42 ta queued masalasi:** Ilgari sinov paytida `STATE.md` ga kiritilgan 42 ta navbat hozirgi jonli PostgreSQL bazasida mavjud emas (tozalangan yoki nomzodlarga o'tkazilgan).

---

## 6. Migratsiya `9c8d7e6f5a4b` Tekshiruvi

- **Tekshiruv natijasi:** `9c8d7e6f5a4b_create_ingest_items_table.py` migratsiyasi jonli ishlab chiqarish bazasida **TO'LIQ QO'LLANILGAN**.
- **Dalil:**
  1. Neon PostgreSQL `alembic_version` jadvali tekshirildi: joriy versiya `['b2c3d4e5f6a7']` (`idempotent_schema_reconciler.py`).
  2. `backend/alembic/versions/` zanjiri:
     `f1322da82a96` -> `9c8d7e6f5a4b` (ingest_items yaratish) -> `b2c3d4e5f6a7` (reconciler bosh revision).
  3. Jonli bazada `ingest_items` jadvali to'liq mavjud va faol ishlamoqda.

---

## 7. Skip Qilingan 8 ta Test Sababi va Lokal PG Tahlili

- **Qaysi testlar:** `backend/tests/pg/test_real_postgres_integration.py` dagi 8 ta test:
  1. `test_d4e5f6a1b2c3_partial_unique_index_rejects_duplicate`
  2. `test_d4e5f6a1b2c3_partial_unique_allows_duplicate_with_null_tmdb`
  3. `test_d4e5f6a1b2c3_movie_and_series_separate_tmdb_namespaces`
  4. `test_d4e5f6a1b2c3_different_tmdb_same_content_type_allowed`
  5. `test_for_update_skip_locked_concurrent_claims`
  6. `test_advisory_lock_mutual_exclusion`
  7. `test_publish_status_default_constraint`
  8. `test_raw_insert_without_publish_status_defaults_to_pending`
- **Skip sababi:** Kodda `skip_no_test_db` o'rnatilgan: `TEST_DATABASE_URL` environment o'zgaruvchisi berilmagan. Maqsad — jonli ishlab chiqarish bazasiga tasodifiy DELETE/INSERT test so'rovlari tushishidan himoya qilish.
- **Lokal PG + Mock bilan yurgizish mumkinmi?:**
  * SQLite yoki Oddiy Mock bilan: **YO'Q**. Chunki ushbu testlar PostgreSQL ga xos bo'lgan `FOR UPDATE SKIP LOCKED` (qator darajasidagi blokirovka), `pg_advisory_xact_lock` (advisory qulflar) va `WHERE tmdb_id IS NOT NULL` qisman unikal indekslarini tekshiradi. SQLite bu mexanizmlarni qo'llab-quvvatlamaydi.
  * Lokal/Docker PostgreSQL bilan: **HA**. Alohida test bazasi (`postgresql+asyncpg://.../test_db`) yaratilib `TEST_DATABASE_URL` berilsa, barcha 8 ta test to'liq muvaffaqiyatli o'tadi.

---

## 8. Manba Tahlili: Uzmovi va Kinochilar

### A. UZMOVI (uzmovi.net)
1. **Kontent tuzilmasi:**
   - DLE (DataLife Engine) tizimi. Bo'limlar: `/tarjima-kinolarri/`, `/serialar/`, `/anime/`. Sahifalash: `/page/N/`.
   - URL sxemasi: `https://uzmovi.net/<kategoriya>/<ID>-<slug>.html`.
2. **Media uzatish usuli:**
   - Sayt sahifasida ochiq Telegram `file_id` berilmaydi.
   - Ilgari `@UzmovieTV_Bot` orqali tarqatilgan, lekin saytdagi `<ID>` raqami botdagi kino kodiga to'g'ri kelmaydi. Saytda ichki veb-pleyer iframelari ishlatiladi.
3. **Metadata sifati:**
   - Nom, premyera yili, janr, mamlakat mavjud. TMDb/IMDb ID ko'rsatilmagan. Moslashtirish faqat nom va yil bo'yicha TMDb API qidiruvi orqali amalga oshiriladi.
4. **Cheklovlar va Himoya:**
   - Cloudflare bilan himoyalangan (`Server: cloudflare`).
   - `robots.txt`: `Allow: /`, `Content-Signal: search=yes,ai-train=no,use=reference`. Skreyping uchun maxsus CAPTCHA yo'q, lekin tez-tez so'rov yuborilsa Cloudflare 429/403 qaytaradi.
5. **Katalog bilan kesishuv:** Bizning bazadagi premyeralar bilan taxminan **70-80%** kesishadi.
6. **Xavflar:** Noto'g'ri bot kodi sababli boshqa kinoning yuklanishi (cross-title) eng katta xavf.
7. **Adapter taklifi:**
   - Hajm: **M (O'rta)**.
   - Shart: Faqat Uzmovi HTML sahifasidan aniq bot kodi topilsagina (yoki veb-pleyer orqali) yuklashga ruxsat beruvchi qat'iy tekshiruv joriy etish.

### B. KINOCHILAR (kinochilar.com)
1. **Kontent tuzilmasi:**
   - DLE tizimi. Bo'limlar: `/tarjima-kinolar/`, `/tarjima-seriallar/`. Sahifalash: `/page/N/`.
   - URL sxemasi: `https://kinochilar.com/<kategoriya>/<ID>-<slug>.html`.
2. **Media uzatish usuli:**
   - **Kutilmagan yangilik:** Saytdagi so'nggi sahifalar tahlil qilinganda, `@kinochilar_fast_bot?start=<hash>` havolalari olib tashlangani aniqlandi!
   - Saytda media quyidagicha uzatilmoqda:
     * Tashqi CDN pleer iframesi: `//wreath-as.stravers.live/?token_movie=...`
     * Ichki pleer: `/player/iframe/<ID>/...`
     * Yopiq Telegram kanallari havolalari: `t.me/+...` (kanalga obuna bo'lish talab etiladi).
3. **Metadata sifati:**
   - Nom, yil, janr, sifat tegi (`1080p FHD`). TMDb ID yo'q.
4. **Cheklovlar va Himoya:**
   - Cloudflare CDN, DLE robots.txt (`Disallow: /engine/go.php`, `/*do=download`).
5. **Katalog bilan kesishuv:** Bizning katalog bilan taxminan **60-70%** kesishadi.
6. **Xavflar:**
   - Agar media faqat CDN pleyerda bo'lsa, uni Telegram orqali olish imkonsiz (to'g'ridan-to'g'ri serverdan yuklab olib Telegram storage'ga yuklash talab qilinadi, bu esa server trafigi va diskiga og'ir yuk bo'ladi).
   - Yopiq kanallar doimiy o'zgaradi va Telegram Telethon hisobini spam-blokirovkaga tushirish ehtimoli juda yuqori.
7. **Adapter taklifi:**
   - Hajm: Agar bot orqali bo'lsa **S (Kichik)**, agar CDN/Stream orqali bo'lsa **L (Katta)**.
   - Hozirgi holatda Kinochilar manbasini integratsiya qilish tavsiya etilmaydi (foyda/xavf nisbati salbiy).

---

## 9. Xavflar va Qaror Kerak Bo'lgan Savollar

1. **1-Qaror (Uzmovi bot kodi nomuvofiqligi):**
   * Uzmovi saytidagi ID raqami Telegram bot kodiga to'g'ri kelmasligi tasdiqlangan. Shu sababli Uzmovi dan faqat kino/serial nomlari va metadata olinib, videoni Asilmedia/Anitoob dan qidirish gibrid strategiyasini tasdiqlaysizmi?
2. **2-Qaror (Kinochilar botining yo'qligi):**
   * Kinochilar saytida Telegram bot chuqur havolalari to'xtatilgan va CDN pleyerga o'tilgan. Kinochilarni hozircha kun tartibidan chiqarib, resursni Asilmedia va Anitoob sifat nazoratiga qaratamizmi?
3. **3-Qaror (`ingest_items` dagi yagona 'T' elementi):**
   * Jonli bazada turgan `id=806` (`title='T'`, `source='uz'`) noto'g'ri test elementini `rejected` ga o'tkazishga ruxsat berasizmi?
