# 🛠️ MediaPlus / Kinochi — QA & Security Bug Fix Hisoboti (FIX_REPORT.md)

> **Loyiha:** MediaPlus / Kinochi  
> **Mas'ul Injener:** Senior Backend & Fullstack Engineer  
> **Sana:** 2026-11-10  
> **Boshlang'ich Git Tegi:** `audit-baseline` (`fcacbec`)  
> **Qoida:** Har bir tuzatish (RED -> Fix -> GREEN) xom test dalillari bilan isbotlanadi.

---

## 1. 📋 TUZATISHLAR JADVALI (BUG FIX MATRIX)

| BUG-ID | Og'irlik | Komponent | Holat | Commit Hash | Test Fayli va Nomi |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BUG-001** | CRITICAL | Backend API (`deps.py`) | **TUZATILDI** | `18510b7` | `backend/tests/test_banned_user_blocked_api.py::test_banned_user_is_strictly_blocked_with_403` |
| **BUG-002** | HIGH (Sec) | Backend Core (`config.py`) | **TUZATILDI** | `4a5d3c9` | `backend/tests/test_cors_regex_security.py::test_cors_attacker_subdomain_rejected` |
| **BUG-003** | HIGH (DB) | Alembic Migrations (`c011ec7100`) | **TUZATILDI** | `e6df651` | `backend/tests/test_alembic_migrations_clean_db.py` |
| **BUG-004** | HIGH (Build) | Admin-Panel (`scraper/page.tsx`) | **TUZATILDI** | `98f53af` | `npx tsc --noEmit` (Admin Panel TS Suite) |
| **BUG-005** | MEDIUM (UX) | Bot (`handlers/reviews.py`) | **TUZATILDI** | `aa7682e` | `bot/tests/test_cancel_fsm_command.py` |
| **BUG-006** | MEDIUM (Ops) | Bot (`main.py`) | **TUZATILDI** | `d85b427` | `bot/tests/test_bot_instance_lock.py` |
| **BUG-007** | MEDIUM (Sec) | Bot (`middlewares/ban_check.py`, `api_client.py`) | **TUZATILDI** | `d85b427` | `bot/tests/test_ban_middleware_inline.py` |
| **BUG-008** | MEDIUM (Leak) | Scraper (`scraper/queue_manager.py`) | **TUZATILDI** | `33b0193` | `backend/tests/test_queue_manager_engine_dispose.py` |
| **BUG-009** | MEDIUM (Design) | Website (`achievements`, `catalog`, etc.) | **TUZATILDI** | `caa6aa9` | `backend/tests/test_cinematic_red_design_standard.py` |
| **BUG-010** | LOW (Sync/UX) | Website (`ContinueWatchingSection.tsx`) | **TUZATILDI** | `ad7dbfa` | `website/tests/continue_watching_sync.spec.ts` |

---

## 2. 🔬 ILDIZ SABABLAR XULOSASI (ROOT CAUSE ANALYSIS)

### BUG-001: Backend API Banned User Bypass
- **Ildiz sabab:** `backend/app/api/deps.py` dagi `get_current_user` dependency faqat JWT tokenni decode qilib, payload dagi `sub` (user_id) va `telegram_id` ni qaytargan, biroq bazadan foydalanuvchining `is_banned` holatini tekshirmagan. Oqibatda bloklangan foydalanuvchi o'z JWT tokeni bilan barcha shaxsiy API'larga (tarix, obunalar, tavsiyalar, sharhlar) to'liq kirish imkoniyatiga ega bo'lib qolgan.
- **Tuzatish:** `get_current_user` ga `session: AsyncSession = Depends(get_db_session)` ulandi. Bazadan `UserModel` tekshirilib, topilmasa 401 Unauthorized, agar `user.is_banned == True` bo'lsa darhol `HTTPException(403, detail="Hisobingiz ma'muriyat tomonidan bloklangan")` chiqarildi. `get_current_user_optional` ham ushbu tekshiruvdan o'tadi va bloklangan/yaroqsiz foydalanuvchilarni `None` deb hisoblaydi.
- **RED Dalil:** `AssertionError: Expected 403 Forbidden for banned user, got 200: {"series":[],"collections":[],"total":0}`
- **GREEN Dalil:** `backend/tests/test_banned_user_blocked_api.py::test_banned_user_is_strictly_blocked_with_403 PASSED [100%]` (bloklangan user 403 oladi, faol user 200 oladi).

### BUG-002: CORS Origin Regex Orqali Begona Vercel Domenlariga Ruxsat Berilishi
- **Ildiz sabab:** `backend/app/core/config.py` dagi `CORS_ORIGIN_REGEX` `r"^https:\/\/(kinochi-project-alpha|kinochi-admin)(-[a-zA-Z0-9_-]+)?\.vercel\.app$"` ko'rinishida bo'lib, `(-[a-zA-Z0-9_-]+)?` qismi ixtiyoriy so'z qo'shimchalariga ruxsat bergan. Natijada xaker `kinochi-project-alpha-attacker.vercel.app` nomli ilova ochib, foydalanuvchilarning JWT sessiyalarini o'g'irlash yoki credentialed so'rovlar yuborish imkoniyatiga ega edi.
- **Tuzatish:** `CORS_ORIGIN_REGEX` qat'iylashtirildi: `r"^https:\/\/(kinochi-project-alpha|kinochi-admin)-(?:git-[a-zA-Z0-9_-]+|[a-z0-9]{9,}(?:-[a-zA-Z0-9_-]+)?)\.vercel\.app$"`. Endi faqat haqiqiy Git branch deploymentlari (`git-*`) yoki Vercel avtomatik xeshli preview deploymentlariga (`[a-z0-9]{9,}`) ruxsat beriladi, ixtiyoriy begona so'zlar rad etiladi. Rasmiy ishlab chiqarish domenlari esa `CORS_ORIGINS` ro'yxatida to'liq tekshiriladi.
- **RED Dalil:** `AssertionError: Security flaw: Attacker origin https://kinochi-project-alpha-attacker.vercel.app was allowed by CORS configuration!`
- **GREEN Dalil:** `backend/tests/test_cors_regex_security.py PASSED [100%]` (tajovuzkor domenlar bloklandi, rasmiy preview va prod domenlar ruxsat etildi).

### BUG-003: Bo'sh Bazada Alembic Migratsiyasining Yiqilishi (`collections` Bog'liqligi)
- **Ildiz sabab:** `backend/alembic/versions/c011ec7100_add_collection_subscriptions.py` migratsiyasida `collection_subscriptions` jadvali `REFERENCES collections(id)` tashqi kaliti bilan yaratilgan, biroq `collections` jadvalini yaratuvchi DDL zanjirda keyinroq keluvchi reconciler migratsiyasiga (`b2c3d4e5f6a7`) qo'yilgan bo'lgan. Oqibatda bo'sh bazada yoki yangi muhitda migratsiyalar bajarilganda PostgreSQL `asyncpg.exceptions.UndefinedTableError: relation "collections" does not exist` xatosi bilan to'xtagan.
- **Tuzatish:** `c011ec7100_add_collection_subscriptions.py` migratsiyasiga `collection_subscriptions` yaratilishidan avval idempotent `CREATE TABLE IF NOT EXISTS collections (...)` DDL qo'shildi. `downgrade` qismiga ham tegishli xavfsiz tozalash kiritildi.
- **RED Dalil:**
  ```
  asyncpg.exceptions.UndefinedTableError: relation "collections" does not exist
  [SQL: CREATE TABLE IF NOT EXISTS collection_subscriptions (
      ... collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE ...
  )]
  ```
- **GREEN Dalil:** `backend/tests/test_alembic_migrations_clean_db.py PASSED [100%]` (Bo'sh PostgreSQL bazasida `upgrade head`, `downgrade -1`, `upgrade head` zanjiri to'liq va xatosiz o'tdi).

### BUG-004: Admin Panel TypeScript Kompilyatsiyasi va Build Yiqilishi
- **Ildiz sabab:** `admin-panel/app/scraper/page.tsx` da `interface QueueItem` statuslari faqat `"pending" | "in_progress" | "completed" | "failed" | "already_exists" | "needs_review"` bilan cheklangan bo'lib, backendning yangi `"queued"` va `"published"` statuslari kiritilmagan edi. Natijada kodda `"published"` yoki `"queued"` bilan taqqoslashlar TS2367 ("no overlap") xatosini keltirib chiqargan.
- **Tuzatish:** `QueueItem['status']` union tipiga `"queued"` va `"published"` qo'shildi.
- **RED Dalil:**
  ```
  app/scraper/page.tsx(4631,54): error TS2367: This comparison appears to be unintentional because the types '"failed" | "pending" | "in_progress" | "already_exists" | "needs_review"' and '"published"' have no overlap.
  app/scraper/page.tsx(4957,57): error TS2367: This comparison appears to be unintentional because the types '"completed" | "failed" | "in_progress" | "already_exists" | "needs_review"' and '"queued"' have no overlap.
  ```
- **GREEN Dalil:** `cd admin-panel; npx tsc --noEmit` -> chiqish kodi 0 (0 errors, 100% muvaffaqiyatli kompilyatsiya).

### BUG-005: Telegram Botda `/cancel` Komandasining Yo'qligi va FSM Sharh Qopqoni
- **Ildiz sabab:** `bot/handlers/reviews.py` dagi `handle_review_comment` handleri `ReviewStates.waiting_for_comment` holatida har qanday matnni (`F.text`) sharh deb hisoblagan. Foydalanuvchi jarayondan chiqish niyatida `/cancel` yozganda ham, bot uni film sharhi sifatida qabul qilib bazaga saqlagan. Shuningdek global `/cancel` komandasi ro'yxatdan o'tkazilmagan.
- **Tuzatish:** `handle_review_comment` ichiga `/cancel`, `cancel`, `bekor qilish` so'zlari kelganda `state.clear()` qilib sharh qoldirishni to'xtatish qo'shildi. Qo'shimcha ravishda `@router.message(Command("cancel"))` orqali har qanday faol FSM holatini bekor qilish kiritildi.
- **RED Dalil:**
  ```
  AssertionError: Expected 'submit_review' to not have been called. Called 1 times.
  Calls: [call(user_id=12345, rating=9, comment='/cancel', movie_id=100, series_id=None, episode_id=None)].
  ```
- **GREEN Dalil:** `bot/tests/test_cancel_fsm_command.py PASSED [100%]` (ikkala test: sharh FSM bekor qilinishi va `/cancel` buyrug'i 100% o'tdi).

### BUG-006: Telegram Botda Yagona Instansiya (Single Instance Lock) Himoyasining Yo'qligi
- **Ildiz sabab:** `bot/main.py` da bir vaqtda bir nechta polling instansiyasi ochilishini cheklovchi mexanizm yo'q edi. Natijada ikkinchi bot jarayoni (masalan fon servislari yoki adashib ishga tushirilgan nusxa) ishga tushganda, Telegram API ga takroriy `getUpdates` so'rovlari ketib, uzluksiz `TelegramConflictError` vujudga kelgan va inline qidiruvlar yo'qolgan.
- **Tuzatish:** `bot/main.py` ga atomik OS bayroqlari (`os.O_CREAT | os.O_EXCL`) va PID fayl (`.bot.lock`, `.bot.pid`) bilan ishlovchi `BotInstanceLock` klassi kiritildi. Agar bot allaqachon ishlab turgan bo'lsa, ikkinchi nusxa `BotAlreadyRunningError` bilan xavfsiz to'xtaydi. Bot yopilganda qulf avtomatik bo'shatiladi.
- **RED Dalil:** `ImportError: cannot import name 'BotInstanceLock' from 'bot.main'`
- **GREEN Dalil:** `bot/tests/test_bot_instance_lock.py PASSED [100%]` (takroriy qulflash `BotAlreadyRunningError` beradi, release'dan keyin qayta qulflash muvaffaqiyatli).

### BUG-007: BanCheckMiddleware `inline_query` Voqealariga Qo'llanmaganligi va Stale-While-Error Siyosati
- **Ildiz sabab:** `bot/main.py` da `BanCheckMiddleware` faqat `dp.message` va `dp.callback_query` ga ro'yxatdan o'tkazilib, `dp.inline_query` chetda qolib ketgan edi. Bloklangan foydalanuvchi `@bot kino_nomi` deb inline qidiruv yuborganida tizim unga javob beravergan. Bundan tashqari, 60s TTL kesh muddati tugaganda agar backend vaqtincha javob bermay qolsa, foydalanuvchi avtomatik unban bo'lib qolgan.
- **Tuzatish:**
  1. `bot/main.py` ga `dp.inline_query.middleware(BanCheckMiddleware())` qo'shildi.
  2. `bot/middlewares/ban_check.py` da `InlineQuery` voqeasiga `switch_pm_text="⛔️ Hisobingiz bloklangan"` bilan bo'sh natijalar qaytarildi.
  3. `bot/services/api_client.py` dagi `check_user_banned` ga me'moriy kelishuvga binoan Stale-While-Error siyosati kiritildi: avval bloklanganligi ma'lum bo'lgan foydalanuvchi backend uzilib qolsa ham baribir bloklangan deb qoladi (`True`). Faqat avval ro'yxatda bo'lmagan yangi foydalanuvchilar uchun fail-open ishlaydi va warning log qilinadi.
- **RED Dalil:**
  ```
  AssertionError: Expected answer to have been awaited once. Awaited 0 times.
  AssertionError: Stale banned user was incorrectly unbanned during backend outage! (assert False is True)
  ```
- **GREEN Dalil:** `bot/tests/test_ban_middleware_inline.py PASSED [100%]` (ikkala test: inline query ban middleware va stale-while-error siyosati 100% o'tdi).

### BUG-008: Ephemeral Thread Loopda `null_engine` Resurslarining Oqishi (Socket Leak)
- **Ildiz sabab:** `scraper/queue_manager.py` dagi `_run_coro_sync` funksiyasi sinxron chaqiruvlarni bajarish uchun alohida `ThreadPoolExecutor` ichida yangi `new_loop = asyncio.new_event_loop()` yaratgan. Shu jarayonda yaratilgan `null_engine` loop obyektiga bog'langan (`_kinochi_loop_session_factory`). Biroq, `finally:` blokida faqat `new_loop.close()` chaqirilib, unga bog'langan `null_engine.dispose()` chaqirilmagan. Natijada yuzlab sinxron operatsiyalar davomida ochiq TCP rozetkalari (sockets) va ulanish resurslari oqib (leak bo'lib) qolgan.
- **Tuzatish:** `_run_coro_sync` ichida koroutina `_runner_coro` bilan o'raldi. Ushbu o'rovchi koroutina `finally:` blokida joriy ishlayotgan loopdan `_kinochi_loop_session_factory` ni oladi, agar mavjud bo'lsa loop yopilishidan avval `await factory.kw["bind"].dispose()` ni to'liq bajaradi. Thread xavfsizligi uchun `_runner` ning tashqi `finally:` blokida ham qo'shimcha dispose tekshiruvi qo'yildi.
- **RED Dalil:**
  ```
  AssertionError: Engine was not disposed before thread loop shutdown! Disposed count: 0
  assert 0 == 1
  ```
- **GREEN Dalil:** `backend/tests/test_queue_manager_engine_dispose.py PASSED [100%]` (ikkala test: asinxron kontekst va sinxron kontekstdagi ephemeral loopda engine to'liq dispose bo'lishi 100% o'tdi).

### BUG-009: Cinematic Red Standartining Ommaviy Buzilishi (Amber/Yellow Qoldiqlari)
- **Ildiz sabab:** Loyiha konstitutsiyasida belgilangan Cinematic Red Design Standard qoidasiga ko'ra, sariq va oltin ranglar (`rating-gold`, `amber-*`, `yellow-*`) FAQAT reyting yulduzlari va ballari (IMDb/Kinopoisk) uchun ruxsat etilgan. Biroq, `website/app/achievements/page.tsx`, `catalog/page.tsx`, `notifications/page.tsx`, `profile/page.tsx` va `subscriptions/page.tsx` sahifalarida yutuq kartalari, bildirishnoma piktogrammalari, profil doiralari, sarlavha aksentlari va obuna badgelari sariq/amber ranglarida qolib ketgan edi (jami 25 ta qoidabuzarlik).
- **Tuzatish:** Ushbu 5 ta sahifadagi barcha reytingga aloqador bo'lmagan `amber-*` va `rating-gold` sinflari Cinematic Red (`primary`, `#E50914`, `primary-hover`) sinflari bilan to'liq almashtirildi. Faqat IMDb/Kinopoisk yulduzchalari va ballari o'zining oltin rangida saqlandi.
- **RED Dalil:**
  ```
  AssertionError: Found 25 Cinematic Red Design Standard violations:
    achievements/page.tsx:141 -> ['amber-500']
    achievements/page.tsx:148 -> ['amber-400', 'amber-500', 'amber-400', 'amber-400']
    catalog/page.tsx:26 -> ['amber-500']
    notifications/page.tsx:255 -> ['amber-400']
    profile/page.tsx:236 -> ['text-rating-gold']
    subscriptions/page.tsx:86 -> ['bg-rating-gold/15', 'text-rating-gold', 'border-rating-gold/30']
    ...
  assert 25 == 0
  ```
- **GREEN Dalil:** `backend/tests/test_cinematic_red_design_standard.py PASSED [100%]` va `website` da `npx tsc --noEmit` chiqish kodi 0 (0 xato).

### BUG-010: Saytda "Tarixni tozalash"ning Chala Ishlashi (`localStorage` Desinxronizatsiyasi)
- **Ildiz sabab:** `website/components/home/ContinueWatchingSection.tsx` da tomosha tarixi ikki manbadan olingan: 1) autentifikatsiyadan o'tgan foydalanuvchi uchun backend API (`/users/me/history`), 2) mehmonga xos brauzer `localStorage.getItem("mediaplus_continue_watching")`. Foydalanuvchi Telegram bot orqali yoki saytdan "Tarixni tozalash" qilganida server DB tozalanardi, biroq sayt bosh sahifasini ochganda server tarixi bo'sh (0 ta) bo'lsa ham brauzer `localStorage` dagi eski keshni o'qib, o'chirilgan kinolarni qayta ekranga chiqarib yuborardi.
- **Tuzatish:** `resolveContinueWatchingItems` funksiyasi ajratildi. Agar foydalanuvchi autentifikatsiyadan o'tgan bo'lsa (`status === "authenticated"`) va uning serverdagi tarixi muvaffaqiyatli olinib bo'sh (0 ta) bo'lsa, `localStorage.removeItem("mediaplus_continue_watching")` chaqirilib, mahalliy xotiradagi eski kesh butunlay tozalanadi va mehmonga xos filmlar ekranga aralashmaydi. Mehmon foydalanuvchilar uchun esa `localStorage` avvalgidek to'g'ri ishlaydi.
- **RED Dalil:**
  ```
  TypeError: (0 , _ContinueWatchingSection.resolveContinueWatchingItems) is not a function
    at tests/continue_watching_sync.spec.ts:24:53
  2 failed
  ```
- **GREEN Dalil:**
  ```
  Running 2 tests using 1 worker
    ok 1 tests\continue_watching_sync.spec.ts:5:7 › authenticated user with cleared history (0 items) must purge localStorage and return 0 items (16ms)
    ok 2 tests\continue_watching_sync.spec.ts:36:7 › unauthenticated guest user continues to receive localStorage items (7ms)
    2 passed (1.9s)
  ```
  va `website` da `npx tsc --noEmit` chiqish kodi 0 (0 xato).

---

## 3. 🔍 YANGI TOPILMALAR (NEW FINDINGS)

*Ushbu bosqichda barcha 10 ta nuqson (BUG-001 dan BUG-010 gacha) muvaffaqiyatli tuzatildi va to'liq suite regressiyasiz yashil holatga keltirildi. Yangi bloklovchi xatolar topilmadi.*

---

## 4. 📊 TESTLAR VA QAMROV (BEFORE / AFTER METRICS)

### A. Testlar Statistikasi Solishtirmasi:
| Komponent | Boshlang'ich (Audit Holati) | Yakuniy (Tuzatishlardan So'ng) | O'zgarish |
| :--- | :--- | :--- | :--- |
| **Backend (pytest)** | 518 passed, 3 failed, 10 skipped | **529 passed, 0 failed, 10 skipped** (89.25s) | **+11 test, 0 failure** |
| **Bot (pytest)** | 87 passed | **92 passed, 0 failed** (10.08s) | **+5 test, 0 failure** |
| **Admin-Panel (tsc)** | 3 ta TS kompilyatsiya xatosi | **0 errors (`npx tsc --noEmit` muvaffaqiyatli)** | **100% tuzatildi** |
| **Website (tsc & test)** | 25 ta Cinematic Red buzilishi | **0 errors (tsc), 2 passed (playwright), 0 dizayn xatosi** | **100% tuzatildi** |

### B. Qamrov (Coverage):
* Backend umumiy test qamrovi: **53%** (9,898 statements, 4,670 miss).

---

## 5. ❓ OCHIQ MASALALAR VA SAVOLLAR

1. **Skipped testlar (10 ta):** 
   - `test_storage_locking_and_defaults.py`: `test_queue_manager_concurrent_claim_skip_locked` (SKIP_LOCKED funksiyasi SQLite in-memory emas, real PostgreSQL da ishlaydi).
   - `test_autopilot_rebuild.py` (8 ta test): Telethon va live session talab qiluvchi real tarmoq testlari.
   - `test_media_types_feature.py`: real donor kanallariga bog'liq integratsion test.
   Ushbu skipped testlar ishlab chiqarish xavfsizligi va lokal DB/mock cheklovlari doirasida tabiiy ravishda cheklangan.
2. Barcha 10 ta audit nuqsoni qat'iy TDD (RED -> Minimal Fix -> GREEN -> Single Commit) tamoyili asosida to'liq bartaraf etildi.
