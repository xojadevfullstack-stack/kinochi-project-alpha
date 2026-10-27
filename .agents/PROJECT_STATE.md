# Kinochi Loyihasi Holati (Project State)

Ushbu hujjat loyihaning haqiqiy kod holatini aks ettiruvchi dolzarb context hujjatidir. (So'nggi yangilanish: **2026-10-27**, Faza F0 yakunlandi). AI va Dasturchilar uchun loyihaning arxitekturasi, mavjud yechimlari va joriy statusini saqlab turadi.

---

## 0. Joriy Rivojlanish Bosqichi: Faza F0 (Stabilization & Foundations) — YAKUNLANDI ✅

F0 bosqichida tizim poydevori to'liq mustahkamlandi, barcha 6 ta commit muvaffaqiyatli bajarildi:

1. **C0.1 (`00170bb`)**: `test(bootstrap): isolate env, add test db fixtures and freeze autopilot defaults`
   - Test muhitida `.env` fayli pydantic-settings orqali chetlab o'tildi (`Settings.model_config["env_file"] = None`).
   - Xavfsizlik filtri: `verify_safe_test_db` faqat `localhost` va `kinochi_v2_test` bazasiga ulanishga ruxsat beradi.
   - Autopilot flaglari va default holatlari muzlatildi.
2. **C0.2 (`d5fbaae`)**: `fix(alembic): merge dual heads into single head and add migration tests`
   - Ikkita shoxli Alembic versiyalari bitta bosh revisionga (`f1322da82a96`) birlashtirildi.
   - `c011ec7100`, `d012ec7201`, `e013ec7302` migratsiyalaridagi multi-statement `op.execute` lari asyncpg protokoli talabiga ko'ra ajratildi (100% semantik tenglik).
   - 5 ta xavfsiz migratsiya testlari (`backend/tests/test_alembic.py`) qo'shildi.
3. **C0.3 (`751486d`)**: `fix(db): asyncpg pooler-safe engine and configurable pool`
   - PgBouncer / Neon transaction pooler uchun xavfsiz sozlamalar (`statement_cache_size=0`, `prepared_statement_cache_size=0`, `prepared_statement_name_func`) joriy qilindi.
   - `DB_POOL_SIZE` (default 10) va `DB_MAX_OVERFLOW` (default 20) konfiguratsiyaga kiritildi.
4. **C0.4 (`a9a2948`)**: `perf(series): optimize series list query with lightweight pagination`
   - Seriallar ro'yxatida N+1 muammosi bartaraf etildi: `noload(SeriesModel.seasons, SeriesModel.pages)`.
   - `SeriesSummary` va `PaginatedSeriesSummaryResponse` DTO lar joriy qilindi. Ro'yxat so'rovlari soni 3 tadan oshmaydi.
5. **C0.5 (`47c46ec`)**: `fix(push): throttle new episode notifications with retry and cleanup`
   - Telegram orqali bildirishnomalar yuborishda 20 xabar/sekund (`0.05s`) cheklovi va har 500 tada `1.0s` pauza o'rnatildi.
   - `429 Too Many Requests` javobida `retry_after` bilan qayta urinish.
   - `403 Forbidden` holatida botni bloklagan foydalanuvchilar bazadan o'chiriladi.
   - Endpoint fon vazifasi (`BackgroundTasks.add_task`) yordamida zudlik bilan javob qaytaradi.
6. **C0.6 (`31bd515`)**: `chore(ci): configure CI with postgres service, bot tests, and full checks`
   - `.github/workflows/ci.yml` ga `postgres:17` servisi, Alembic tekshiruvi, backend testlari, bot testlari va website build/lint bosqichlari qo'shildi.
   - `TEST_DB_PORT` orqali CI da 5432, lokalda 5433 portlari xavfsiz boshqariladi.
   - Muhit yo'llari izolyatsiyalandi (`cd backend` va repo root bir xil ishlaydi).

### Frozen Baseline Statusi:
Backend testlarida aniq 3 ta muzlatilgan failure mavjud, yangi failure lar soni: **0**.
- `test_fix_f013_swallowed_exceptions.py::test_no_swallowed_exceptions_in_critical_modules`
- `test_seed_config_s2.py::test_seed_config_defaults`
- `test_seed_ingestor_full_s9.py::test_s9_build_seeds_filters_adult_and_low_votes_and_rating`
- **Jami backend:** 338 passed, 3 baseline failed, 8 skipped.
- **Jami bot:** 75 passed.
- **Website:** lint va production build muvaffaqiyatli (`✓ Compiled successfully`).

---

## 1. BACKEND (backend/)
**Holati: To'liq shakllangan, Clean Architecture qoidalarida ishlaydi.**

**1.1 Domain va Modullar:**
- `movies`: Alohida filmlar CRUD amallari.
- `series`: Seriallar arxitekturasi **filmlardan butunlay ajratilgan (decoupled)**. `Series -> Season -> Episode` iyerarxiyasida ishlaydi. Ro'yxat olish yengil `SeriesSummary` ga o'tkazilgan.
- `categories`: Janrlar va toifalar.
- `users`: Telegram bot orqali ro'yxatdan o'tganlar.
- `channels`: Majburiy obuna kanallari (Redis orqali tekshiriladi).
- `broadcasts`: Barcha foydalanuvchilarga xabar yuborish mexanizmi.
- `admin_users` / `auth`: JWT (Access/Refresh token) asosida ishlovchi admin avtorizatsiyasi.

**1.2 Alembic Migratsiyalar:**
- `alembic/versions/` papkasida yagona `f1322da82a96` bosh revision mavjud.
- Barcha kelgusi F1 migratsiyalari shu revision ustiga quriladi.

---

## 2. BOT (bot/)
**Holati: Funksional va Barqaror (75 ta test yashil).**

**2.1 Mexanizm va Funksiyalar:**
- **Polling / Web Server:** Bot Render.com da port band qilishi va o'chib qolmasligi uchun `main.py` da "dummy web server" bilan Polling rejimida ishlaydi.
- **Handlers:** `/start` deep-linking, qidiruv (`search`), seriallarni bosqichma-bosqich tanlash menyulari.
- **Middleware:** `subscription_check.py` majburiy kanallarga a'zolikni tekshiradi.
- **Kino berish:** Fayl ID lari backenddan keladi va bot Telegram serverlaridan videoni forward/copy qiladi.

---

## 3. ADMIN PANEL (admin-panel/)
**Holati: To'liq ishlayapti.**

---

## 4. WEBSITE (website/)
**Holati: To'liq SEO-optimallashtirilgan Katalog (Next.js 14).**
- SSR va avtomatlashtirilgan sitemap/robots generatsiyasi.
- Build va lint 100% yashil.

---

## 5. KEYINGI QADAM: FAZA F1 (V2 Schema & Enrichment)
- C1.1: `feat(db): additive v2 tables (persons, credits, terms)` (IF NOT EXISTS / inspector himoyasi bilan).
- C1.2: `feat(enricher): person/credit/term extraction from tmdb payload`.
- C1.3: `feat(api): detail response enrichment with persons, credits, terms`.
- C1.4: `test(enricher): regression tests for v2 schema and parser`.
