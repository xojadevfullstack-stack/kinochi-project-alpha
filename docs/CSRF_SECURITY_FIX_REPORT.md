# KINOCHI — CSRF SECURITY FIX REPORT

**Xavfsizlik Auditor & Muhandis:** Mustaqil Senior QA & Security Engineer  
**Sana:** 2026-11-14  
**Topshiriq:** CSRF (Cross-Site Request Forgery) Zaifligini To'liq va Xavfsiz Bartaraf Etish  
**Yakuniy status:** **PASS (To'liq Yopildi)**  

---

## 1. AMALGA OSHIRILGAN ISHLAR VA NATIJALAR QISQACHA

| # | Tekshiruv / Himoya elementi | Status | Izoh |
|---|---|---|---|
| 1 | **Safe Methods (GET, HEAD, OPTIONS)** | **PASS** | Xavfsiz metodlar cheklovsiz ishlaydi (RFC 7231). |
| 2 | **Begona Origin (Attacker)** | **PASS** | State-changing so'rovlarda ruxsat etilmagan Origin darhol `403 Forbidden` oladi. |
| 3 | **Ishonchli Origin (Frontend)** | **PASS** | `website` va `admin-panel` originlari to'liq qabul qilinadi. |
| 4 | **Origin Yo'q (Cookie bilan)** | **PASS** | Cookie orqali avtorizatsiya bo'lib, Origin ham, Referer ham bo'lmasa yoki Referer begona bo'lsa `403 Forbidden`. |
| 5 | **Origin Yo'q (Referer to'g'ri)** | **PASS** | Brauzer Origin yubormagan, lekin Referer ishonchli domen bo'lsa so'rovga ruxsat beriladi. |
| 6 | **Server-to-Server / Bot** | **PASS** | Telegram Bot (`X-Bot-Secret`) va API (`Bearer`) so'rovlari cookiesiz ishlaydi va to'sqinliksiz o'tadi. |
| 7 | **Admin va User Auth** | **PASS** | Admin (`/admin/cache/flush`, `/auth/refresh`, `/auth/logout`) va User (`/users/me/history`) to'liq himoyalandi. |
| 8 | **Test Qamrovi** | **PASS** | 7 ta yangi maxsus test + 30 ta audit2 regresiya testlari (100% Yashil). |

---

## 2. DASTLABKI TAHLIL VA DISCOVERY NATIJALARI

1. **Cookie orqali autentifikatsiya qilinadigan state-changing endpointlar:**
   - `AdminUserModel`: `/api/v1/auth/logout`, `/api/v1/auth/refresh`, hamda barcha CRUD admin endpointlari (`/api/v1/movies`, `/api/v1/series`, `/api/v1/categories`, `/api/v1/channels`, `/api/v1/sources`, `/api/v1/admin/cache/flush`, va h.k.).
   - `UserModel`: `/api/v1/users/me/history` (DELETE), `/api/v1/reviews` (POST/DELETE), `/api/v1/content-requests` (POST), `/api/v1/series-subscriptions` (POST/DELETE), `/api/v1/reports` (POST).
2. **Production ishonchli originlar:**
   - `https://kinochi-project-alpha.vercel.app` (Asosiy veb-portal)
   - `https://kinochi-admin.vercel.app` (Ma'muriyat paneli)
   - `https://kinochi.uz` (Production shaxsiy domen)
   - `https://admin.kinochi.uz` (Admin shaxsiy domen)
   - Vercel preview deploy regex: `^https:\/\/(kinochi-project-alpha|kinochi-admin)(?:-(?:git-[a-zA-Z0-9_-]+|[a-z0-9]{9,}(?:-[a-zA-Z0-9_-]+)?))?\.vercel\.app$`
   - Lokal dev: `http://localhost:3000`, `http://localhost:3001`, `http://127.0.0.1:3000`, `http://127.0.0.1:3001`, `http://localhost:8000`, `http://test`.
3. **Nega `SameSite=None` ishlatilgan?**
   - Frontend (`vercel.app`) va Backend (`onrender.com` / VPS) turli domenlarda joylashgan. Brauzer cross-origin `fetch` so'rovlarida cookie yuborishi uchun `SameSite=None; Secure` majburiy talab etiladi.
   - Ammo `SameSite=None` uchinchi tomon saytlaridan (`evil.com`) yuborilgan so'rovlarda ham cookie'lar avtomatik qo'shilishiga olib kelgani sababli, alohida CSRF himoyasi zarur bo'lib qolgan edi.
4. **CORS nimaga CSRF himoyasi emas?**
   - CORS faqat JavaScript orqali javobni o'qishni taqiqlaydi. Oddiy HTML `<form action="https://api.../flush" method="POST">` yuborilganda server so'rovni baribir bajaradi. Shuning uchun mustaqil Origin/Referer tekshiruvi kiritildi.

---

## 3. AMALGA OSHIRILGAN HIMOYALASH MEXANIZMI

Fayl: `backend/app/main.py`  
Yaratilgan middleware: `csrf_origin_protection_middleware`

### Himoya Algoritmi:
```text
So'rov kelganda:
├── 1. Metod xavfsizmi? (GET, HEAD, OPTIONS)
│      └── HA: O'tkazib yubor (call_next).
│
├── 2. Origin sarlavhasi bormi?
│      ├── HA: Origin ishonchlimi? (is_origin_allowed(origin) YOKI same-origin)
│      │        ├── HA: O'tkazib yubor.
│      │        └── YO'Q: 403 Forbidden ("CSRF himoyasi: Ruxsat etilmagan Origin").
│      │
│      └── YO'Q: So'rovda auth cookie bormi? (access_token, user_access_token, refresh_token)
│               ├── YO'Q: Cookie yo'q (masalan, Bot X-Bot-Secret yoki API Bearer token).
│               │         └── O'tkazib yubor (router autentifikatsiyasiga).
│               └── HA: Referer sarlavhasi bormi?
│                        ├── HA: Referer ishonchli domendanmi?
│                        │        ├── HA: O'tkazib yubor.
│                        │        └── YO'Q: 403 Forbidden ("Ruxsat etilmagan Referer").
│                        └── YO'Q: 403 Forbidden ("Origin yoki Referer sarlavhasi talab qilinadi").
```

---

## 4. TEST DALILLARI VA TERMINAL NATIJALARI

TDD (Test-Driven Development) usulida `tests/audit2/test_csrf_origin_protection.py` yaratildi va sinovdan o'tkazildi:

### Test Natijalari (Raw Terminal Output):
```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Администратор\Desktop\kino bot project\kinochi project
configfile: pytest.ini
collected 7 items

tests/audit2/test_csrf_origin_protection.py::test_csrf_safe_methods_unrestricted PASSED [ 14%]
tests/audit2/test_csrf_origin_protection.py::test_csrf_untrusted_origin_rejected_on_post PASSED [ 28%]
tests/audit2/test_csrf_origin_protection.py::test_csrf_trusted_origin_allowed PASSED [ 42%]
tests/audit2/test_csrf_origin_protection.py::test_csrf_missing_origin_cookie_auth_handling PASSED [ 57%]
tests/audit2/test_csrf_origin_protection.py::test_csrf_server_to_server_bot_unrestricted PASSED [ 71%]
tests/audit2/test_csrf_origin_protection.py::test_csrf_admin_cookie_auth_protection PASSED [ 85%]
tests/audit2/test_csrf_origin_protection.py::test_csrf_refresh_and_logout_endpoints PASSED [100%]

============================= 7 passed in 14.30s ==============================
```

### To'liq Regressiya Tekshiruvi (`tests/audit2/` suite):
```text
============================= 30 passed in 22.72s =============================
```
Avvalgi barcha 23 ta audit va integratsiya testlari 0 xato bilan to'liq o'tdi. Hech qanday regressiya yuz bermadi.

---

## 5. REFRESH TOKEN XAVFSIZLIGI TAHLILI VA KELAJAK REJASI

> [!NOTE]
> Ushbu tahlil topshiriqning 4-bandiga asosan kiritildi va mavjud CSRF tuzatishiga aralashtirilmadi.

### 5.1. Mavjud Muammo (Stateless Replay Risk)
Hozirgi tizimda `refresh_token` ma'lumotlar bazasida saqlanmaydi (stateless JWT).
- **Xavf:** Agar tajovuzkor adminning refresh tokenini o'g'irlasa, admin brauzerdan logout qilganidan keyin ham 7 kun ichida `/api/v1/auth/refresh` orqali yangi access tokenlar olaveradi.
- Hozirgi rotation mexanizmi faqat yangi token chiqaradi, ammo eski tokenni bazada bekor qilmaydi (chunki baza yo'q).

### 5.2. Taklif Qilinadigan DB-Backed Rotation & Revocation Arxitekturasi
Eski tokenni qayta ishlatishni to'xtatish uchun:
1. **Yangi Jadval:** `admin_refresh_tokens`:
   - `id`: UUID (Primary Key)
   - `admin_id`: Integer (ForeignKey -> admin_users.id)
   - `jti`: String (JWT unikal identifikatori)
   - `is_revoked`: Boolean (Default: False)
   - `expires_at`: DateTime (7 kun)
   - `replaced_by`: String (nullable - yangi chiqarilgan token jti)
2. **Breach Detection (Qayta ishlatishni aniqlash):**
   - Agar biror refresh so'rovida `is_revoked == True` bo'lgan token kelib tushsa: darhol xakerlik urinishi deb baholanadi va ushbu adminga tegishli barcha aktiv tokenlar bekor qilinadi.
3. **Logout:**
   - Logout paytida foydalanuvchining aktiv tokeni bazada `is_revoked = True` qilinadi.

---

## 6. XULOSA VA YAKUNIY STATUS

- CSRF zaifligi to'liq bartaraf etildi.
- Mavjud Telegram Bot, Scraper va Frontend integratsiyalari to'liq saqlab qolindi.
- Barcha o'zgarishlar minimal (jami 97 qator) va 100% testlar bilan tasdiqlandi.

**Yakuniy qaror:** **PASS (To'liq Yopildi)**
