# KINOCHI STABILIZATION PROJECT: GUEST FLOW AUDIT & DISCOVERY REPORT

**Sana:** 2026-11-14  
**Faza:** 1. PROJECT DISCOVERY & 2. IMPLEMENTATION AUDIT (GUEST OQIMI)  
**Holat:** Yakunlandi (KODGA TEGINILMADI, FAQAT FAKT VA DALILLAR ANIQLANDI)

---

## 1. GUEST FEATURE INVENTORY (Mehmon Sahifalari Xaritasi)

| # | Sahifa Marshruti | Komponent / Fayl | Maqsadi & Guest Rejimidagi Holati | Real Implementatsiya Holati |
|---|---|---|---|---|
| 1 | `/` (Bosh sahifa) | `website/app/page.tsx` | Hero banner, davom ettirish, lentalar | SSR orqali `/movies` va `/series` chaqiriladi. LocalStorage davom ettirish bloki mavjud. |
| 2 | `/movie/[code]` | `website/app/movie/[code]/page.tsx` | Film tafsilotlari, reyting, aktyorlar | **IN-BROWSER PLEYER YO'Q.** Tomosha tugmasi `https://t.me/bot?start=code` ga yo'naltiradi. |
| 3 | `/series/[id]` | `website/app/series/[id]/page.tsx` | Serial fasllari va qismlari | **IN-BROWSER PLEYER YO'Q.** Qism bosilganda Telegram deep-link ochiladi. |
| 4 | `/catalog` | `website/app/catalog/page.tsx` | To'liq filtrli media katalogi | Server-side `/movies` va `/series` filtr parametrlarini birlashtiradi. |
| 5 | `/search` | `website/app/search/page.tsx` | Qidiruv maydoni va natijalar | **KRITIK XATO:** Backendda `NameError: name 're' is not defined` sababli 500 beradi. |
| 6 | `/top100` | `website/app/top100/page.tsx` | Top reytingli kinolar va seriallar | `/movies?sort=rating` va `/series?sort=rating` saralangan ro'yxati. |
| 7 | `/collections` | `website/app/collections/page.tsx` | Franshizalar va to'plamlar | **KRITIK XATO:** N+1 query loop tufayli backend 15s timeout beradi. |
| 8 | `/collections/[slug]` | `website/app/collections/[slug]/page.tsx` | Xronologiya va qismlar | To'plam qismlarini xronologik tartibda ko'rsatadi. |
| 9 | `/actors` | `website/app/actors/page.tsx` | Aktyorlar ro'yxati | `/actors` API orqali aktyorlar kartochkalari ko'rsatiladi. |
| 10 | `/category/[id]` | `website/app/category/[id]/page.tsx` | Janr bo'yicha saralangan sahifa | `/categories` va janr ID orqali filtrlangan ro'yxat. |
| 11 | `/anime` | `website/app/anime/page.tsx` | Anime toifasi | `category_id=2` orqali `/series` va `/movies` chaqiradi. |
| 12 | `/cartoons` | `website/app/cartoons/page.tsx` | Multfilmlar toifasi | `category_id=22` orqali `/movies` va `/series` chaqiradi. |
| 13 | `/doramas` | `website/app/doramas/page.tsx` | Doramalar toifasi | `category_id=40` orqali `/series` va `/movies` chaqiradi. |
| 14 | `/movies` | `website/app/movies/page.tsx` | Barcha filmlar | `/movies` API natijalarini sahifalab ko'rsatadi. |
| 15 | `/series` | `website/app/series/page.tsx` | Barcha seriallar | `/series` API natijalarini sahifalab ko'rsatadi. |
| 16 | `/premieres` | `website/app/premieres/page.tsx` | Premyeralar | Oxirgi chiqarilgan filmlar ro'yxati. |
| 17 | `/notifications` | `website/app/notifications/page.tsx` | Bildirishnomalar | **FASAD:** `/broadcasts/public` o'qiydi, shaxsiy qismi Guest uchun sintetik "Xush kelibsiz" beradi. |
| 18 | `/history` | `website/app/history/page.tsx` | Tomosha tarixi | Guest uchun Telegram login taklif etuvchi ekran chiqadi. |
| 19 | `/favorites` | `website/app/favorites/page.tsx` | Sevimlilar ro'yxati | Guest uchun Telegram login taklif etuvchi ekran chiqadi. |
| 20 | `/profile` | `website/app/profile/page.tsx` | Profil kabineti | Guest uchun Telegram login taklif etuvchi ekran chiqadi. |
| 21 | `/achievements` | `website/app/achievements/page.tsx` | Yutuqlar | **FASAD:** Guest uchun qulflangan yutuqlar ro'yxati va login ko'rsatiladi. |
| 22 | `/subscriptions` | `website/app/subscriptions/page.tsx` | Obunalar | Guest uchun login taklif etiladi. |
| 23 | `/requests` | `website/app/requests/page.tsx` | Film so'rash / buyurtma | Guest ovoz bera oladi yoki yangi kino so'rashi mumkin. |
| 24 | `/p/[slug]` | `website/app/p/[slug]/page.tsx` | Maxsus sahifalar | `/pages/{slug}` API orqali dinamik ma'lumot yuklanadi. |
| 25 | `/test-auth` | `website/app/test-auth/page.tsx` | Diagnostika sahifasi | **XAVFSIZLIK:** Diagnostika sahifasi ochiq qolgan. |

---

## 2. BUTTON & INTERACTION INVENTORY (Guest Harakatlari)

| Komponent | Tugma / Element | Triggerni Kod Qatori | Guest Uchun Amaldagi Natijasi |
|---|---|---|---|
| `TelegramWatchButton.tsx` | `TELEGRAM ORQALI TOMOSHA QILISH` | `line 108: handleClick` | LocalStorage'ga yozadi, Telegram bot havolasini ochadi va **"Muvaffaqiyatli yuborildi" soxta modalini** ko'rsatadi. |
| `TrailerModal.tsx` | `Treyler ko'rish` | `line 45: setIsOpen(true)` | YouTube iframe yoki video modalini ochadi. Ishlaydi. |
| `ShareButton.tsx` | `Ulashish` | `line 22: handleShare` | Clipboard'ga nusxalaydi yoki `navigator.share` ochadi. Ishlaydi. |
| `SubscribeButton.tsx` | `Obuna bo'lish` | `line 68: handleToggle` | `status !== "authenticated"` sababli `TelegramLoginModal` ochiladi. Ishlaydi. |
| `ReportIssueButton.tsx` | `Xatolikni bildirish` | `line 36: setIsOpen(true)` | `ReportIssueModal` ochiladi. Guest fayl va matn yubora oladi (`POST /api/v1/reports`). Ishlaydi. |
| `ReviewsSection.tsx` | `Fikr bildirish / Baholash` | `line 201: setFormOpen` | Form ochilganda Guestga `TelegramLoginWidget` ko'rsatiladi. To'g'ri. |
| `ContinueWatchingSection.tsx` | `✕ O'chirish` | `line 238: removeItem` | LocalStorage'dan o'chiradi va UI yangilanadi. Ishlaydi. |
| `ContinueWatchingSection.tsx` | `Kartochka bosish` | `Link href="/movie/..."` | Film sahifasiga yo'naltiradi. |
| `UnifiedFilterBar.tsx` | Janr / Yil / Saralash dropdownlari | `onChange / Link` | URL qidiruv parametrlarini o'zgartiradi va sahifani yangilaydi. Ishlaydi. |
| `SearchClientView.tsx` | Qidiruv maydoni (Input) | `line 105: performLiveSearch` | Debounce 300ms. **500 xato oladi va .catch ichida yutib yuboradi.** |

---

## 3. API DEPENDENCY MAP (Guest Chaqiradigan Endpointlar va Real Backend Javobi)

| Frontend Chaqiruvi | Backend Haqiqiy Marshruti | Guest HTTP Javobi | Tahlil va Holat |
|---|---|---|---|
| `GET /movies?limit=...` | `backend/app/api/v1/movies.py:61` | `200 OK` (32.9 KB) | ✅ Barcha e'lon qilingan filmlar qaytadi. |
| `GET /movies/search?q=...` | `backend/app/api/v1/movies.py:663` | **`500 Internal Server Error`** | ❌ **HALOKAT:** `movie_repo.py:341` da `NameError: name 're' is not defined`. |
| `GET /series?limit=...` | `backend/app/api/v1/series.py:53` | `200 OK` (32.5 KB) | ✅ Barcha e'lon qilingan seriallar qaytadi. |
| `GET /series/search?q=...` | `backend/app/api/v1/series.py:349` | `200 OK` | ✅ Seriallar qidiruvi ishlaydi. |
| `GET /categories` | `backend/app/api/v1/categories.py:27` | `200 OK` (2.2 KB) | ✅ 35 ta toifa to'liq qaytadi. |
| `GET /collections` | `backend/app/api/v1/collections.py:164` | **`TIMEOUT (> 15s)`** | ❌ **HALOKAT:** N+1 DB query loop sababli server qotib qoladi. |
| `GET /actors` | `backend/app/api/v1/actors.py:25` | `200 OK` (7.2 KB) | ✅ Aktyorlar ro'yxati qaytadi. |
| `GET /pages` | `backend/app/api/v1/pages.py:30` | `200 OK` (306 B) | ✅ Sahifalar qaytadi. |
| `GET /content-requests` | `backend/app/api/v1/content_requests.py:77` | `200 OK` (18.6 KB) | ✅ 15 ta faol tavsiya qaytadi. |
| `GET /broadcasts/public` | `backend/app/api/v1/broadcasts.py:275` | `200 OK` (7.0 KB) | ✅ Ommaviy e'lonlar qaytadi. |
| `GET /reviews?limit=...` | `backend/app/api/v1/reviews.py:75` | `200 OK` (60 B) | ✅ Sharhlar qaytadi. |
| `GET /sources` | `backend/app/api/v1/sources.py:40` | **`401 Unauthorized`** | ⚠️ Guest uchun yopiq, lekin SourceBadge ba'zida ma'lumot kutadi. |

---

## 4. MOCK, PLACEHOLDER & FAKE SUCCESS AUDIT

### 4.1. Fake Success: `TelegramWatchButton.tsx` (Qatorlar 185–195)
- **Muammo:** Foydalanuvchi "Telegram orqali tomosha qilish" tugmasini bosganda, brauzer faqat `https://t.me/...` havolasini ochadi. Hech qanday backend API chaqirilmaydi.
- **Soxtalik:** Modal oynada yashil belgi va:
  `Muvaffaqiyatli yuborildi! Telegram botingizga video fayl va tomosha qilish havolasi yuborildi.` deb yoziladi.
- **Haqiqat:** Botga hech narsa yuborilmagan. Agar bot o'chiq bo'lsa yoki foydalanuvchida Telegram bo'lmasa ham, sayt "yuborildi" deb aldaydi.

### 4.2. Mock / Placeholder Logic: `ContinueWatchingSection.tsx` (Qatorlar 61, 74, 117)
- **Muammo:** Progress foizi dinamik vaqtga (masalan 14/120 daqiqa) asoslanmagan.
- **Soxtalik:** 
  `progress: item.progress || 60` (Hardcoded 60%)  
  `progress: h.status === "completed" ? 100 : 65` (Hardcoded 65%)
- **Haqiqat:** Qanchalik ko'rilganidan qat'i nazar, barcha kartochkalar soxta 60% yoki 65% progress chizig'ini ko'rsatadi.

### 4.3. Botdagi Fake Loading: `bot/handlers/browsing.py` (Qatorlar 33–34)
- **Muammo:** Agar bazadagi filmda video fayl (`telegram_file_id`) biriktirilmagan bo'lsa, `send_movie_to_user` `False` qaytaradi.
- **Soxtalik:** Bot foydalanuvchiga:
  `⏳ Video yuklanmoqda...` deb xabar beradi.
- **Haqiqat:** Hech qanday yuklash fonida vazifa (job) ketayotgani yo'q. Video hech qachon kelmaydi.

---

## 5. SILENT ERROR HANDLING AUDIT

| Fayl | Qator | Kod Parchasi | Ta'siri |
|---|---|---|---|
| `website/components/SearchClientView.tsx` | 185 | `fetchApi('/movies/search?...').catch(() => ({ items: [] }))` | Backend 500 NameError bersa, konsolga xato chiqarmay bo'sh massiv qaytaradi. Foydalanuvchiga kino yo'qdek ko'rinadi. |
| `website/app/notifications/page.tsx` | 136 | `try { localStorage.setItem(...) } catch (e) {}` | Xato yashiriladi. |
| `website/components/TelegramWatchButton.tsx` | 74 | `try { tg.BackButton.offClick(...) } catch (e) {}` | Xato yashiriladi. |
| `website/components/home/ContinueWatchingSection.tsx` | 225, 243 | `try { ... } catch (e) {}` | Xato yashiriladi. |

---

## 6. YAGONA ISSUE REGISTRY (GUEST OQIMI)

### [GUEST-ISSUE-001] Qidiruv 500 NameError (Kritik Blocker)
- **Fayl:** `backend/app/infrastructure/db/repositories/movie_repo.py`, qator 341
- **Dalil:** `NameError: name 're' is not defined. Did you forget to import 're'?`
- **Takrorlash:** Brauzerda yoki cURL orqali `GET http://127.0.0.1:8000/api/v1/movies/search?q=avatar` yuborilganda 500 status qaytadi.
- **Frontendi:** `SearchClientView.tsx:185` ushbu 500 ni `.catch()` qilib yutib yuboradi va "Topilmadi" deb ko'rsatadi.
- **Ustuvorlik:** P0 (Blocker).

### [GUEST-ISSUE-002] To'plamlar N+1 Loop & Timeout (Kritik Blocker)
- **Fayl:** `backend/app/api/v1/collections.py`, qatorlar 194–221
- **Dalil:** `list_collections` har bir to'plam uchun alohida `db.execute(count)` va `db.execute(selectinload)` bajaradi. 9 ta to'plam uchun 36+ ta so'rov ketma-ket yuborilib, 15 soniyadan oshib ketadi va so'rov uziladi (`timed out`).
- **Takrorlash:** `GET http://127.0.0.1:8000/api/v1/collections` so'rovi 15 soniyada javob bermaydi.
- **Ustuvorlik:** P0 (Blocker).

### [GUEST-ISSUE-003] In-Browser Player Fasad va Soxta Yuborish Xabarnomasi (Major UX)
- **Fayl:** `website/components/TelegramWatchButton.tsx`, qatorlar 185–195
- **Dalil:** Vebsaytda HTML5/HLS pleyer mavjud emas. Har qanday tomosha harakati foydalanuvchini botga yo'naltiradi, lekin ekranda "Telegram botingizga video fayl muvaffaqiyatli yuborildi" degan soxta tasdiq chiqadi.
- **Takrorlash:** Istalgan kinoga kirib "Telegram orqali tomosha qilish" bosilsa, Telegram ochilmasdan oldinoq modalda "yuborildi" deb chiqadi.
- **Ustuvorlik:** P1 (Major).

### [GUEST-ISSUE-004] Continue Watching Soxta Foiz (Minor)
- **Fayl:** `website/components/home/ContinueWatchingSection.tsx`, qatorlar 61, 74, 117
- **Dalil:** `progress: 60` va `progress: 65` qattiq yozilgan.
- **Takrorlash:** Mehmon sifatida film bosilganda ro'yxatda 60% ko'rsatadi.
- **Ustuvorlik:** P2 (Minor).

### [GUEST-ISSUE-005] Botda Video Yo'q Filmlar Uchun Aldovchi Kutish Xabari (Major)
- **Fayl:** `bot/handlers/browsing.py`, qatorlar 33–34
- **Dalil:** `if not success: await callback.message.answer("⏳ Video yuklanmoqda...")`.
- **Takrorlash:** Bazada video file ID si bo'lmagan kinoda "Ko'rish" bosilsa, "yuklanmoqda" deydi, lekin hech narsa bo'lmaydi.
- **Ustuvorlik:** P1 (Major).

### [GUEST-ISSUE-006] Ochiq Qolgan Diagnostika Sahifasi (Security)
- **Fayl:** `website/app/test-auth/page.tsx`
- **Dalil:** Ishlab chiqarish muhitida `/test-auth` marshruti ochiq turibdi.
- **Ustuvorlik:** P2 (Security Cleanup).

---

## 7. DISCOVERY COVERAGE REPORT (Qamrov Hisoboti)

- **Tekshirilgan Guest Sahifalari:** 25 / 25 (100% to'liq ko'rib chiqildi).
- **Tekshirilgan Frontend Komponentlari:** 72 ta TSX fayl.
- **Tekshirilgan API Endpointlari:** 13 ta asosiy Guest GET/POST endpointlari.
- **Aniqlangan P0 Blockerlar:** 2 ta (`GUEST-ISSUE-001`, `GUEST-ISSUE-002`).
- **Aniqlangan P1 Major Muammolar:** 2 ta (`GUEST-ISSUE-003`, `GUEST-ISSUE-005`).
- **Aniqlangan P2 Minor / Cleanup:** 2 ta (`GUEST-ISSUE-004`, `GUEST-ISSUE-006`).
- **O'zgartirilgan Kod Qatorlari:** **0 qator** (Qat'iy ravishda hech qanday kod o'zgartirilmadi).
