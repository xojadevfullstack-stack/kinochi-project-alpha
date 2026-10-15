# Kinochi Project — Build & Refactor Progress

Ushbu hujjat loyihadagi barcha bosqichlar, arxitekturaviy qarorlar va bajarilgan commits ketma-ketligini qayd etadi.

## Bajarilgan bosqichlar (Tarix)
- [x] **Stage 1 (FloodWait)**: `scraper/run_scraper.py` va `queue_manager.py` da FloodWait retry (max 3 ta) hamda 30 daqiqalik stale recovery qo'shildi. Commit: `2eaaeef`
- [x] **Stage 2 (JSON out of git)**: `scraper_queue.json`, `scraper_state.json`, `quarantine_items.json` git indeksidan chiqarildi, `FileLock` va avtomatik bo'sh holat yaratish joriy qilindi. Commit: `12952fb`
- [x] **Stage 3 (publish_status boshlang'ich kodi)**: `MovieModel` va `SeriesModel` ga `publish_status` ustuni, Alembic migratsiya fayli, asosiy repo va servis filtrlari qo'shildi. Commit: `89333e2`

---

## CHECKLIST

### [A] Finish publish_status (ships together with the gate)
- [x] **A1**. Migratsiya `b3a1c2d4e5f6`: `ADD COLUMN ... DEFAULT 'published' NOT NULL` saqlanadi (mavjud qatorlar ochiq qoladi), so'ngra shu migratsiyaning o'zida `movies` va `series` uchun `ALTER COLUMN ... SET DEFAULT 'pending'` qilinadi. Modellar: `default='pending'`, `server_default='pending'`. Gate'ni aylanib o'tgan har qanday insert `'pending'` (ko'rinmas) bo'lib tushadi. Commit: `9ca99f3`
- [x] **A2**. O'qish yo'llaridagi barcha ochiq teshiklarni yopish:
  - `recommendations.py:93-120` va `133-140` (recommendations + trending)
  - `series.py:273` (`seasons/{id}`)
  - `series.py:365` + `series_repository.py:280-318` (`episodes/code/{code}` va barcha episode lookup lari)
  - mavsum/qism ID orqali olinadigan barcha public endpointlar
  - bot inline rejimi
  - *Qoida*: media/mavsum/qismning ommaviy o'qilishi uning ota `publish_status == 'published'` bo'lishini talab qiladi.
  - *Filtrsiz qoladiganlar*: faqat `by-source` lookup (`auto_index`), admin/audit endpointlar, scraper dedupe, foydalanuvchining shaxsiy `watch_history` si. Commit: `0c6c979`
- [x] **A3**. Barcha ad-hoc filtrlar o'rniga bitta yagona yordamchi helper (`published_only(stmt, Model)`) qo'llanilishi. Test: barcha `/api/v1` yo'nalishlarini tekshirib, har bir public yo'l pending/hidden ma'lumotlarni yashirishini assert qilish. Commit: `0c6c979`
- [x] **A4**. Redis kesh kalitlari `publish_status` filtrini hisobga olishi va status o'zgarganda kesh tozalanishi. Commit: `0c6c979`

### [B] Admission gate + rejected_items
- [x] **B1**. Migratsiya + model `rejected_items`:
  - Maydonlar: `id`, `media_type` ('movie'/'series'/'episode'), `source`, `source_key`, `title`, `payload` JSONB, `defects` JSONB (list of `{field, code, message}`), `media_id` NULL, `attempts` int default 1, `status` ('rejected','resolved','blacklisted'), `created_at`, `updated_at`.
  - `UNIQUE(source, source_key)`; takroriy urinishda `attempts += 1` va payload yangilanadi. (needs DB verification) Commit: `69255c8`
- [x] **B2**. Yagona umumiy modul `admission_gate` (backend va scraper bir xil kodni import qiladi, mantiq takrorlanmaydi):
  - `pre_check(kind, payload)` va `final_check(kind, media)`.
  - Yagona konfiguratsiya (`REQUIRED_FIELDS`).
  - Tashqi ID qoidasi (TMDb / Shikimori).
  - Reachability (poster, trailer HEAD tekshiruvi).
  - Dublikatlar (tmdb_id/shikimori_id, so'ng normalizatsiyalangan nom+yil, `rejected_items` va blacklist).
  - Qism (episode) tekshiruvlari.
  - Holat mashinasi (State machine): `pre_check` -> `pending` row -> video biriktirish -> `final_check` -> faqat gate ichida `published`. Commit: `01b0620`
- [x] **B3**. BARCHA yozish yo'llarini gate orqali yo'naltirish (API, auto_index, scraper moderator pipeline, ingest_pusu). Commit: `0b96e6c`
- [x] **B4**. Non-blocking pipeline, CircuitBreaker faqat infratuzilma xatolarida to'xtashi, Autopilot `rejected`/`blacklisted` elementlarni qayta navbatga qo'ymasligi. Commit: `d2d8aed`

---

## Qarorlar (Decisions Log)
- **D1 (DB Isolation)**: `TEST_DATABASE_URL` mavjud bo'lmaganda, ishlab chiqarish (production) bazasiga tegilmaydi. Barcha migratsiyalar `alembic upgrade --sql` orqali static preview bilan tekshirilib, "needs DB verification" belgisi qo'yiladi.
- **D2 (Atomic Rollout)**: Bosqich 3 (`publish_status`) va Bosqich 4 (`admission_gate`) o'zaro bog'liq bo'lgani sababli, production xavfsizligi uchun bitta release sifatida taqdim etiladi. Yangi yozuvlar qat'iy `pending` ga tushadi va faqat Gate tekshiruvidan so'ng `published` bo'ladi.
