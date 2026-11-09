# 🕵️‍♂️ MUSTAQIL SENIOR QA & SECURITY AUDIT HISOBOTI (AUDIT_REPORT.md)

> **Loyiha:** MediaPlus / Kinochi (Cinema Streaming Ecosystem)  
> **Auditor:** Mustaqil Senior QA Engineer & Security Auditor  
> **Audit Sanasi:** 2026-11-10  
> **Boshlang'ich Git Tegi:** `audit-baseline` (`fcacbec`)  
> **Holat:** YAKUNIY TAHLIL VA DALILLAR JADVALI (Fix qilinmadi, faqat tekshirildi)

---

## 1. 📊 QAMROV VA TEKSHIRUV JADVALI (VERIFICATION MATRIX)

| Bo'lim | Band / Tekshiruv obyekti | Natija | Xom Dalil (Command / File:Line / Chiqish) |
| :--- | :--- | :--- | :--- |
| **0. Baseline** | 0.1 `git status`, `git log -30 --stat` | **PASS** | `git status`: 2 commit oldinda, 42 modified, 26 untracked. Baseline tag: `audit-baseline`. |
| | 0.2 Inventarizatsiya (skript bilan) | **PASS** | `inventory.py`: 195 ta FastAPI route, 14 ta bot routeri, 25 ta website sahifasi, 19 ta admin sahifasi, 49 ta env o'zgaruvchisi. |
| | 0.3 Test suite tahlili | **FAIL** | Backend: `518 passed, 3 failed, 10 skipped, 421 warnings in 61.49s`. Bot: `87 passed in 6.20s`. Test coverage: `53%` (ko'plab modullar 0-20%). |
| | 0.4 Frontend (website & admin-panel) | **FAIL** | Website: `tsc --noEmit` 0 xato, build PASS. Admin-Panel: `tsc --noEmit` **3 xato bilan YIQILDI**, `next build` FAIL bo'ldi. Hech birida test skripti yo'q. |
| | 0.5 Alembic zanjiri va drift | **FAIL** | Yagona head `b2c3d4e5f6a7`, `ingest_items` zanjirda bor. Ammo bo'sh DB da `upgrade head` **YIQILDI** (`collections` jadvali yo'qligi sababli). `alembic check` drift aniqladi. |
| **1. STATE.md** | 1.a Mutation Check (Worktree) | **PASS** | `..\kinochi-audit-worktree` da tekshirildi. `series.py` o'zgarishi qaytarilganda `test_fix_f006` va admin testlari yiqildi (bo'sh test emas). |
| | 1.b Ban Enforce (Backend vs Bot) | **FAIL** | Botda `BanCheckMiddleware` bor, ammo **Backend API da ban tekshiruvi yo'q** (`get_current_user` DB dan `is_banned` ni tekshirmaydi). |
| | 1.c Loop-bound Session Leak | **FAIL** | `queue_manager.py:256` da engine loopga bog'langan, ammo worker thread loopi yopilganda `null_engine.dispose()` chaqirilmaydi (socket leak). |
| | 1.d auto_index.py Race Condition | **PASS** | "GET max+1" race yo'q: qism raqami qat'iy ravishda captiondan regex orqali olinadi (`CAPTION_EPISODE_PATTERNS`) va `async with get_source_lock` orqali bloklanadi. |
| | 1.e Scraper holati & Checkpoints | **PASS** | Queue: PostgreSQL `ingest_items` da jonli. Checkpoints: `scraper_state.json` da. `SOURCE_MEDIA_TOTAL_PAGES` (anime: 3) dan oshganda tsikl cheksiz aylanmaydi, `break` qiladi. |
| **2. Backend** | Auth Matritsa & Himoyasiz Endpointlar | **FAIL** | CORS regex zaifligi: `kinochi-project-alpha-*.vercel.app` ixtiyoriy tajovuzkor Vercel domeniga ruxsat beradi. Banned user API ga kira oladi. |
| | publish_status izolyatsiyasi | **PASS** | Ommaviy o'qish yo'llari (`/movies`, `/series`) `publish_status='published'` ni qat'iy talab qiladi. |
| | Boundary & Pagination | **FAIL** | `page=0` va `page=-1` xato (422) qaytarmaydi, 200 OK beradi. `limit=10000000` esa 422 beradi. Global engine asyncpg event loop mismatch berdi. |
| | CRUD & Reyting Qayta Hisoblash | **PASS** | Oxirgi sharh o'chirilganda `func.avg()` `None` qaytaradi, `kinochi_rating=None`, `votes=0` (ZeroDivisionError yo'q). |
| | Fuzzy Search | **PASS** | `/api/v1/search/live?q=aka+uka` -> `Aka-uka Grimm ertaklari` (ID 1016) qaytadi. |
| **3. Bot** | Handlerlar va Deep Linking | **PASS** | `/start 1428`, `/start ep_...` to'g'ri ishlaydi, 87 ta bot testi yashil. |
| | Middleware va Ban | **FAIL** | `BanCheckMiddleware` `message` va `callback_query` ga ulangan, ammo **`inline_query` ga ulanmagan**! 60s kesh tufayli unban kechikadi. Fail-open siyosati tanlangan. |
| | FSM & /cancel | **FAIL** | `/cancel` komandasi mavjud emas! `ReviewStates.waiting_for_comment` holatida `/cancel` yozilsa, bu film sharhi sifatida bazaga yoziladi! |
| | Yagona Instansiya & Conflict | **FAIL** | `bot/main.py` da PID fayli yoki mutex/lock yo'q! Ikkinchi marta ishga tushirilsa `TelegramConflictError` beradi. |
| **4. Admin** | Sahifalar ochilishi | **FAIL** | `admin-panel/app/scraper/page.tsx` da 3 ta qattiq TypeScript xatosi bor, loyiha `next build` dan o'tmaydi. |
| | Sidebar havolalari | **PASS** | Sidebardagi barcha 15 ta havola real mavjud sahifalarga yo'naltirilgan. `series/[id]` qoldiqlari yo'q. |
| **5. Website** | ContinueWatching sinxronizatsiyasi | **FAIL** | Botda tarix tozalansa DB tozalanadi, ammo brauzerdagi `localStorage` tozalanmaydi. Saytda eski filmlar ko'rinishda davom etadi. |
| | Cinematic Red & Rang Qonuni | **FAIL** | STATE.md da'vosi YOLG'ON: `achievements`, `catalog`, `notifications`, `profile`, `subscriptions` sahifalarida `amber-*`, `text-rating-gold`, `bg-amber-400` keng qo'llangan. |
| **6. E2E** | QA Qabul Qilish Ro'yxati | **PARTIAL** | 8 ta banddan 5 tasi PASS, 3 tasi FAIL yoki chala (Banned user API bypass, continue watching localStorage qoldig'i, admin scraper build xatosi). |
| **7. Deploy** | Env & Konfiguratsiya | **FAIL** | `backend/.env.example` da 10 dan ortiq kod ishlatadigan o'zgaruvchilar (`GEMINI_API_KEY`, `KINOPOISK_API_KEY`, `SEED_*`, `AUTO_INDEX_*`) mavjud emas. |

---

## 2. 📑 STATE.md DA'VOLARI AUDITI (HYPOTHESIS VERIFICATION)

| № | STATE.md dagi Da'vo | Auditor Xulosasi | Xom Dalil va Haqiqiy Holat |
| :--- | :--- | :--- | :--- |
| 1 | *"Backend Test Suite: 504 passed, 17 failed (historical baseline & specific UI mock tests), 10 skipped"* | **QISMAN TO'G'RI / ESKIRGAN** | Haqiqiy yugurishda **518 passed, 3 failed, 10 skipped**. 17 ta xato yo'q, faqat 3 ta xato bor. 10 ta skipped esa `TEST_DATABASE_URL` yo'qligi va SQLite cheklovlari sababli. |
| 2 | *"Bot Test Suite: 87 passed in 8.86s"* | **TASDIQLANDI** | `cd bot; pytest tests/` buyrug'i 87 ta testni 6.20 soniyada 100% yashil o'tkazdi. |
| 3 | *"Website Frontend: website/node_modules/.bin/tsc --noEmit passed with 0 errors"* | **TASDIQLANDI (LEKIN CHALA)** | Website haqiqatan 0 xato bilan o'tadi, ammo Admin Panel qasddan yashirilgan: **Admin Panelda `tsc --noEmit` 3 ta xato bilan qulaydi**. |
| 4 | *"Database Migrations: Alembic current head is b2c3d4e5f6a7 (head)"* | **QISMAN TO'G'RI** | Bitta head mavjudligi to'g'ri, ammo **bo'sh bazada migratsiya `c011ec7100` da qulaydi** (`collections` jadvali yo'qligi sababli). Drift mavjud. |
| 5 | *"BanCheckMiddleware orqali bloklangan foydalanuvchilar to'liq to'xtatiladi"* | **YOLG'ON / XAVFLI** | Botda faqat `message` va `callback` to'xtatiladi (`inline_query` to'xtatilmaydi). **Backend API da esa ban tekshiruvi UMUMAN YO'Q**! Banned user token bilan barcha ma'lumotlarni o'zgartira oladi. |
| 6 | *"Barcha faol holatlar, asosiy tugmalar va hoverlar FAQAT Primary Red (#E50914) bo'lishi shart... Sariq rang faqat reyting yulduzchalarida qoldirilgan"* | **YOLG'ON** | Grep tekshiruvi `website/app/achievements`, `catalog`, `notifications`, `profile`, `subscriptions` sahifalarida o'nlab `amber-400`, `rating-gold` tugma, border va progress barlarni fosh qildi. |
| 7 | *"Bot profilidan Tarixni tozalash bosilganda bazadagi tomosha yozuvlari o'chadi va saytda Continue Watching bo'limi yangilanadi"* | **QISMAN TO'G'RI / CHALQITUVCHI** | DB da o'chadi, ammo sayt `localStorage` dagi guest yozuvlarni tozalay olmaydi. Sayt ochilganda `localStorage` dan yana o'sha filmlar yuklanadi. |
| 8 | *"Admin Panel Scraper Queue navbat ko'rinishi va cheksiz aylanuvchi spinner tuzatildi"* | **QISMAN TO'G'RI** | Mantiqiy kod yozilgan, ammo TypeScript type mismatch (`TS2345`, `TS2367`) tufayli admin panel production build qilib bo'lmaydigan holatda. |

---

## 3. 🐛 TOPILGAN XATOLAR VA ZAIFLIKLAR RO'YXATI (DEFECT LOG)

### 🔴 BUG-001: Backend API da Banned Foydalanuvchilarni Tekshirishning Mavjud Emasligi
* **Og'irlik:** **HIGH (Security Bypass)**
* **Komponent:** `backend/app/api/deps.py` (`get_current_user`)
* **Qadamlar:**
  1. Foydalanuvchi hisobiga tegishli token bilan `GET /api/v1/users/me/recommendations` yoki `POST /api/v1/reviews` ga so'rov yuborish.
  2. Foydalanuvchi bazada `is_banned = True` qilingan bo'lsa ham so'rov muvaffaqiyatli 200/201 qaytadi.
* **Kutilgan:** 403 Forbidden ("Hisobingiz ma'muriyat tomonidan bloklangan").
* **Haqiqiy:** 200 OK (`test_banned_user_can_still_access_protected_api` testi buni isbotladi).
* **Fayl:Qator:** `backend/app/api/deps.py:129-160`
* **Sabab (Gipoteza):** `get_current_user` faqat JWT ni dekod qiladi, DB dan foydalanuvchining `is_banned` holatini tekshirmaydi.
* **Tavsiya:** `get_current_user` ichida `session.execute(select(UserModel.is_banned)...)` tekshiruvi qo'shilsin yoki JWT revocation/ban check middleware joriy etilsin.

---

### 🔴 BUG-002: CORS Origin Regex Orqali Ixtiyoriy Vercel Subdomenlariga Ruxsat Berilishi
* **Og'irlik:** **HIGH (Security Vulnerability / Cross-Origin Data Leak)**
* **Komponent:** `backend/app/core/config.py` (`CORS_ORIGIN_REGEX`)
* **Qadamlar:**
  1. Hujumchi Vercel platformasida `kinochi-project-alpha-attacker.vercel.app` nomli ilova yaratadi.
  2. Foydalanuvchi brauzeridan `credentials: "include"` bilan backend API ga so'rov yuboradi.
  3. Backend so'rovni qabul qiladi va `Access-Control-Allow-Origin: https://kinochi-project-alpha-attacker.vercel.app` sarlavhasini qaytaradi.
* **Kutilgan:** Faqat rasmiy prod domenlar va aniq Vercel hashiga ega preview branchlarga ruxsat berilishi.
* **Haqiqiy:** `r"^https:\/\/(kinochi-project-alpha|kinochi-admin)(-[a-zA-Z0-9_-]+)?\.vercel\.app$"` regexi ixtiyoriy `-har_qanday_soz` qo'shimchasiga ruxsat beradi.
* **Fayl:Qator:** `backend/app/core/config.py:80`
* **Sabab (Gipoteza):** Regex Vercel preview deploymentlari uchun haddan tashqari keng (`(-[a-zA-Z0-9_-]+)?`) ochib yuborilgan.
* **Tavsiya:** Regex qat'iy Vercel team/project slugiga cheklansin yoki ruxsat etilgan domenlar faqat oq ro'yxat (`CORS_ORIGINS`) orqali berilsin.

---

### 🔴 BUG-003: Bo'sh Bazada Alembic Migratsiyasining Yiqilishi (`collections` Bog'liqligi)
* **Og'irlik:** **HIGH (Database / DevOps Blocker)**
* **Komponent:** `backend/alembic/versions/c011ec7100_add_collection_subscriptions_and_category_type.py`
* **Qadamlar:**
  1. Yangi bo'sh PostgreSQL bazasida `alembic upgrade head` buyrug'ini ishga tushirish.
* **Kutilgan:** Barcha 27 ta migratsiya ketma-ket muvaffaqiyatli bajarilib, head holatiga kelishi.
* **Haqiqiy:** `f1a2b3c4d5e6 -> c011ec7100` migratsiyasida `asyncpg.exceptions.UndefinedTableError: relation "collections" does not exist` xatosi bilan to'xtaydi.
* **Fayl:Qator:** `backend/alembic/versions/c011ec7100_*.py:28`
* **Sabab (Gipoteza):** `collections` jadvalini yaratuvchi DDL zanjirda `c011ec7100` dan oldin qo'shilmagan (u keyinchalik reconciler `b2c3d4e5f6a7` ga joylashtirilgan).
* **Tavsiya:** `collections` jadvalini yaratish migratsiyasi `c011ec7100` dan oldingi o'ringa ko'chirilsin yoki birlashtirilsin.

---

### 🔴 BUG-004: Admin Panel TypeScript Kompilyatsiyasi va Production Build Yiqilishi
* **Og'irlik:** **HIGH (Build / Deployment Blocker)**
* **Komponent:** `admin-panel/app/scraper/page.tsx`
* **Qadamlar:**
  1. `cd admin-panel; npx tsc --noEmit` yoki `npm run build` buyrug'ini bajarish.
* **Kutilgan:** 0 errors, muvaffaqiyatli production bundle.
* **Haqiqiy:** 3 ta qattiq TypeScript xatosi (`TS2345`, `TS2367`) sababli build to'xtaydi:
  * `app/scraper/page.tsx(533,122): error TS2345: Argument of type 'string | undefined' is not assignable to parameter of type 'string'.`
  * `app/scraper/page.tsx(4631,54): error TS2367: This comparison appears to be unintentional ("published" has no overlap).`
  * `app/scraper/page.tsx(4957,57): error TS2367: This comparison appears to be unintentional ("queued" has no overlap).`
* **Fayl:Qator:** `admin-panel/app/scraper/page.tsx:533, 4631, 4957`
* **Sabab (Gipoteza):** F1-S68 slaysida statuslar tipi (`"pending"` vs `"queued"`) va `editingItem.media_type` ning `undefined` bo'lishi e'tiborga olinmagan.
* **Tavsiya:** Tiplar unioniga `"published"` va `"queued"` qo'shilsin va optional chaining (`editingItem?.media_type || ""`) berilsin.

---

### 🟡 BUG-005: Telegram Botda `/cancel` Komandasining Yo'qligi va FSM Sharh Tutqichi
* **Og'irlik:** **MEDIUM (UX & Functional Defect)**
* **Komponent:** `bot/handlers/reviews.py`
* **Qadamlar:**
  1. Foydalanuvchi botda filmga baho qo'yadi (bot "Fikringizni yozing" holatiga o'tadi).
  2. Foydalanuvchi fikridan qaytib `/cancel` yoki `/start` yuboradi.
* **Kutilgan:** Bot FSM holatidan chiqishi va jarayon bekor qilinishi.
* **Haqiqiy:** Bot `/cancel` so'zini sharh deb qabul qilib, bazaga film sharhi sifatida saqlaydi!
* **Fayl:Qator:** `bot/handlers/reviews.py:316-322`
* **Sabab (Gipoteza):** Botda global `/cancel` yoki `Command("cancel")` handleri registratsiya qilinmagan.
* **Tavsiya:** FSM holatlarini bekor qiluvchi global `/cancel` handleri va `state.clear()` qo'shilsin.

---

### 🟡 BUG-006: Telegram Botda Yagona Instansiya (Single Instance Lock) Himoyasining Yo'qligi
* **Og'irlik:** **MEDIUM (Operational Stability)**
* **Komponent:** `bot/main.py`
* **Qadamlar:**
  1. `python bot/main.py` ni birinchi terminalda yoqish.
  2. `python bot/main.py` ni ikkinchi terminalda yoqish.
* **Kutilgan:** Ikkinchi jarayon "Bot allaqachon ishlayapti" deb xavfsiz to'xtashi.
* **Haqiqiy:** Ikkala jarayon ham Telegram API ga ulanadi va uzluksiz `TelegramConflictError` tashlab, inline query va xabarlarni yo'qotadi.
* **Fayl:Qator:** `bot/main.py:25`
* **Sabab (Gipoteza):** `run_scraper.py` da `ScraperCliLock` mavjud bo'lsa-da, `bot/main.py` da hech qanday fayl yoki PID qulfi yo'q.
* **Tavsiya:** `bot/main.py` ishga tushishida `.bot.pid` yoki filelock mexanizmi joriy etilsin.

---

### 🟡 BUG-007: BanCheckMiddleware `inline_query` Voqealariga Qo'llanmaganligi
* **Og'irlik:** **MEDIUM (Security Inconsistency)**
* **Komponent:** `bot/main.py`
* **Qadamlar:**
  1. Bloklangan foydalanuvchi Telegram chatida `@kinochi_mvp_bot kino_nomi` deb inline qidiruv yozadi.
* **Kutilgan:** Foydalanuvchiga qidiruv natijalari ko'rsatilmasligi yoki bloklanganligi bildirilishi.
* **Haqiqiy:** Natijalar ko'rsatiladi, chunki `dp.inline_query.middleware(BanCheckMiddleware())` registratsiya qilinmagan (faqat `message` va `callback_query` ga ulangan).
* **Fayl:Qator:** `bot/main.py:31-35`
* **Sabab (Gipoteza):** Middleware ro'yxatiga `dp.inline_query` kiritilishi unutilgan.
* **Tavsiya:** `dp.inline_query.middleware(BanCheckMiddleware())` qo'shilsin.

---

### 🟡 BUG-008: Ephemeral Thread Loopda `null_engine` Resurslarining Oqishi (Socket Leak)
* **Og'irlik:** **MEDIUM (Resource Leak)**
* **Komponent:** `scraper/queue_manager.py` (`_run_coro_sync`)
* **Qadamlar:**
  1. Sinxron kontekstdan `qm.stats()` yoki `qm.get_pending(...)` 100 marta chaqiriladi.
* **Kutilgan:** Ulanishlar to'liq yopilishi (`engine.dispose()`).
* **Haqiqiy:** Har safar `new_loop` ochilib yopiladi, ammo unga bog'langan `null_engine` dispose qilinmaydi va xotirada ulanish rozetkalari ochiq qoladi.
* **Fayl:Qator:** `scraper/queue_manager.py:209-223`
* **Sabab (Gipoteza):** `finally` blokida faqat `new_loop.close()` chaqirilgan, ammo `factory.kw['bind'].dispose()` chaqirilmagan.
* **Tavsiya:** Thread loop yopilishidan oldin unga bog'langan engine dispose qilinsin.

---

### 🟡 BUG-009: Cinematic Red Standartining Ommaviy Buzilishi (Amber/Yellow Qoldiqlari)
* **Og'irlik:** **MEDIUM (Design Standard Violation)**
* **Komponent:** `website/app/achievements/page.tsx`, `catalog/page.tsx`, `notifications/page.tsx`, `profile/page.tsx`, `subscriptions/page.tsx`
* **Qadamlar:**
  1. Ko'rsatilgan sahifalarni ochish va UI elementlarini ko'zdan kechirish.
* **Kutilgan:** Sariq rang faqat IMDb/Kinopoisk reyting yulduzchalarida bo'lishi, qolgan barcha narsalar Cinematic Red bo'lishi.
* **Haqiqiy:** Yutuqlar kartalari, bildirishnoma piktogrammalari, toifa aksentlari, akkaunt doiralari va obuna badgelari sariq/amber rangda porlab turibdi.
* **Fayl:Qator:** `website/app/achievements/page.tsx:141-358`, `website/app/catalog/page.tsx:26-27`, `website/app/subscriptions/page.tsx:86`
* **Sabab (Gipoteza):** Slayslarda faqat asosiy `page.tsx` va kartochka qisman tuzatilgan, qolgan sahifalar e'tibordan chetda qolgan.
* **Tavsiya:** Barcha `amber-*` va no-rating `rating-gold` sinflari Cinematic Red (`#E50914`, `primary-*`) bilan almashtirilsin.

---

### 🔵 BUG-010: Saytda "Tarixni tozalash"ning Chala Ishlashi (`localStorage` Desinxronizatsiyasi)
* **Og'irlik:** **LOW (Data Consistency / UX)**
* **Komponent:** `website/components/home/ContinueWatchingSection.tsx`
* **Qadamlar:**
  1. Foydalanuvchi saytda mehmonga o'xshab bir nechta film tomosha qiladi (yoki sayt ularni `localStorage` ga yozadi).
  2. Bot orqali profiliga kirib "Tarixni tozalash" ni bosadi.
  3. Saytga qaytib bosh sahifani yangilaydi (F5).
* **Kutilgan:** "Ko'rishni davom ettirish" bo'limi bo'sh bo'lishi.
* **Haqiqiy:** Sayt `localStorage.getItem("mediaplus_continue_watching")` dagi eski filmlarni yana ekranga chiqaradi.
* **Fayl:Qator:** `website/components/home/ContinueWatchingSection.tsx:76-116`
* **Sabab (Gipoteza):** Bot faqat server DB sini tozalay oladi, brauzerning ichki `localStorage` siga kira olmaydi. Sayt esa ikkala manbani birlashtiradi.
* **Tavsiya:** Agar foydalanuvchi tizimga kirgan bo'lsa va serverdagi tarixi 0 bo'lsa, `localStorage` dagi eski yozuvlar ham tozalansin yoki ustuvorlik serverga berilsin.

---

## 4. 📈 TEST STATISTIKASI VA QAMROV (COVERAGE REPORT)

### A. Testlar Soni Solishtirmasi
* **Audit Boshida:**
  * Bot: 87 passed.
  * Backend: 518 passed, 3 failed, 10 skipped.
  * Frontend: 0 ta avtomatlashtirilgan test (hech qanday test kutubxonasi yoki skripti ulanmagan).
* **Audit Davomida tests/audit/ ga Yozilgan Yangi Testlar:**
  1. `tests/audit/inventory.py`: Butun tizim (FastAPI, Bot, UI, Env) to'liq inventarizatsiyasi.
  2. `tests/audit/test_security_and_auth_matrix.py`:
     * `test_banned_user_can_still_access_protected_api` -> **PASSED** (Banned user API zaifligini isbotladi).
     * `test_cors_origin_regex_vulnerability` -> **PASSED** (CORS tajovuzkor Vercel domenini tasdiqladi).
     * `test_input_validation_boundary_pagination` -> **FAILED** (Asyncpg cross-loop runtime xatosini fosh qildi).

### B. Backend Kod Qamrovi (Coverage: 53%)
* **0% Qamrovdagi modullar (Umuman test qilinmagan):**
  * `backend/app/domain/admin_users/entities.py` (0%)
  * `backend/app/core/franchise_canon.py` (0%)
* **O'ta past qamrovdagi modullar (< 35%):**
  * `backend/app/infrastructure/telegram/telegram_client.py` (7% — 424 qator test qilinmagan)
  * `backend/app/core/watch_history.py` (15%)
  * `backend/app/core/recommendations.py` (20%)
  * `backend/app/infrastructure/db/repositories/broadcast_repo.py` (23%)
  * `backend/app/infrastructure/db/repositories/channel_repo.py` (26%)
  * `backend/app/infrastructure/db/repositories/user_repo.py` (30%)
  * `backend/app/infrastructure/db/repositories/movie_repo.py` (32%)
  * `backend/app/core/reviews.py` (34%)
  * `backend/app/infrastructure/db/repositories/series_repository.py` (34%)
* **Frontend Test Qamrovi:** **0%** (Playwright yoki Jest o'rnatilmagan/sozlanmagan).

---

## 5. ✅ ISBOTLANGAN VA ISHLAYOTGAN TIZIM QISMLARI

1. **Telegram Bot Asosiy Oqimi:** `/start`, `/start {code}`, raqamli va shortuuid kodlarni ajratish, 87 ta avtotest to'liq yashil.
2. **Fuzzy Search:** Tire, bo'sh joy va tinish belgilariga nisbatan qidiruv bardoshliligi (`aka-uka` == `aka uka`) to'liq ishlaydi.
3. **Sharhlar Reytingini Qayta Hisoblash:** Sharh qo'shilganda yoki admin tomonidan o'chirilganda o'rtacha reyting tranzaksiya ichida to'g'ri qayta hisoblanadi (bo'sh qolganda nolga bo'lish xatosi yo'q).
4. **Auto-Index Sequential Lock:** Telegramdan kelayotgan qismlar `get_source_lock` orqali tartiblanadi, read-modify-write poygasi yo'q.
5. **Website Asosiy Sahifa Renderingi:** Next.js 14 production build muvaffaqiyatli o'tadi, ambient fon treyleri va marquee chegaralari ishchi holatda.
6. **Lokal PostgreSQL Xavfsizligi:** `localhost:5433/kinochi_v2_test` bazasida real postgres testlari (8 ta) 100% yashil o'tdi, Neon yoki prod tegilmadi.

---

## 6. ⚠️ TEKSHIRIB BO'LMAGAN BANDLAR VA SABABLARI

1. **Production Render Webhook & Upstash Redis:** Audit qoidasiga (Production'ga tegmaslik) ko'ra jonli Render serveriga so'rov yuborilmadi va tirik botlar to'xtatilmadi.
2. **Telethon Jonli MTProto Yuklash:** Haqiqiy Telegram akkaunti va donor botlardan video tortish boshlanmadi (F1-S69 taqiqlanganligi sababli).
3. **Playwright Brauzer End-to-End Sinovlari:** Muhitda brauzer binarlari o'rnatilmaganligi va test scripti yo'qligi sababli brauzer testlari API darajasida simulyatsiya qilindi.

---

## 7. 🛠️ TAVSIYA ETILADIGAN TUZATISH TARTIBI (FIX ROADMAP)

1. **1-Bosqich (CRITICAL & HIGH Xavfsizlik):**
   * `BUG-001`: `get_current_user` ichiga `is_banned` tekshiruvini qo'shish (Banned userlar zudlik bilan API dan uziladi).
   * `BUG-002`: `CORS_ORIGIN_REGEX` ni qat'iylashtirish (Begona Vercel domenlarining token o'g'irlash xavfi bartaraf etiladi).
2. **2-Bosqich (HIGH Build & Baza):**
   * `BUG-004`: `admin-panel/app/scraper/page.tsx` dagi 3 ta TypeScript xatosini to'g'rilash (Admin panel build qilinadigan bo'ladi).
   * `BUG-003`: Alembic `c011ec7100` migratsiyasida `collections` bog'liqligini tuzatish (Noldan boshlab deploy qilish imkoniyati tiklanadi).
3. **3-Bosqich (MEDIUM Bot & Tizim Barqarorligi):**
   * `BUG-005`: Botga `/cancel` komandasini qo'shish va FSM holatidan chiqishni ta'minlash.
   * `BUG-006`: `bot/main.py` ga yagona instansiya (PID fayl / FileLock) qo'shish.
   * `BUG-007`: `BanCheckMiddleware` ni `inline_query` ga ham ulash.
   * `BUG-008`: `queue_manager.py` da ephemeral loop yopilganda engine'ni dispose qilish.
4. **4-Bosqich (Dizayn va Qoidalar):**
   * `BUG-009`: `achievements`, `catalog`, `notifications`, `profile`, `subscriptions` sahifalaridagi sariq ranglarni Cinematic Red (`#E50914`) ga o'tkazish.
   * `BUG-010`: `ContinueWatchingSection` da serverda tarix bo'sh bo'lganda `localStorage` ni tozalash mexanizmini kiritish.

---
*Hisobot to'liq dalillar asosida yakunlandi. Asosiy kodga hech qanday o'zgartirish kiritilmadi.*
