# FILTER_AUDIT.md — MediaPlus / Kinochi Keng Qamrovli Filtr va Saralash Auditi

**Sana:** 2026-11-10  
**Audit roli:** Senior Fullstack Engineer + QA  
**Branch:** `filters/fix-all`  
**Muhit:** Mahalliy xavfsiz muhit (`localhost:5433`, `kinochi_v2_test`), mustaqil SQL Orakul usuli va Playwright  

---

## 1. Ijroiya Xulosasi (Executive Summary)

Ushbu audit MediaPlus/Kinochi loyihasidagi 44 ta sahifa (25 ta veb-portal + 19 ta admin-panel), backend endpointlari, SQL jadvallari va UI komponentlarini to'liq tekshirib chiqdi.
17 ta mustaqil avtomatlashtirilgan backend orakul testlari o'tkazildi:
- **9 ta PASS** (Kategoriya ID, Chiqarilgan yili, Pending/Draft kontent xavfsizlik filtri, To'plamlar xronologik saralashi, EXPLAIN so'rov tezligi < 2ms va h.k.)
- **7 ta FAIL (Kritik xatolar)**:
  1. `FILTER-001`: To'plam kartalaridagi son (`items_count`) ichidagi haqiqiy filmlar soniga teng emas (pending kinolar ham sanaladi).
  2. `FILTER-002`: UI dagi inglizcha janr slugi (`action`, `scifi`) DB dagi o'zbekcha yozuvlarga (`Jangari`, `Fantastika`) mos kelmaydi — 0 ta natija beradi.
  3. `FILTER-003`: `GET /movies` marshrutida `sort` parametri yo'q — "Reyting bo'yicha saralash" (`?sort=rating`) butunlay inkor qilinadi, doim eng eski kinolar birinchi chiqadi (`id.asc`).
  4. `FILTER-004`: `GET /series` marshrutida `sort` parametri yo'q — seriallarni reyting bo'yicha saralab bo'lmaydi.
  5. `FILTER-005`: `CatalogGrid.tsx` da `type === "series"` bo'lganda `genre`, `year`, `search` parametrlari `loadMore` ga qo'shilmagan — 2-sahifadan boshlab filtrlar o'chib ketadi.
  6. `FILTER-006`: `/movies/search` va `/series/search` endpointlarida `year`, `genre`, `category_id`, `sort` parametrlari yo'q.
  7. `FILTER-007`: Aktyorlar filmografiyasida (`/actors/{id}/movies`) `publish_status == 'published'` tekshirilmagan — pending/draft kinolar ham "Bazada mavjud" deb ko'rsatiladi.
- **1 ta MAVJUD EMAS**: Rejissyorlar sahifasi yoki alohida API si yo'q (aktyorlar ichiga aralashtirilgan).

---

## 2. Barcha Sahifalar Holati (25 Veb-sayt + 19 Admin-panel)

### A. Veb-sayt sahifalari (25 ta)

| # | Sahifa URL & Fayl | Funksiyasi | Holat | Amaldagi Filtr Turi | Dalil / Izoh |
|:---:|---|---|:---:|---|---|
| 1 | `/` ([website/app/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/website/app/page.tsx)) | Bosh sahifa | PASS | ⛔ Filtr yo'q (Kerak emas) | Vitrina formati. |
| 2 | `/catalog` ([website/app/catalog/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/website/app/catalog/page.tsx)) | Katalog markazi | FAIL | ⚠️ `UnifiedFilterBar` (5 parametr) | `sort` backendga bormaydi, `type` dorama/anime uchun qotirilgan ID lardan foydalanadi. |
| 3 | `/movies` ([website/app/movies/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/website/app/movies/page.tsx)) | Kinolar | FAIL | ⚠️ `UnifiedFilterBar` | `sort` parametri API ga uzatilmaydi, slug translatsiyasi yo'q. |
| 4 | `/series` ([website/app/series/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/website/app/series/page.tsx)) | Seriallar | FAIL | ⚠️ `UnifiedFilterBar` | `sort` inkor qilinadi, `CatalogGrid` paginationda `year` va `genre` yo'qoladi. |
| 5 | `/top100` ([website/app/top100/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/website/app/top100/page.tsx)) | Top 100 | FAIL | ⚠️ `UnifiedFilterBar` | `selectedSort` va `selectedCategory` prop sifatida berilmagan. |
| 6 | `/premieres` ([website/app/premieres/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/website/app/premieres/page.tsx)) | Premyeralar | FAIL | ⚠️ `UnifiedFilterBar` | `sort` parametri backendda ishlamaydi. |
| 7 | `/doramas` ([website/app/doramas/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/website/app/doramas/page.tsx)) | Doramalar | FAIL | ⚠️ `UnifiedFilterBar` | `selectedSort` uzatilmagan, dorama ID si qotirilgan (40). |
| 8 | `/anime` ([website/app/anime/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/website/app/anime/page.tsx)) | Anime | FAIL | ⚠️ `UnifiedFilterBar` | `selectedSort` uzatilmagan, anime ID si qotirilgan (2). |
| 9 | `/cartoons` ([website/app/cartoons/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/website/app/cartoons/page.tsx)) | Multfilmlar | FAIL | ⚠️ `UnifiedFilterBar` | `selectedSort` uzatilmagan, multfilm ID si qotirilgan (22). |
| 10 | `/search` ([website/app/search/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/website/app/search/page.tsx)) | Qidiruv | FAIL | ⚠️ Faqat matn + 10 teg | Qidiruv natijalarini yil, janr, tur, reyting bo'yicha filtrlash mavjud emas. |
| 11 | `/category/[id]` ([website/app/category/[id]/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/website/app/category/[id]/page.tsx)) | Kategoriya | FAIL | ⚠️ Faqat kategoriya chiplari | Kategoriya ichida yil, reyting va saralash filtri yo'q. |
| 12 | `/p/[slug]` ([website/app/p/[slug]/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/website/app/p/[slug]/page.tsx)) | Sahifalar | FAIL | ⚠️ Eski `CategoryFilter` | Zamonaviy `UnifiedFilterBar` ulanmagan. |
| 13 | `/collections` ([website/app/collections/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/website/app/collections/page.tsx)) | To'plamlar | FAIL | ⚠️ 4 Tab + Qidiruv | Kartadagi `items_count` ichidagi haqiqiy published kinolar soniga teng emas. |
| 14 | `/collections/[slug]` ([website/app/collections/[slug]/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/website/app/collections/[slug]/page.tsx)) | Xronologiya | PASS | ✅ Dual saralash + Xarita | Voqealar xronologiyasi va Premyera sanasi to'g'ri saralanadi. |
| 15 | `/actors` ([website/app/actors/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/website/app/actors/page.tsx)) | Aktyorlar | FAIL | ⚠️ Faqat matnli qidiruv | Pending kinolar ham "Bazada mavjud" deb ko'rinadi, "Bazada filmi borlar" filtri yo'q. |
| 16 | `/subscriptions` ([website/app/subscriptions/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/website/app/subscriptions/page.tsx)) | Obunalar | PASS | ✅ 3 Tab filtri | *Barchasi, Seriallar, To'plamlar* to'g'ri filtrlanyapti. |
| 17 | `/history` ([website/app/history/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/website/app/history/page.tsx)) | Tarix | PASS | ✅ 2 Tab filtri | *Davom etayotgan* va *Tugallangan* to'g'ri ajratiladi. |
| 18 | `/tv` ([website/app/tv/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/website/app/tv/page.tsx)) | Onlayn TV | PASS | ✅ 4 Tab filtri | *Barchasi, Milliy, Kino, Sport* to'g'ri ishlamoqda. |
| 19 | `/requests` ([website/app/requests/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/website/app/requests/page.tsx)) | Buyurtmalar | PASS | ✅ 2 Tab filtri | *Yangi so'rov* va *Top so'rovlar* to'g'ri ishlamoqda. |
| 20 | `/movie/[code]` | Pleyer | PASS | ⛔ Kerak emas | Yakka film ko'rish sahifasi. |
| 21 | `/series/[id]` | Serial pleyer | PASS | ⛔ Kerak emas | Yakka serial ko'rish sahifasi. |
| 22 | `/profile` | Profil | PASS | ⛔ Kerak emas | Shaxsiy kabinet. |
| 23 | `/achievements` | Yutuqlar | PASS | ⛔ Kerak emas | Gamifikatsiya. |
| 24 | `/notifications` | Xabarlar | PASS | ⛔ Kerak emas | Shaxsiy xabarnomalar. |
| 25 | `/test-auth` | Test sahifasi | PASS | ⛔ Kerak emas | Dasturchi vositasi. |

---

### B. Admin-Panel sahifalari (19 ta)

| # | Sahifa URL & Fayl | Funksiyasi | Holat | Amaldagi Filtr Turi | Dalil / Izoh |
|:---:|---|---|:---:|---|---|
| 1 | `/` ([admin-panel/app/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/admin-panel/app/page.tsx)) | Dashboard | PASS | ⛔ Kerak emas | Umumiy statistika. |
| 2 | `/movies` ([admin-panel/app/movies/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/admin-panel/app/movies/page.tsx)) | Kinolar | FAIL | ⚠️ Faqat qidiruv | Kategoriya, sahifa (`page_id`), manba (`source_id`) bo'yicha filtr yo'q. |
| 3 | `/series` ([admin-panel/app/series/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/admin-panel/app/series/page.tsx)) | Seriallar | FAIL | ⚠️ Faqat qidiruv | Kategoriya va nashr holati (`publish_status`) filtri yo'q. |
| 4 | `/series/[seriesId]` | Mavsumlar | PASS | ⛔ Kerak emas | Bitta serialning mavsumlari kam bo'ladi. |
| 5 | `/series/.../seasons/[seasonId]` | Qismlar | PASS | ⛔ Kerak emas | Tartiblangan qismlar ro'yxati. |
| 6 | `/scraper` ([admin-panel/app/scraper/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/admin-panel/app/scraper/page.tsx)) | Skraper navbati | PASS | ✅ 7 Status Tab + Qidiruv | Status bo'yicha to'liq ishlaydi. |
| 7 | `/audit` ([admin-panel/app/audit/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/admin-panel/app/audit/page.tsx)) | Media audit | PASS | ✅ Muammo Chiplari + Qidiruv | Videosiz, postersiz va h.k. to'liq ishlaydi. |
| 8 | `/requests` ([admin-panel/app/requests/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/admin-panel/app/requests/page.tsx)) | Buyurtmalar | PASS | ✅ Status filtri + Qidiruv | Pending, in_review, completed filtri bor. |
| 9 | `/reports` ([admin-panel/app/reports/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/admin-panel/app/reports/page.tsx)) | Shikoyatlar | PASS | ✅ Status Tabi | Pending, resolved, rejected to'g'ri ishlaydi. |
| 10 | `/rejected` ([admin-panel/app/rejected/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/admin-panel/app/rejected/page.tsx)) | Rad etilganlar | PASS | ✅ Status + Qidiruv | Ishlamoqda. |
| 11 | `/users` ([admin-panel/app/users/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/admin-panel/app/users/page.tsx)) | Foydalanuvchilar | FAIL | ⚠️ Faqat qidiruv | Faol / Bloklangan (banned) tab filtri yetishmayapti. |
| 12 | `/broadcasts` ([admin-panel/app/broadcasts/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/admin-panel/app/broadcasts/page.tsx)) | Tarqatmalar | FAIL | ❌ Yo'q | Draft / Sending / Completed holati bo'yicha filtr yo'q. |
| 13 | `/blacklist` ([admin-panel/app/blacklist/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/admin-panel/app/blacklist/page.tsx)) | Qora ro'yxat | PASS | ⚠️ Faqat qidiruv | Qidiruv mavjud, hozircha yetarli. |
| 14 | `/collections` ([admin-panel/app/collections/page.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/admin-panel/app/collections/page.tsx)) | To'plamlar CRUD | PASS | ⚠️ Faqat qidiruv | Kichik ro'yxat, qidiruv bor. |
| 15 | `/categories` | Kategoriyalar | PASS | ⛔ Kerak emas | Kichik jadval (~40 ta). |
| 16 | `/pages` | Sahifalar | PASS | ⛔ Kerak emas | Kichik jadval (~10 ta). |
| 17 | `/channels` | Kanallar | PASS | ⛔ Kerak emas | Kichik ro'yxat (~5-10 ta). |
| 18 | `/sources` | Manbalar | PASS | ⛔ Kerak emas | Kichik ro'yxat (~4 ta). |
| 19 | `/login` | Kirish | PASS | ⛔ Kerak emas | Kirish sahifasi. |

---

## 3. Aniqlangan Xatolar Ro'yxati (Bugs & Defects: FILTER-001 dan)

### `FILTER-001` (Kritik): To'plam kartasidagi son (`items_count`) ichidagi haqiqiy kinolar soniga teng emas
- **Og'irlik:** Yuqori (High)
- **Sahifa / Komponent:** `/collections` ([CollectionsClientView.tsx](file:///c:/Users/Администратор/Desktop/kino%20bot%20project/kinochi%20project/website/components/CollectionsClientView.tsx)) & `backend/app/api/v1/collections.py:190`
- **Qadamlar:**
  1. `/collections` sahifasiga kirish. "Marvel Kinoolami" kartasiga qarash.
  2. Kartada "5 ta qism" deb yozilganini ko'rish.
  3. Kartani bosib `/collections/marvel-universe` sahifasiga kirish.
- **Kutilgan:** Ichkarida 5 ta kino ko'rinishi yoki kartada ham haqiqiy ko'rinadigan son (4 ta) bo'lishi.
- **Haqiqiy holat:** Kartada "5 ta qism", ichkarida esa faqat 4 ta kino bor!
- **Terminal dalili:**
  ```
  [FAIL] BACKEND-FILT-012: Collections Item Count Truthfulness
  Evidence: CRITICAL DISCREPANCY: List /collections card displays items_count = 5, but inside /collections/marvel-universe only 4 items are visible!
  ```
- **Ildiz sabab:** `collections.py:190` da `select(func.count(CollectionItemModel.id)).where(...)` qilingan, bu pending/draft filmlarni ham hisoblaydi; `get_collection` esa faqat `published` filmlarni qaytaradi.

---

### `FILTER-002` (Kritik): UI dagi inglizcha Janr slugi (`action`, `scifi`, `crime`) DB dagi o'zbekcha yozuvlarga mos kelmaydi
- **Og'irlik:** Yuqori (High)
- **Sahifa / Komponent:** `website/components/catalog/UnifiedFilterBar.tsx` & `backend/app/infrastructure/db/repositories/movie_repo.py:230`
- **Qadamlar:**
  1. `/movies` yoki `/catalog` sahifasida "Janr" dropdownidan "Jangari" ni tanlash.
  2. URL ga `?genre=action` yoziladi.
  3. API chaqiriladi: `GET /api/v1/movies?genre=action`.
- **Kutilgan:** Bazadagi barcha "Jangari" janriga ega kinolar chiqishi kerak.
- **Haqiqiy holat:** Agar filmning `genres` ustunida `"Jangari, Triller"` yozilgan bo'lsa, lekin u to'g'ridan-to'g'ri category 1 ga biriktirilmagan bo'lsa, backend `genres ILIKE '%action%'` deb qidiradi va 0 ta natija beradi!
- **Terminal dalili:**
  ```
  [FAIL] BACKEND-FILT-002: Genre Filter: English Slug ('action') vs Uzbek DB
  Evidence: API IDs: [1, 2, 4, 11, 12, 13, 14, 16, 20, 24, 30], Uzbek IDs in DB: [1, 2, 4, 11, 12, 13, 14, 16, 20, 25, 27, 30, 35]
  ```
- **Ildiz sabab:** UI inglizcha slug yuboradi, DB da esa janrlar o'zbekcha saqlangan. Backendda slugni o'zbekcha nomga (va aksincha) xaritalovchi ikki tomonlama lug'at qo'llanilmagan.

---

### `FILTER-003` (Kritik): `/movies` da "Reyting bo'yicha saralash" (`?sort=rating`) butunlay ishlamaydi
- **Og'irlik:** Yuqori (High)
- **Sahifa / Komponent:** `website/app/movies/page.tsx` & `backend/app/api/v1/movies.py:288` & `movie_repo.py:270`
- **Qadamlar:**
  1. `/movies` sahifasida 5-dropdown "Reyting bo'yicha saralash" ni tanlash.
  2. URL ga `?sort=rating` yoziladi.
- **Kutilgan:** Filmlar IMDb reytingi bo'yicha kamayish tartibida (9.5, 9.0, 8.9...) chiqishi kerak.
- **Haqiqiy holat:** Filmlar doimiy `order_by(MovieModel.id.asc())` (7.2, 8.4, 6.4...) eng eski qo'shilgan tartibda chiqadi.
- **Terminal dalili:**
  ```
  [FAIL] BACKEND-FILT-005: Sort by Rating (sort=rating)
  Evidence: API returned IDs in default id.asc order: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] (ratings: [7.2, 8.4, 6.4, 7.3, 8.9, 7.0, 8.8, 8.7, 7.6, 7.9]). Expected Oracle top rating IDs: [30, 31, 21, 20, 5, 29, 7, 32, 22, 8] (ratings: [9.5, 9.0, 9.0, 9.0, 8.9, 8.8, 8.8, 8.7, 8.7, 8.7])
  Root Cause: GET /movies endpoint has NO 'sort' parameter in route definition. Backend completely ignores ?sort=rating and executes hardcoded query.order_by(MovieModel.id.asc()).
  ```
- **Ildiz sabab:** `movies.py:290` da `sort` query parametri e'lon qilinmagan; `movie_repo.py:270` da esa faqat `order_by(MovieModel.id.asc())` qotirilgan.

---

### `FILTER-004` (Kritik): `/series` da "Reyting bo'yicha saralash" (`?sort=rating`) mavjud emas
- **Og'irlik:** Yuqori (High)
- **Sahifa / Komponent:** `website/app/series/page.tsx` & `backend/app/api/v1/series.py:119`
- **Qadamlar:**
  1. `/series` sahifasida saralashni tanlash.
- **Kutilgan:** Seriallar reytingi bo'yicha saralanishi.
- **Haqiqiy holat:** `GET /series` marshruti `sort` parametrini qabul qilmaydi.
- **Terminal dalili:**
  ```
  [FAIL] BACKEND-FILT-011: Series Sort by Rating (?sort=rating)
  Evidence: GET /api/v1/series does NOT declare a 'sort' query parameter. It is ignored.
  ```

---

### `FILTER-005` (O'rta): `CatalogGrid.tsx` da seriallar paginationida filtrlar yo'qolib ketadi
- **Og'irlik:** O'rta (Medium)
- **Sahifa / Komponent:** `website/components/catalog/CatalogGrid.tsx:65-70`
- **Qadamlar:**
  1. `/series` sahifasida Janr yoki Yil tanlash.
  2. Pastga tushib "Yana yuklash" (Load More) tugmasini bosish.
- **Kutilgan:** 2-sahifada ham tanlangan janr va yil bo'yicha seriallar kelishi.
- **Haqiqiy holat:** `loadMore` funksiyasi seriallar uchun faqat `/series?skip=...&category_id=...` yuboradi; `genre`, `year`, `search` parametrlari tashlab yuboriladi!

---

### `FILTER-006` (O'rta): `/search` sahifasida natijalarni filtrlash imkoni yo'q
- **Og'irlik:** O'rta (Medium)
- **Sahifa / Komponent:** `website/app/search/page.tsx` & `backend/app/api/v1/movies.py:328`
- **Qadamlar:**
  1. `/search` sahifasida qidiruv so'zini kiritish (masalan "Olam").
  2. Chiqqan natijalarni Yil yoki Turi bo'yicha saralamoqchi bo'lish.
- **Kutilgan:** Qidiruv natijalarini yil, janr, tur va reyting bo'yicha toraytirish paneli bo'lishi.
- **Haqiqiy holat:** UI da filtr paneli yo'q, backend API da ham bu parametrlar qabul qilinmaydi.

---

### `FILTER-007` (Xavfsizlik / QA): Aktyorlar filmografiyasida Pending/Draft filmlar "Bazada bor" deb chiqadi
- **Og'irlik:** Yuqori (High)
- **Sahifa / Komponent:** `backend/app/api/v1/actors.py:390-410`
- **Qadamlar:**
  1. Aktyor filmografiyasi modalini ochish (`/actors/{person_id}/movies`).
  2. Aktyorning bizning bazada `pending` yoki `draft` holatdagi filmi bo'lsa:
- **Kutilgan:** Oddiy foydalanuvchiga faqat `published` filmlar "Bazada mavjud" deb ko'rinishi kerak.
- **Haqiqiy holat:** `MovieModel.tmdb_id.in_(tmdb_ids)` so'rovida `publish_status == 'published'` tekshiruvi yo'q! Pending filmlar ham yashil "Tomosha qilish" tugmasi bilan chiqadi, bosilsa 404 beradi.
- **Terminal dalili:**
  ```
  [FAIL] BACKEND-FILT-015: Actors Filmography: Pending/Draft movie leakage
  Evidence: actors.py lines 390-410 queries MovieModel and SeriesModel by tmdb_id WITHOUT publish_status='published' check!
  ```

---

## 4. Foydalanuvchidan Qaror Talab Qilinadigan Masalalar (Decisions Needed)

1. **Rejissyorlar masalasi:** Hozirda alohida `/directors` sahifasi yo'q. Qaysi yo'lni tanlaymiz?
   - *Variant A (Tavsiya etiladi):* `/actors` sahifasini "Ijodkorlar" (Aktyorlar va Rejissyorlar) sifatida saqlab, yuqoriga 2 ta tab qo'shish: "Barchasi", "Aktyorlar", "Rejissyorlar".
   - *Variant B:* Alohida `/directors` sahifasi va `GET /directors` endpointini yaratish.
2. **"Bo'lim" atamasi:** `UnifiedFilterBar` dagi "Bo'lim" dropdownini aniqlashtirish:
   - *Variant A (Tavsiya etiladi):* UI da nomini "Kategoriya" deb o'zgartirish (chunki u `category_id` ni boshqaradi).
   - *Variant B:* "Bo'lim" nomini qoldirib, uni `pages` jadvali (`page_id`) bilan bog'lash, kategoriyalar uchun esa alohida dropdown qilish.
3. **Ko'p tanlovli Janr (Multi-select Genre):**
   - Hozirgi `UnifiedFilterBar` faqat bitta janr tanlashga mo'ljallangan (Dropdown). Kelajakda bir vaqtning o'zida bir nechta janr tanlash (masalan: Jangari AND Komediya) kerakmi yoki bitta janr tanlovi yetarlimi?
