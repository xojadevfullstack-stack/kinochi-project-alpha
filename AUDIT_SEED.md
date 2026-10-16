# Mustaqil Audit Hisoboti: TMDb Seed Ingestor (Oltin Kolleksiya)

## Xulosaviy Statistikalar (Severity Counts)
- **CRITICAL**: 0
- **HIGH**: 1
- **MEDIUM**: 3
- **LOW**: 2
- **Jami Topilmalar**: 6 ta

---

## Topilmalar Ro'yxati (Xavflilik Darajasi Bo'yicha Saralangan)

### [SF-001] [HIGH] [FIXED: f10b2b7] Adversarial Qidiruvda Substring Mosligi Bo'yicha Soxta Ijobiy (False Positive) Natija
- **Status**: FIXED (Commit: `f10b2b7`)
- **Fayl va qator**: `scraper/tmdb_top_ingestor.py:146-148`
- **Kod parchasi**:
  ```python
  norm_scraped = to_slug(scraped_clean.get("title") or scraped_title)
  for st in seed_variants:
      norm_seed = to_slug(st)
      if norm_seed and len(norm_seed) >= 5:
          if norm_seed in norm_scraped or norm_scraped in norm_seed:
              return True, "Sarlavha qisman o'zak mos keldi"
  ```
- **Repro (Qayta takrorlash)**:
  1. `seed_title_en = "Drive"`, `seed_year = 2011`.
  2. Saytdan topilgan ma'lumot: `scraped_title = "G'azabli drayv / Drive Angry"`, `scraped_year = 2011`.
  3. Har ikkala film uchun `extract_part_number(...)` qiymati `1` qaytaradi.
  4. Chiqqan yili ikkalasida ham `2011` bo'lgani sababli yil tekshiruvidan o'tadi.
  5. `norm_seed` = `"drive"`, `norm_scraped` = `"drive-angry"`. `"drive" in "drive-angry"` sharti `True` qaytaradi.
  6. Yoki `scraped_year = None` bo'lgan holatda `Avatar: The Way of Water` (2022) filmi `Avatar` (2009) filmiga mos keladi (`p_seed=1`, `p_scraped=1`, `norm_scraped in norm_seed`).
  7. Agar manbadan faqat bitta nomzod qaytsa (`len(passing_candidates) == 1`), tizim uni avtomatik tasdiqlaydi (`status = 'found'`).
- **Kutilgan natija**: Qat'iy nom mosligi (aniq slug yoki stem tengligi) talab qilinishi yoki unvonlar orasida qo'shimcha so'zlar bo'lsa, `ambiguous` holatiga o'tishi kerak.
- **Amaldagi natija**: Substring qoidasi sababli boshqa film (masalan, Nicolas Cage'ning `Drive Angry` filmi) Ryan Gosling'ning `Drive` filmi o'rniga avtomatik qabul qilinadi.
- **Tuzatish**: Bo'sh substring qidiruvi olib tashlandi, faqat aniq slug va o'zak slug kesishmasi qoldirildi. `title_cleaner` ga `dublyaj` shovqin andozasi qo'shildi.

---

### [SF-002] [MEDIUM] [FIXED: 66e9df9] Bo'sh Sarlavha Holatida Blacklist So'rovi Barcha Yozuvlarga Mos Kelishi
- **Status**: FIXED (Commit: `66e9df9`)
- **Fayl va qator**: `scraper/tmdb_top_ingestor.py:180-185`
- **Kod parchasi**:
  ```python
  bl_res = await session.execute(
      select(BlacklistModel.id).where(
          or_(
              BlacklistModel.title.ilike(f"%{title}%"),
              BlacklistModel.url.ilike(f"%{tmdb_id}%")
          )
      ).limit(1)
  )
  ```
- **Repro (Qayta takrorlash)**:
  1. `title` o'zgaruvchisi bo'sh satr bo'lsa (`title = ""`), SQL so'rovi quyidagicha kompilyatsiya qilinadi:
     `lower(blacklist.title) LIKE lower('%%')`
  2. Ushbu shart `blacklist` jadvalidagi istalgan birinchi qatorga to'liq mos keladi (`True`).
  3. Natijada, agar bazada bittagina qora ro'yxat elementi bo'lsa ham, sarlavhasi bo'sh bo'lgan har qanday yangi nomzod noto'g'ri ravishda `Qora ro'yxatda (blacklist) mavjud` deb hisoblanadi va o'tkazib yuboriladi.
- **Kutilgan natija**: `if title and title.strip():` sharti orqali faqat bo'sh bo'lmagan sarlavhalar bo'yicha `ilike` tekshiruvi bajarilishi kerak.
- **Amaldagi natija**: Bo'sh sarlavha holatida SQL `LIKE '%%'` hosil bo'ladi.
- **Tuzatish**: `clean_title = (title or "").strip()` tekshiruvi qo'shildi va faqat nom bo'sh bo'lmagandagina `title.ilike` sharti orqali so'rovga qo'shilishi ta'minlandi.

---

### [SF-003] [MEDIUM] [FIXED: df06752] Admin Paneldan Qayta Qidiruv (Retry) `seed_candidates` Holatini Yangilamaydi
- **Status**: FIXED (Commit: `df06752`)
- **Fayl va qator**: `backend/app/api/v1/rejected.py:91-94` va `scraper/tmdb_top_ingestor.py:317-327`
- **Kod parchasi**:
  ```python
  # backend/app/api/v1/rejected.py:
  item.status = "resolved"
  item.updated_at = func.now()
  await db.commit()

  # scraper/tmdb_top_ingestor.py:
  query = select(SeedCandidateModel).where(
      or_(
          SeedCandidateModel.status == "new",
          and_(
              SeedCandidateModel.status == "not_found",
              SeedCandidateModel.last_searched_at <= retry_cutoff
          )
      )
  )
  ```
- **Repro (Qayta takrorlash)**:
  1. Bir nechta manba nomzodlari topilganda, `SeedCandidateModel.status = 'ambiguous'` qilinadi va `rejected_items` ga yoziladi.
  2. Admin interfeysida ushbu elementga "Retry" bosilganda, faqat `rejected_items.status = 'resolved'` bo'ladi.
  3. `SeedCandidateModel` jadvalidagi tegishli yozuv esa o'zgarishsiz `status = 'ambiguous'` holatida qoladi.
  4. `tmdb_top_ingestor.py --search` esa faqat `status == 'new'` yoki `status == 'not_found'` bo'lgan elementlarni qidiradi.
- **Kutilgan natija**: Admin qayta qidiruvni buyurganda, `SeedCandidateModel.status` ham `'new'` holatiga o'tishi va qayta qidiruvga tushishi kerak.
- **Amaldagi natija**: Nomzod `seed_candidates` jadvalida abadiy `ambiguous` holatida qoladi va qayta qidirilmaydi.
- **Tuzatish**: `retry_rejected_item` endpointida `source == 'tmdb_seed'` bo'lgan elementlar uchun `SeedCandidateModel` holati avtomatik ravishda `status='new'` va `attempts=0` ga qaytarilishi joriy qilindi.

---

### [SF-004] [MEDIUM] [FIXED: 4e849bc] Windows Konsolida Emojilar Sababli `UnicodeEncodeError` Yuzaga Kelishi
- **Status**: FIXED (Commit: `4e849bc`)
- **Fayl va qator**: `scripts/reset_media.py:66` va `scraper/tmdb_top_ingestor.py:300, 411, 434`
- **Kod parchasi**:
  ```python
  print("❌ [XAVFSIZLIK BLOKIROVKASI] Production muhitida ushbu skriptni ishga tushirish qat'iyan taqiqlanadi!")
  ```
- **Repro (Qayta takrorlash)**:
  1. Windows operatsion tizimi standart konsolida (`cp1251` yoki `cp866` kodirovkasi) skript ishga tushirilganda:
     `UnicodeEncodeError: 'charmap' codec can't encode character '\u274c' in position 0: character maps to <undefined>`
  2. Skript to'liq to'xtab qoladi (crash).
- **Kutilgan natija**: `sys.stdout.reconfigure(encoding='utf-8')` o'rnatilishi yoki xabarlarda standart ASCII prefikslari (`[ERROR]`, `[INFO]`, `[OK]`) ishlatilishi kerak.
- **Amaldagi natija**: UTF-8 reconfigure qilinmagan fayllarda emojilar xatolik keltirib chiqaradi.
- **Tuzatish**: `scripts/reset_media.py` va `scraper/tmdb_top_ingestor.py` fayllari boshida `sys.stdout` va `sys.stderr` uchun `utf-8` va `errors='replace'` bilan xavfsiz qayta konfiguratsiya o'rnatildi.

---

### [SF-005] [LOW] [FIXED: 94e0c04] Linter Ogohlantirishlari (E402 va Ishlatilmagan Importlar)
- **Status**: FIXED (Commit: `94e0c04`)
- **Fayl va qator**: `scraper/tmdb_top_ingestor.py:39-46`, `scripts/reset_media.py:30`
- **Kod parchasi**:
  ```python
  from sqlalchemy import select, func, and_, or_, text  # F401: text is unused
  from app.infrastructure.db.session import async_session_factory  # E402: import not at top of file
  ```
- **Repro (Qayta takrorlash)**:
  1. `ruff check scraper/tmdb_top_ingestor.py scripts/reset_media.py` buyrug'i bajarilganda 27 ta ogohlantirish qaytadi.
- **Kutilgan natija**: Ishlatilmagan importlar olib tashlanishi va importlar tartibi qoidalarga mos bo'lishi kerak.
- **Amaldagi natija**: Skript ishlashiga to'sqinlik qilmaydi, lekin linter ogohlantirishlari mavjud.
- **Tuzatish**: Ishlatilmagan importlar (`text`, `re`) olib tashlandi, CLI entrypointlari uchun `# ruff: noqa: E402` deklaratsiyasi qo'yildi.

---

### [SF-006] [LOW] [FIXED: 76812a6] `reset_media.py` Testlarida Guard 3 (Production Blokirovkasi) Alohida Test Qilinmagan
- **Status**: FIXED (Commit: `76812a6`)
- **Fayl va qator**: `backend/tests/test_reset_media_s8.py:1-92`
- **Repro (Qayta takrorlash)**:
  1. `test_reset_media_s8.py` faylida `execute=False` (Guard 1) va `execute=True, confirm="YES"` (Guard 2) sinovdan o'tkazilgan.
  2. Biroq `APP_ENV = "production"` bo'lganda skript haqiqatan ham bloklanishi bo'yicha alohida test yozilmagan.
- **Kutilgan natija**: Barcha 3 ta guard uchun alohida avtomatlashtirilgan test mavjud bo'lishi lozim.
- **Amaldagi natija**: Ishlash mantig'i mavjud bo'lsa-da, test qamrovi yetishmaydi.
- **Tuzatish**: `test_reset_media_s8.py` ga `test_s8_reset_media_guard_3_production_blocked` testi qo'shildi va `APP_ENV='production'` da skript to'xtatilishi tasdiqlandi.

---

## Nazorat Ro'yxati (Audit Checklist)

- [x] **1. Build vs claims**: `BUILD_PROGRESS_SEED.md` dagi barcha tasdiqlar git tarixi bilan solishtirildi. Har bir bosqich uchun commit va diff dalillari tasdiqlandi (S1: `33a75f5`, S2: `eb6ab85`, S3: `0947d3b`, S4/S5: `491204e`, S6: `e6cb2bf`, S7/S8: `755c4a7`, S9: `8890712`, S10: `1c04017`).
- [x] **2. Baseline**:
  - `compileall`: 0 ta xato, to'liq kompilyatsiya qilindi.
  - `pytest -rs`: 152 ta test o'tdi (152 passed, 0 skipped, 0 failed, 62 warnings).
  - Linter: `ruff` orqali tekshirildi, mavjud ogohlantirishlar qayd etildi (SF-005).
- [x] **3. Migration**:
  - Yagona bosh: `a1b2c3d4e5f6 (head)`.
  - Additivlik: Faqat `CREATE TABLE` va `CREATE INDEX`. Hech qanday `DROP/ALTER/DELETE` yo'q.
  - SQL ko'rinishi: `alembic upgrade f1a2b3c4d5e6:a1b2c3d4e5f6 --sql` to'liq xavfsiz DDL generatsiya qildi.
  - *Izoh*: `TEST_DATABASE_URL` mavjud bo'lmagani sababli, hard rule talabiga asosan real Neon tarmog'ida tekshirish talab etiladi (needs DB verification).
- [x] **4. Bypass scan**: `grep` orqali tahlil qilindi. `scraper/tmdb_top_ingestor.py` faqat `MovieModel` va `SeriesModel` bo'yicha `select` qiladi (dublikatlarni tekshirish uchun). Yangi yozuvlar faqat `SeedCandidateModel` va `RejectedItemModel` ga yoziladi. Nashr faqat `Admission Gate` orqali amalga oshiriladi.
- [x] **5. Matching quality**: 41 ta adversarial test juftligi sinovdan o'tkazildi:
  - Jami: 41 juftlik | To'g'ri Ijobiy (TP): 10 | To'g'ri Salbiy (TN): 25 | Soxta Ijobiy (FP): 2 | Soxta Salbiy (FN): 4.
  - 2 ta soxta ijobiy holat aniqlandi (`Drive` vs `Drive Angry` va nomsiz yilda `Avatar 2` vs `Avatar 1`) va [SF-001] sifatida qayd etildi.
- [x] **6. Filters and idempotency**:
  - `adult`, `vote_count >= 1000`, `vote_average >= 7.0` filtrlari to'liq ishlaydi.
  - Idempotent: `tmdb_id` bo'yicha mavjud bo'lsa qayta qo'shilmaydi.
  - `not_found` uchun 30 kunlik retry window (`SEED_NOT_FOUND_RETRY_DAYS=30`) tekshiriladi.
  - Bo'sh sarlavha uchun blacklist SQL defekti aniqlandi ([SF-002]).
- [x] **7. Rate limiting**:
  - `TMDbRateLimiter`: Asinxron token bucket (standart 10 req/s, burst 10).
  - 429 xatosi: `Retry-After` sarlavhasini o'qiydi va kutib qayta urinadi.
  - Per-source delay: `SEED_SEARCH_DELAY_SECONDS = 1.0` sozlangan.
  - Maxfiylik: API kaliti hech qachon loglarga va istisnolarga chiqmaydi (tasdiqlandi).
- [x] **8. Queue**:
  - `QueueManager.get_pending`: `priority` bo'yicha kamayish tartibida saralaydi (`priority=100` birinchi ishlanadi).
  - Eskirgan (eski formatdagi) navbat elementlari buzilmasdan ishlaydi (`priority=0` standart).
  - Dry-run: `self.qm.add_item` chaqirilmaydi, navbat fayli o'zgarmaydi.
- [x] **9. Gate integration**:
  - To'liq TMDb metadata payload bilan navbatga qo'yilgan element `pre_check` tekshiruvidan to'liq o'tadi.
  - Poster yoki treyler bo'lmaganda `missing_or_invalid_poster_url` / `invalid_trailer_url` defekti bilan rad etiladi.
  - Bir nechta mosliklar `rejected_items` ga tushadi, ammo admin qayta urinishi bo'yicha integratsiya defekti topildi ([SF-003]).
- [x] **10. start.bat**:
  - Bazani bir tugma bilan o'chirib yuborish (wipe) varianti yo'q.
  - `17) Enqueue EXECUTE`: Foydalanuvchidan klaviaturadan aniq `"YES"` deb yozishni talab qiladi.
  - `19) Reset`: Faqat DRY-RUN rejimida ishlaydi, real tozalash buyrug'ini matn sifatida ko'rsatadi.
- [x] **11. reset_media.py**:
  - Dry-run rejimi batafsil statistika beradi va hech narsani o'zgartirmaydi.
  - 3 ta guard mavjud: `--execute`, `--confirm YES`, `APP_ENV != production`.
  - `queued`, `ingested`, `skipped` holatlarini `new` ga qaytaradi, `not_found` saqlanadi.
  - Emojilar tufayli Windows konsolida xatolik aniqlandi ([SF-004]).
- [x] **12. Volume estimate (1000 filmlar + 500 seriallar)**:
  - **TMDb so'rovlari**: Ro'yxatlar uchun ~125 so'rov + to'liq metadata uchun ~800 so'rov = ~925 so'rov (~100 soniya).
  - **Manbalar qidiruvi**: 1500 nomzod * 6 so'rov = ~9,000 HTTP qidiruv so'rovi (1.0s tanaffus bilan ~75 daqiqa).
  - **Telegram yuklash hajmi (Filmlar)**: 600 ta film * 1.0 GB = **~600 GB tarmoq trafiki**.
  - **Telegram yuklash hajmi (Seriallar - XAVF)**: 200 ta serial * 25 qism = **5,000 ta qism!** 5,000 * 400 MB = **~2,000 GB (2 Terabayt!)**.
  - **FloodWait Xavfi**: Telegram MTProto orqali ketma-ket 5,000 ta video yuklash muqarrar ravishda ko'p soatlik `FloodWaitError` cheklovlariga olib keladi.
  - **Render 512MB RAM Xavfi**: Render bepul/starter instansiyasida 512MB RAM chegarasi mavjud. Telethon, video buferlar va FastAPI bir vaqtda ishlaganda OOM (Out Of Memory) crash kafolatlangan. Scraper faqat lokal mashinada ishlatilishi shart.
- [x] **13. Owner smoke tests**: Tizim egasi real manbalarda xavfsiz sinab ko'rishi uchun buyruqlar va mezonlar ishlab chiqildi.

---

## 13-Band: Tizim Egasi Uchun Xavfsiz Sinov (Owner Smoke Tests)

Ushbu sinovlar faqat o'qish (read-only) va sinov (dry-run) rejimida real TMDb hamda O'zbek manbalari bilan aloqani tekshirish uchun mo'ljallangan.

### Sinov 1: TMDb Ulanishi va Nomzodlarni Yig'ish (Read-Only)
```powershell
backend\.venv\Scripts\python.exe scraper/tmdb_top_ingestor.py --stats
backend\.venv\Scripts\python.exe scraper/tmdb_top_ingestor.py --build-seeds
```
- **Kutilgan natija**: `seed_candidates` jadvaliga 1000 ta film nomzodi yoziladi yoki avval bor bo'lsa `existing` deb ko'rsatiladi.
- **Isbotlovchi belgi**: Terminalda `[BUILD-SEEDS] Yakunlandi: ... ta yangi seed qo'shildi` xabari chiqadi.

### Sinov 2: Real Manbalardan 3 ta Film Qidirish (HYPOTHESIS)
*(Eslatma: Tashqi saytlarning real vaqtdagi holati HYPOTHESIS sifatida belgilanadi)*
```powershell
backend\.venv\Scripts\python.exe scraper/tmdb_top_ingestor.py --search --limit 3
```
- **Tekshiriladigan 3 ta film**:
  1. *Interstellar* (TMDb: 157336) -> Uzmovi/Asilmedia saytlarida `Yulduzlar aro` yoki `Interstellar` nomi bilan topilishi kutiladi.
  2. *Spirited Away* (TMDb: 129) -> Anime routing AniToob/Animeelar manbalariga yo'naltirishi kutiladi.
  3. *The Dark Knight* (TMDb: 155) -> Uzmovi/Asilmedia saytlarida topilishi kutiladi.
- **Isbotlovchi belgi**: Terminalda `🎯 [FOUND] TMDb ... -> [UZMOVI] ...` yoki `❌ [NOT FOUND]` xabarlari xatosiz chiqadi.

### Sinov 3: Navbatga Qo'yish (Faqat DRY-RUN)
```powershell
backend\.venv\Scripts\python.exe scraper/tmdb_top_ingestor.py --enqueue --limit 3
```
- **Kutilgan natija**: Hech qanday ma'lumot `scraper_queue.json` ga yozilmaydi.
- **Isbotlovchi belgi**: Terminalda `🔍 [DRY-RUN] Navbatga qo'shilar edi: ...` chiqadi, navbat fayli hajmi o'zgarmaydi.
