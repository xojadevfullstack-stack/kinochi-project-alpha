# Kinochi Loyihasi Holati (Project State)

Ushbu hujjat loyihaning haqiqiy kod holatini aks ettiruvchi dolzarb context hujjatidir. (So'nggi yangilanish: **2026-07-11**). AI va Dasturchilar uchun loyihaning arxitekturasi, mavjud yechimlari va joriy statusini saqlab turadi.

## Loyihaning Umumiy Holati

Loyiha to'liq MVP holatiga kelgan va **Production muhitiga joylangan (Deployed)**:
- **Frontend (Website & Admin Panel):** Vercel
- **Backend & Telegram Bot:** Render
- **Database:** Neon (PostgreSQL)
- **Redis (Kesh & Limitlar):** Upstash

Asosiy maqsad (bot orqali kino/serial tarqatish, veb-sayt orqali SEO qidiruv, va admin panel orqali boshqarish) to'liq amalga oshirilgan.

---

## 1. BACKEND (backend/)
**Holati: To'liq shakllangan, Clean Architecture qoidalarida ishlaydi.**

**1.1 Domain va Modullar:**
- `movies`: Alohida filmlar CRUD amallari.
- `series` (YANGI): Seriallar arxitekturasi **filmlardan butunlay ajratilgan (decoupled)**. `Series -> Season -> Episode` iyerarxiyasida ishlaydi. 
- `categories`: Janrlar va toifalar.
- `users`: Telegram bot orqali ro'yxatdan o'tganlar.
- `channels`: Majburiy obuna kanallari (Redis orqali tekshiriladi).
- `broadcasts`: Barcha foydalanuvchilarga xabar yuborish mexanizmi.
- `admin_users` / `auth`: JWT (Access/Refresh token) asosida ishlovchi admin avtorizatsiyasi.

**1.2 Alembic Migratsiyalar:**
- `alembic/versions/` papkasida migratsiyalar ketma-ketligi mavjud.
- *Eslatma:* Migratsiyani autogenerate qilish uchun local/remote DB ishlayotgan bo'lishi shart. Agar `movies.is_series` yoki eski jadvallar qolib ketgan bo'lsa, manual `alembic upgrade head` qilinishi kutilmoqda.

**1.3 API Xavfsizligi va Avtorizatsiya:**
- `/auth/me`, `/movies`, `/series`, `/categories`, `/channels`, `/broadcasts` endpointlarining mutatsion qismlari (POST, PUT, DELETE) `get_current_admin` bilan to'liq yopilgan.
- Keng omma (Bot va Vebsayt) uchun faqat o'qish (GET) va ayrim maxsus (Register) post endpointlar ochiq qoldirilgan.

---

## 2. BOT (bot/)
**Holati: Funksional va Barqaror.**

**2.1 Mexanizm va Funksiyalar:**
- **Polling / Web Server:** Bot Render.com da port band qilishi va o'chib qolmasligi uchun `main.py` da "dummy web server" (Aiohttp yordamida `0.0.0.0:PORT`) bilan birgalikda Polling rejimida ishga tushirilgan.
- **Handlers:** `/start` deep-linking (kino yoki epizodni avtomatik berish), qidiruv (`search`), seriallarni qadam-baqadam tanlash menyulari.
- **Middleware:** `subscription_check.py` orqali baza va redisni tekshirib foydalanuvchini majburiy kanallarga a'zolikka majburlaydi.
- **Kino berish:** Fayl ID lari backenddan keladi va bot bevosita Telegram serverlaridan videoni forward/copy qiladi.

---

## 3. ADMIN PANEL (admin-panel/)
**Holati: To'liq ishlayapti, UI/UX yechimlari bilan boyitilgan.**

**3.1 Asosiy qismlar:**
- **Auth:** Login orqali kirish (Cookie-based JWT ulanishi).
- **Movies:** Kino ma'lumotlarini kiritish va videoni bevosita Telegram yopiq kanaliga yuklash.
- **Series (Yangi):** Seriallarni `Series -> Season -> Episode` zanjiri orqali boshqarish. **Video yuklash jarayoni bevosita "Episode (Qism)" yaratish formasi bilan bitta "Saqlash" tugmasiga birlashtirilgan** (ikkinchi qadamga hojat qolmagan).
- **Channels & Broadcasts:** Obuna kanallarini qo'shish va reklama jo'natish paneli.

---

## 4. WEBSITE (website/)
**Holati: To'liq SEO-optimallashtirilgan Katalog.**

**4.1 Xususiyatlari:**
- Next.js (App Router) da yozilgan, Server-Side Rendering (SSR) dan faol foydalanilgan.
- `app/sitemap.ts` va `app/robots.ts` orqali avtomatlashtirilgan SEO fayllar generatsiyasi.
- Kino va Seriallarni qidirish, ko'rish hamda bevosita botga yo'naltiruvchi `TGSaytga o'tish` deep-linklari.

---

## 5. MUHIM TEXNIK QOIDALAR VA QO'LLANMA (.agents/rules)

1. **Clean Architecture (`backend/`):** Routerni to'g'ridan-to'g'ri Repositoriyga ulash taqiqlanadi. Albatta Service qatlami bo'lishi kerak. Pydantic modellarga `ConfigDict(from_attributes=True)` yozish yoddan chiqmasin.
2. **Thin Client (`bot/` va `website/`):** Ular hech qachon bazaga to'g'ridan-to'g'ri ulanmaydi, barcha ma'lumot HTTP so'rov orqali backend API'dan olinadi.
3. **Session Cookie:** Admin panelda HTTP klient albatta `credentials: "include"` argumenti bilan fetch qilishi shart.
4. **Cloud Deployment:** Render'da botning o'chib qolmasligi uning ichki aiohttp dummy-serveri hisobiga amalga oshmoqda. Buni o'chirish taqiqlanadi (Webhook'ga o'tilmaguncha).

---

## KEYINGI QADAM (NEXT STEPS)

- **Series (Seriallar) bo'limi (Part 2 & Part 3):** Backend va Admin Panel to'liq mustaqil Series/Season/Episode arxitekturasiga o'tkazildi. Qismlar (Episodes) uchun video yuklash va message_id ulash tizimi qo'shildi. Bot qismida Serial qismlari uchun navigatsiyali Inline Keyboard qo'shildi. Seriallarga Kategoriyalar bog'lash to'liq joriy qilindi. **Season uchun Poster URL qo'shildi va Vebsaytda Serial qismlari xronologik dizaynga (timeline) o'tkazildi.**
- Hozirgi kod bazasi kengayishga to'liq tayyor. Keyingi qadam: Ko'p-dublyaj (studiya) tanlash tizimi (Part 4) va Admin Panelni sayqallash (Part 5).
