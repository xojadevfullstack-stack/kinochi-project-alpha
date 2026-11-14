# KINOCHI STABILIZATION PROJECT — GUEST FLOW REPAIR REPORT

**Sana:** 2026-11-14  
**Holat:** COMPLETED (Barcha 6 ta issue to‘liq bartaraf etildi)  
**Metodologiya:** Reproduce → RED Test → Root Cause Analysis → Minimal Fix → GREEN Test → Regression Suite → Commit

---

## 1. IJRO XULOSASI (EXECUTIVE SUMMARY)

Guest Flow auditida aniqlangan 6 ta muammo (2 ta P0, 2 ta P1, 2 ta P2) bo‘yicha to‘liq ta’mirlash ishlari amalga oshirildi. Har bir muammo uchun dastlab nosozlikni isbotlovchi avtomatlashtirilgan test yozildi (RED), so‘ngra minimal va maqsadli tuzatish kiritildi (GREEN) va mavjud tizimning regressiyasi tekshirildi.

| Issue ID | Komponent / Fayl | Daraja | Holat | Avtomatlashtirilgan Test | Commit Hash |
|---|---|---|---|---|---|
| **GUEST-ISSUE-001** | `backend/.../movie_repo.py` | P0 | **RESOLVED** | `tests/audit2/test_guest_flow_repair.py::test_guest_issue_001_movie_search_no_name_error` | `9877842` |
| **GUEST-ISSUE-002** | `backend/app/api/v1/collections.py` | P0 | **RESOLVED** | `tests/audit2/test_guest_flow_repair.py::test_guest_issue_002_collections_no_n_plus_one` | `422be3c` |
| **GUEST-ISSUE-003** | `website/components/TelegramWatchButton.tsx` | P1 | **RESOLVED** | `website/tests/telegram_watch_modal.spec.ts` | `05d4216` |
| **GUEST-ISSUE-004** | `bot/handlers/browsing.py` | P1 | **RESOLVED** | `bot/tests/test_browsing_missing_video.py` | `b5e0b9c` |
| **GUEST-ISSUE-005** | `website/components/home/ContinueWatchingSection.tsx` | P2 | **RESOLVED** | `website/tests/continue_watching_sync.spec.ts` | `6f5026e` |
| **GUEST-ISSUE-006** | `website/app/test-auth/page.tsx` | P2 Sec | **RESOLVED** | `website/tests/auth_security.spec.ts` | `22bda32`, `815515d` |

---

## 2. HAR BIR ISSUE BO‘YICHA BATAFSIL TA’MIRLASH BAYONI

### GUEST-ISSUE-001: Film qidiruvida `NameError: name 're' is not defined` (P0)
- **Root Cause:** `movie_repo.py` faylida 341-qatorda `re.split` chaqirilgan, biroq fayl boshida `import re` moduli import qilinmagan. Bu qidiruv so‘rovi kelganda HTTP 500 xatosiga olib kelgan.
- **RED Test Dalili:**
  ```text
  FAILED tests/audit2/test_guest_flow_repair.py::test_guest_issue_001_movie_search_no_name_error
  NameError: name 're' is not defined
  ```
- **Tuzatish:** `backend/app/infrastructure/db/repositories/movie_repo.py` import qismiga `import re` qo‘shildi.
- **GREEN Test Dalili:** `1 passed in 1.02s`. Real bazada `Avatar` va `q=kino` qidiruvlari HTTP 200 bilan natijalar qaytardi.

---

### GUEST-ISSUE-002: To‘plamlarda N+1 DB so‘rovlari va 15s Timeout (P0)
- **Root Cause:** `GET /api/v1/collections` endpointida har bir to‘plam uchun alohida siklda `count` va `items` so‘rovlari yuborilgan. Shuningdek, `CollectionModel` va `CollectionItemModel` modellaridagi `lazy="selectin"` parametrlari tufayli keraksiz `movies`, `categories`, `translations`, `pages` jadvallari ketma-ket chaqirilgan. Natijada 5 ta to‘plam uchun 37 ta DB so‘rovi bajarilgan.
- **RED Test Dalili:**
  ```text
  AssertionError: N+1 query bottleneck detected! Expected <= 4 DB queries, but executed 37 queries.
  assert 37 <= 4
  ```
- **Tuzatish:**
  1. `noload(CollectionModel.items), noload(CollectionModel.subscriptions)` qo‘llandi.
  2. To‘plamlar soni (`counts_map`) bitta guruhlangan so‘rov (`GROUP BY collection_id`) orqali hisoblandi.
  3. Prevyu posterlari bitta SQL Window Function (`row_number() OVER (PARTITION BY collection_id ORDER BY chronological_order ASC)`) orqali olindi.
  4. DB so‘rovlari soni to‘plamlar sonidan qat'i nazar **aniq 3 ta so‘rovga (O(1))** tushirildi (37 ta so‘rovdan 3 taga, ya'ni 92% qisqarish).
- **GREEN Test Dalili:** `tests/audit2/test_guest_flow_repair.py` muvaffaqiyatli o‘tdi. `backend/tests/test_filter_collections_item_count.py` regressiyasi 100% o‘tdi.

---

### GUEST-ISSUE-003: `TelegramWatchButton.tsx` soxta yuborish xabari (P1)
- **Root Cause:** Foydalanuvchi "Telegram orqali ko'rish" tugmasini bosganda, faqat brauzerda deep-link (`https://t.me/...`) ochilar edi. Biroq modal oynada foydalanuvchiga yolg‘on `Muvaffaqiyatli yuborildi!` va `Telegram botingizga video fayl va tomosha qilish havolasi yuborildi` deb ko‘rsatilardi.
- **RED Test Dalili:**
  ```text
  Error: expect(received).not.toContain(expected)
  Expected substring: not "Muvaffaqiyatli yuborildi"
  ```
- **Tuzatish:**
  1. Yashil soxta muvaffaqiyat belgisi o‘rniga Telegram brend ko‘rinishidagi `#229ED9` ochilish indikatori o‘rnatildi.
  2. Holat yozuvi: `Telegram bot ochilmoqda`.
  3. Sarlavha: `Telegram botda davom eting`.
  4. Tavsif: `{mediaTitle} videosini tomosha qilish uchun Telegram botga havola ochildi. Botda «Start» yoki «Boshlash» tugmasini bosing.` deb to‘g‘ri va aniq yo‘naltirildi.
- **GREEN Test Dalili:** `website/tests/telegram_watch_modal.spec.ts` — `1 passed (954ms)`.

---

### GUEST-ISSUE-004: Botda video bo‘lmaganda soxta "Video yuklanmoqda..." (P1)
- **Root Cause:** Film yoki serial qismiga video fayl yuklanmagan bo‘lsa (`translations = []`), `send_movie_to_user` `False` qaytarar edi. `browsing.py` esa foydalanuvchiga go‘yoki fonda avtomatik yuklash ketayotgandek `"⏳ Video yuklanmoqda..."` deb yolg‘on xabar yuborardi.
- **RED Test Dalili:**
  ```text
  AssertionError: Fake video loading message was sent!
  assert 'Video yuklanmoqda' not in '⏳ Video yuklanmoqda...'
  ```
- **Tuzatish:** `bot/handlers/browsing.py` da kontentda video tarjimalari mavjudligi avvaldan tekshirildi. Agar video yuklanmagan bo‘lsa:
  - Film uchun: `"⚠️ Ushbu film uchun video fayl hali yuklanmagan."`
  - Qism uchun: `"⚠️ Ushbu qism uchun video fayl hali yuklanmagan."`
  - Agar yuborishda texnik xatolik bo‘lsa: `"⚠️ Videoni yuborishda xatolik yuz berdi. Iltimos, birozdan so'ng qayta urinib ko'ring."`
- **GREEN Test Dalili:** `bot/tests/test_browsing_missing_video.py` — `2 passed in 3.93s`. To‘liq bot test to‘plami: `98 passed in 7.63s`.

---

### GUEST-ISSUE-005: `ContinueWatchingSection.tsx` soxta 60%/65% progress (P2)
- **Root Cause:** Kodda video progressi bo‘lmagan har qanday holat uchun hardcoded `55`, `65` va `60` foiz qiymatlari sun'iy ravishda berilgan edi.
- **RED Test Dalili:**
  ```text
  Error: expect(received).toBeUndefined()
  Received: 60
  Received: 65
  ```
- **Tuzatish:** Soxta foizlar olib tashlandi. Agar progress real mavjud bo‘lsa (`typeof item.progress === 'number'`), saqlanadi; mavjud bo‘lmasa `undefined` qoldiriladi va kartochkada toza `Davom etmoqda` status badge'i ko‘rsatiladi.
- **GREEN Test Dalili:** `website/tests/continue_watching_sync.spec.ts` — `4 passed (1.6s)`.

---

### GUEST-ISSUE-006: `test-auth/page.tsx` diagnostika sahifasi (P2 Security)
- **Root Cause:** `/test-auth` marshruti production muhitida ochiq qolgan bo‘lib, auth token va foydalanuvchi parametrlarini ko‘rsatishi mumkin edi.
- **RED Test Dalili:**
  ```text
  Error: expect(received).toContain("notFound")
  ```
- **Tuzatish:** Sahifaga `if (process.env.NODE_ENV === "production") { notFound(); }` xavfsizlik to‘sig‘i qo‘shildi.
- **GREEN Test Dalili:** `website/tests/auth_security.spec.ts` — `1 passed (910ms)`. TypeScript typecheck (`npx tsc --noEmit`) 0 xato bilan o‘tdi.

---

## 3. REGRESSIYA VA TIZIM VERIFIKATSIYASI

Barcha tuzatishlardan so‘ng umumiy test sinovlari o‘tkazildi:
1. **Backend Tests:** `tests/audit2/test_guest_flow_repair.py` + `backend/tests/test_filter_collections_item_count.py` → `3 passed`.
2. **Bot Tests:** `bot/tests/` → `98 passed in 7.63s` (100% GREEN).
3. **Website Tests:** `website/tests/` Playwright testlari → `6 passed in 1.6s` (100% GREEN).
4. **Website TypeScript:** `npx tsc --noEmit` → 0 errors.
5. **Admin Panel TypeScript:** `npx tsc --noEmit` → 0 errors.

Guest Flow to‘liq barqarorlashtirildi va navbatdagi bosqich (USER FLOW) uchun tayyor.
