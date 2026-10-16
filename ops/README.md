# Kinochi Tizimini Productionga O'tkazish (Go-Live) va Pilot Qo'llanmasi

Ushbu qo'llanma Kinochi loyihasining operatorlari uchun mo'ljallangan bo'lib, bazani tozalash, xavfsiz Go-Live amallarini bajarish va filmlar bo'yicha pilot yuklashni yo'lga qo'yish bo'yicha qadamma-qadam yo'riqnomani o'z ichiga oladi.

Barcha buyruqlar va xabarlar Windows cp1251/cp866 konsollarida nosozlik keltirib chiqarmasligi uchun faqat ASCII formatida tayyorlangan.

---

## 1. Operator Tomonidan Bajariladigan Aniq Ketma-ketlik

### 0-bosqich: Tayyorgarlik va Talablar
1. Tizimda PostgreSQL CLI (xususan `pg_dump`) o'rnatilganligini tekshiring:
   ```powershell
   pg_dump --version
   ```
   Agar topilmasa, quyidagi buyruq orqali o'rnating:
   ```powershell
   winget install PostgreSQL.PostgreSQL
   ```
2. Hech qanday scraper jarayoni ishlamayotganiga ishonch hosil qiling (`scraper/.scraper_cli.lock` mavjud bo'lmasligi kerak).

### 1-bosqich: Havfsiz Tekshiruv (-DryRun)
Hech qanday ma'lumotni o'zgartirmasdan, tizim tayyorgarligini simulyatsiya qiling:
```powershell
.\ops\go_live.ps1 -DryRun -UrlEnvVar DATABASE_URL
```
Ushbu bosqich disk hajmini, locklarni va parametrlar to'g'riligini tekshiradi, lekin bazaga o'zgartirish kiritmaydi.

### 2-bosqich: Yangi Telegram Userbot Sessiyasini Yaratish
Eski sessiyani bekor qilish va yangisini xavfsiz generatsiya qilish uchun:
```powershell
python ops/new_telegram_session.py --env-file .env.local
```
Skript konsolga sessiya kalitini chiqarmaydi, to'g'ridan-to'g'ri `.env.local` ga yozadi.

### 3-bosqich: Production Go-Live va Media Reset
Haqiqiy Go-Live jarayonini ishga tushiring:
```powershell
.\ops\go_live.ps1 -UrlEnvVar DATABASE_URL
```

> [!WARNING]
> `scripts/reset_media.py` skriptini hech qachon qo'lda, eski bayroqlar bilan to'g'ridan-to'g'ri ishga tushirmang!
> Yangi tozalash mexanizmi `--wipe-media` bayrog'ini talab etadi va faqat `ops/go_live.ps1` orqali to'liq zaxira olingandan so'ng xavfsiz tartibda chaqirilishi shart. Qo'lda bajarilgan reset zaxira kafolatini yo'qotishi mumkin.

Jarayon fazalari:
- **Preflight**: Disk va DB ulanishini tekshiradi (xost yoki Docker orqali pg_dump mavjudligini tasdiqlaydi).
- **Backup**: `backups/kinochi_pre_reset_<timestamp>.dump` fayliga to'liq zaxira oladi, `pg_restore --list` orqali arxiv katalogi yaxlitligini tekshiradi va SHA256 qayd etadi.
- **Migrate**: `alembic upgrade head` ni ishga tushirib, `e8f9a0b1c2d3` versiyasiga ko'taradi va yangi yozuvlar uchun `publish_status='pending'` qiladi. Agar model va baza orasida tafovut aniqlansa, jarayon to'xtatiladi (zarur bo'lsa `-IgnoreAlembicCheck` orqali o'tish mumkin).
- **Deploy Gate**: Backendda SEED_GATE_MODE faolligini bildiradi va operator tasdig'ini (`DEPLOYED`) oladi.
- **Reset**: Foydalanuvchilar va kanallarni saqlab, `scripts/reset_media.py --wipe-media` orqali barcha media jadvallarini (`movies`, `series`, `episodes`, `reports`, `reviews`, `watch_history`, `rejected_items`) 0 ga tushiradi hamda Redis `cache:*` kalitlarini tozalaydi.
- **Final**: Natijaviy hisobot jadvalini chiqaradi.

### 4-bosqich: TMDb Seed Ingestor Pilot Ishga Tushirish
Faqat filmlar uchun 20 talik pilot yig'ish va navbatga qo'yish:
```powershell
.\ops\pilot.ps1 -Limit 20
```
- Skript nomzodlarni qidiradi va ko'rsatadi.
- Admin panelda (`/admin/scraper`) yoki Neon SQL orqali nomzodlarni ko'rib chiqing.
- Konsolda tasdiqlash uchun `YES` deb yozing.

### 5-bosqich: Yuklashni Boshlash (Worker / Grabber)
Navbatga kiritilgan 20 ta filmni yuklash uchun grabberni ishga tushiring:
```powershell
.\start_grabber.bat
```
Yuklanish jarayonini kuzatish:
```powershell
python -m scraper.tmdb_top_ingestor --stats
```

---

## 2. Neon Ma'lumotlar Bazasi Parolini Almashtirish (Rotation)

### Qachon almashtiriladi?
- Go-Live va tozalash muvaffaqiyatli yakunlangach.
- Eski ishlab chiqish bosqichidagi ochiq qolgan parollarni bekor qilish uchun.
- Rejali xavfsizlik yangilanishlarida.

### Qanday almashtiriladi?
1. [Neon Console](https://console.neon.tech) ga kiring.
2. Loyihangizni tanlang -> **Roles / Databases** bo'limiga o'ting.
3. Asosiy rol (masalan, `neondb_owner` yoki `kinochi`) yonidagi **Reset Password** tugmasini bosing.
4. Yangi hosil bo'lgan ulanish satrini nusxalang.
5. Quyidagi xizmatlarda yangilang:
   - **Render**: Dashboard -> Backend xizmati -> Environment -> `DATABASE_URL` ni yangilang va Save bosing (xizmat avtomatik qayta ishga tushadi).
   - **Mahalliy**: `.env` yoki `.env.local` faylidagi `DATABASE_URL` qiymatini yangilang (hech qachon gitga commit qilmang!).

---

## 3. Telegram Ilovasida Eski Sessiyani Bekor Qilish (Revocation)

Userbot hisobi xavfsizligini ta'minlash uchun:
1. Telefoningizda yoki kompyuteringizda Telegram ilovasini oching.
2. **Sozlamalar (Settings)** -> **Qurilmalar (Devices)** bo'limiga kiring.
3. Ro'yxatdagi faol sessiyalarni ko'rib chiqing.
4. Eski bot/userbot sessiyasini tanlang va **Sessiyani yakunlash (Terminate session)** tugmasini bosing.
5. Yangi `ops/new_telegram_session.py` orqali yaratilgan sessiya yagona faol userbot sessiyasi bo'lib qoladi.

---

## 4. Render va Vercel Boshqaruv Panellarida Tekshiriladigan Sozlamalar

### Render (Backend API):
1. **DATABASE_URL**: Yangi Neon paroli bilan ko'rsatilgan bo'lishi kerak.
2. **REDIS_URL**: Upstash yoki mahalliy Redis ulanish satri.
3. **SEED_GATE_MODE**: `quarantine` holatida bo'lishi kerak (yangi kontent darhol omma oldida ko'rinib ketmasligi uchun).
4. **TELEGRAM_STRING_SESSION**: Yangi olingan sessiya satri.
5. **Logs**: Uvicorn server `Application startup complete` xabari bilan ishlashini va `GET /docs` yoki `/api/v1/health` 200 qaytarayotganini tekshiring.

### Vercel (Admin Panel va Web-sayt):
1. **NEXT_PUBLIC_API_URL**: Renderdagi backend API domeniga to'g'ri ulangan bo'lishi kerak.
2. **Deployments**: Oxirgi commit muvaffaqiyatli build bo'lganini (Ready holati) tasdiqlang.
3. **Admin Panel**: `/admin/scraper` va `/admin/movies` sahifalari xatosiz ochilishini tekshiring.

---

## 5. Nosozliklar va Ularning Yechimlari (Troubleshooting Table)

| # | Muammo (Scenario) | Bir qatorlik yechim (Resolution) |
|---|-------------------|-----------------------------------|
| 1 | `pg_dump PATH da topilmadi` | `winget install PostgreSQL.PostgreSQL` buyrug'i orqali CLI vositalarini o'rnating. |
| 2 | `Scraper lock fayli mavjud: .scraper_cli.lock` | Agar scraper ishlamayotgan bo'lsa, `scraper/.scraper_cli.lock` faylini o'chirib tashlang. |
| 3 | `Diskda yetarli joy yo'q (< 2.0 GB)` | Asosiy diskdan kamida 2 GB bo'sh joy oching yoki vaqtinchalik fayllarni tozalang. |
| 4 | `Belgilangan 'DATABASE_URL' muhit o'zgaruvchisi topilmadi` | `$env:DATABASE_URL="postgresql://..."` orqali terminalda muhit o'zgaruvchisini o'rnating. |
| 5 | `Alembic birdan ortiq head aniqladi` | `alembic merge` orqali tarmoqlarni birlashtiring yoki keraksiz migratsiya faylini o'chiring. |
| 6 | `SEED_INCLUDE_SERIES='true' deb sozlangan` | `$env:SEED_INCLUDE_SERIES="false"` qilib pilotni qayta ishga tushiring (pilot faqat filmlar uchun). |
| 7 | `Redis ulanishida ConnectionRefused yoki Timeout` | `REDIS_URL` to'g'riligini va Redis/Upstash serveri ochiqligini tekshiring. |
| 8 | `Zaxira fayli hajmi 1 MB dan kichik` | Neon bazasida jadvallar to'liq ekanligini tekshiring va tarmoq ulanishini yangilab qayta urinib ko'ring. |
| 9 | `Telegram FloodWaitError yuz berdi` | Telegram bergan kutish vaqtini kuting va pilot hajmini 20 tadan oshirmang. |
| 10| `reset_media.py: --i-am-wiping-production talab qilinadi` | Skriptni to'g'ridan-to'g'ri emas, barcha himoya bayroqlarini uzatuvchi `ops/go_live.ps1` orqali bajaring. |
