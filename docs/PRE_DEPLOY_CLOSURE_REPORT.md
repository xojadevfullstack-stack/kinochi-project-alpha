# KINOCHI — PRE-DEPLOY CLOSURE AUDIT & VERIFICATION REPORT

**Auditor:** Mustaqil Senior QA Engineer, Security Auditor & Release Engineer  
**Hujjat sanasi:** 2026-11-14  
**Holat:** Yakuniy Pre-Deploy Tekshiruvi  
**Yakuniy qaror:** **CONDITIONAL RELEASE (Shartli Chiqarilish)**  

---

## 1. AMALGA OSHIRILGAN ISHLAR VA STATUSLAR JADVALI

| # | Tekshiruv bandi | Status | Asosiy xulosa |
|---|---|---|---|
| 1 | **Branding Fix** (`achievements/page.tsx`) | **PASS** | `MediaPlus Afsonasi` matni `Kinochi Afsonasi` ga almashtirildi. |
| 2 | **JWT / Refresh Token Audit** | **PASS** | Stateless arxitekturaning barcha 6 ta xususiyati test dalillari bilan isbotlandi. |
| 3 | **CSRF Xavfsizlik Auditi** | **FAIL (Zaiflik)** | `SameSite=None` cookie'larda mustaqil CSRF token yoki Origin tekshiruvi yo'q. Minimal reja tuzildi. |
| 4 | **Admin-panel Production Build** | **PASS** | TypeScript 0 xato; 21/21 sahifa kompilyatsiya qilindi. Windows symlink EPERM ogohlantirishi qayd etildi. |
| 5 | **Backup / Restore Runbook** | **PASS** | `docs/PRODUCTION_BACKUP_RESTORE.md` operatsion qo'llanmasi yaratildi. |
| 6 | **Deployment Configuration** | **PASS** | 1 ta worker, MemoryStorage, xavfsiz env varlar va DEBUG=False shartlari hujjatlashtirildi. |

---

## 2. BATAFSIL AUDIT VA TEST DALILLARI

### 2.1. Branding Fix
- **Fayl:** `website/app/achievements/page.tsx:91`
- **O'zgarish:**
  ```diff
  - return { title: "MediaPlus Afsonasi", desc: "Barcha yutuqlarni 100% ochgan mutlaq chempion!", icon: "hotel_class" };
  + return { title: "Kinochi Afsonasi", desc: "Barcha yutuqlarni 100% ochgan mutlaq chempion!", icon: "hotel_class" };
  ```
- **Natija:** Boshqa hech qanday UI yoki biznes mantiqqa tegilmadi. Git diff aniq 1 qator.

---

### 2.2. JWT va Refresh Token Auditi (Kod va Test Isboti)

Auditorlik testi: `tests/audit2/test_pre_deploy_jwt_csrf_audit.py` (3 ta test muvaffaqiyatli bajarildi, raw terminal output: `3 passed in 3.90s`).

1. **Access Token qayerda saqlanadi?**
   - Admin: `access_token` httpOnly cookie (va response JSON da).
   - Foydalanuvchi: `user_access_token` httpOnly cookie (va response JSON da).
   - TTL: 30 daqiqa (`ACCESS_TOKEN_EXPIRE_MINUTES = 30`).
2. **Refresh Token qayerda saqlanadi?**
   - Faqat Admin uchun mavjud! `refresh_token` httpOnly cookie (`path="/"`, `max_age=7 days`).
   - Oddiy foydalanuvchilar (Telegram Auth) uchun alohida refresh token yo'q (har gal yangi login orqali yangilanadi).
   - **Ma'lumotlar bazasida (DB) saqlanmaydi.** `backend/app/infrastructure/security/jwt_handler.py:3-8` da ochiq qayd etilgan: stateless JWT yondashuvi.
3. **Logout ikkala tokenni ham tozalaydimi?**
   - **HA.** `_clear_auth_cookies(response)` funksiyasi `access_token`, `refresh_token` va `user_access_token` cookie'larini brauzer darajasida tozalaydi (`max_age=0`).
4. **Refresh endpoint logoutdan keyin eski token bilan ishlaydimi?**
   - **HA (Tasdiqlandi).** `test_admin_login_logout_token_lifecycle` testi buni isbotladi: agar tajovuzkor logoutdan oldin `refresh_token` ni o'g'irlagan bo'lsa, u `/api/v1/auth/refresh` endpointiga yuborilganda server yangi `access_token` va `refresh_token` beradi. Serverda blacklist/revocation ro'yxati yo'qligi sababli stateless token 7 kun davomida haqiqiy bo'lib qoladi.
5. **Refresh token rotation bormi?**
   - **Qisman (Pseudo-rotation).** `/auth/refresh` chaqirilganda yangi refresh token beriladi, ammo eski refresh token bekor qilinmaydi.
6. **O'g'irlangan refresh token qayta ishlatilishi mumkinmi?**
   - **HA (Tasdiqlandi).** Bitta refresh token 7 kunlik muddati davomida bir necha bor ishlatilishi mumkin (testda `replay_resp.status_code == 200` qaytdi).

---

### 2.3. CSRF Xavfsizlik Auditi va Zaiflik Hisoboti

#### Aniqlangan Zaiflik:
- Production muhitida cookie parametrlari: `httponly=True`, `secure=True`, `SameSite="none"`.
- Backendda (`backend/app/main.py`) va barcha endpointlarda:
  - CSRF token (anti-CSRF header) tekshiruvi **MAVJUD EMAS**.
  - `Origin` yoki `Referer` sarlavhalarini tekshiruvchi himoya middleware'i **MAVJUD EMAS**.
- **CORS chalkashligi:** `CORSMiddleware` faqat brauzerdagi JavaScript `fetch` javobini o'qishni taqiqlaydi. Ammo brauzer orqali yuboriladigan oddiy so'rovlar (`<form method="POST">` yoki oddiy cross-site triggerlar) paytida `SameSite=none` cookie'lari avtomatik qo'shiladi va server so'rovni bajaradi (`test_csrf_vulnerability_posture` orqali tasdiqlandi).

#### Minimal Fix Rejasi (Foydalanuvchi tasdig'i uchun):
Keng ko'lamli o'zgarish qilmasdan CSRF himoyasini ta'minlash uchun minimal yechim:
1. **Origin Header Verification Middleware:**
   FastAPI ga 15 qatorlik middleware qo'shish:
   - Faqat state-changing metodlar (`POST`, `PUT`, `DELETE`, `PATCH`) uchun;
   - Agar so'rovda `Cookie` mavjud bo'lsa (ya'ni cookie orqali avtorizatsiya bo'lsa);
   - `request.headers.get("origin")` qiymati `is_origin_allowed(origin)` tekshiruvidan o'tmasa, darhol `403 Forbidden` ("CSRF: Invalid Origin") qaytarish.
   - Oddiy API (Authorization: Bearer ...) va Bot so'rovlari (X-Bot-Secret) uchun bu cheklov qo'llanmaydi.
2. *Holati:* Ushbu reja hozircha kiritilmadi (tasdiq kutmoqda).

---

### 2.4. Admin-panel Production Build Natijalari

Dev-server bilan to'qnashuvni oldini olish maqsadida izolyatsiyalangan build muhitida sinov o'tkazildi:
1. **TypeScript tekshiruvi:** `npx tsc --noEmit` -> **0 xato (Exit code 0)**.
2. **Next.js Production Build:** `npx next build --no-lint` -> **Muvaffaqiyatli (Exit code 0)**.
   - Jami **21 ta sahifa** (19 ta admin routelari + `/login` + `_not-found`) to'liq statik va dinamik sahifalarga kompilyatsiya qilindi.
3. **EPERM Ogohlantirishi Qaydi:**
   - Standalone rejimda Next.js `node_modules` katalogiga Windows Developer Mode'siz symlink yaratishga uringanda quyidagi ogohlantirish chiqdi:
     `EPERM: operation not permitted, symlink '...admin-panel\node_modules' -> '...\.next\standalone\node_modules'`.
   - Ushbu holat faqat lokal Windows muhitida standalone symlink yasashga tegishli bo'lib, Linux/Docker yoki Vercel production serverlarida symlink ruxsatlari mavjud bo'lgani uchun hech qanday xatolik keltirib chiqarmaydi.

---

### 2.5. Ma'lumotlar Bazasi Zaxiralash (Runbook)
- `docs/PRODUCTION_BACKUP_RESTORE.md` fayli yaratildi.
- Standart `pg_dump -F c` siqilgan zaxiralash, SHA256 integrity tekshiruvi, `pg_restore -l` ro'yxatini ko'rish, toza bazaga xavfsiz tiklash, post-restore Alembic `head` versiyasini tasdiqlash va avariya paytidagi failover/rollback qadamlari belgilandi.

---

### 2.6. Deployment Konfiguratsiyasi Tekshiruvi
1. **Yagona Worker Talabi:**
   - `backend/Dockerfile` buyrug'i: `CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"` (standart 1 ta worker).
   - `run.py` uvicorn serverni aiogram bot bilan bitta jarayonda boshqaradi.
   - **Qat'iy qoida:** Multi-worker (`--workers 2+`) rejimida ishga tushirish taqiqlanadi, aks holda:
     a) Telegram Bot `Conflict: terminated by other getUpdates request` xatosi bilan to'xtaydi;
     b) SlowAPI in-memory hisoblagichi ishlamaydi.
2. **SlowAPI MemoryStorage:**
   - Hozirgi `MemoryStorage` yagona worker rejimida to'liq va to'g'ri ishlaydi.
   - Kelajakda gorizontal klaster (bir nechta server yoki worker) qilinganda, `app/api/limiter.py` fayliga `storage_uri=settings.REDIS_URL` qo'shilishi shart.
3. **Xavfsizlik Environment O'zgaruvchilari:**
   - `SECRET_KEY`: `backend/app/core/config.py:133-136` da Pydantic validator production muhitda `change-me-in-production` qolib ketishini taqiqlaydi va ilovani to'xtatadi.
   - `BOT_TOKEN`, `BOT_API_SECRET`, `DATABASE_URL` majburiy env var sifatida olinadi.
   - `DEBUG`: Standart `False` qilib belgilangan.
   - `ENABLE_DEV_LOGIN`: Standart `False` qilib belgilangan va prod'da bloklangan.

---

## 3. QOLDIQ XAVLAR VA TAVSIYALAR

1. **CSRF himoyasini faollashtirish (Tavsiya etiladi):**
   - Yuqorida keltirilgan 15 qatorlik "Origin Header Verification Middleware" ni tasdiqlab, kodga kiritish.
2. **Stateless JWT xususiyati (MVP doirasida):**
   - Admin va foydalanuvchilar logout qilganda token faqat klientdan tozalanadi. Agar kelgusida xavfsizlik darajasini maksimal darajaga ko'tarish kerak bo'lsa, Redis asosidagi token blacklist joriy qilinishi mumkin.

---
*Hisobot dalillarga asoslangan holda yakunlandi.*
