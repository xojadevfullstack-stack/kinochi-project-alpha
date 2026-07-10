# Kinochi Loyihasi Holati (Project State - Diagnostika Natijasi)

Ushbu hujjat loyihaning haqiqiy kod holati (audit natijasi) asosida tuzildi.

## Arhitektura va Texnologiyalar
- **Backend:** FastAPI, PostgreSQL, SQLAlchemy 2.0, Alembic, Pydantic, HTTPX. Clean Architecture tamoyillari (Domain, Application, Infrastructure, API).
- **Telegram Bot:** Aiogram 3.x. Mustaqil servis sifatida ishlaydi.
- **Admin Panel:** Next.js (App Router) + TypeScript + Tailwind CSS.
- **Website:** Foydalanuvchi tomonidan Next.js (App Router) bilan yozilmoqda. **AGENTLAR TOMONIDAN WEBSITE PAPKASIGA TEGILMASIN.**

---

## 1. Backend Holati (MAVJUD VA TEKSHIRILGAN)

Backend to'liq ishlashga tayyor va barcha qatlamlari to'g'ri bog'langan.

**Modullar zanjiri (Domain -> Model -> Service -> API):**
- `movies`: To'liq zanjir mavjud va ishlaydi.
- `categories`: To'liq zanjir mavjud va ishlaydi.
- `channels`: To'liq zanjir mavjud va ishlaydi.
- `broadcasts`: To'liq zanjir mavjud va ishlaydi (Rate limiting `sender.py` orqali ta'minlangan).
  *Eslatma: Broadcast: TO'LIQ TEKSHIRILDI va ISHLAYDI — amaliy 'send' sinovi foydalanuvchi tomonidan tasdiqlandi (2026-07-09), xabar botdan real foydalanuvchiga muvaffaqiyatli yetib bordi.*
- `users`: To'liq zanjir mavjud.
- `admin_users` va `auth`: Domain/Model/API darajasida JWT asosida ishlaydi. Auth xavfsizligi `Depends(get_current_admin)` orqali himoyalangan.

**Alembic Migratsiyalar Zanjiri:**
Barcha migratsiya fayllari zanjiri to'g'ri (uzilmagan) va izchil:
1. `001_initial_movies_categories.py`
2. `9994a3613b61_add_user_and_mandatorychannel_models.py` (down_revision: 001)
3. `6b34f1d25588_add_is_active_to_categories.py` (down_revision: 9994a3613b61)
4. `e42a9b3c4f9a_make_channel_id_nullable.py` (down_revision: 6b34f1d25588)
5. `f7c8d2e1a5b3_create_admin_users_table.py` (down_revision: e42a9b3c4f9a)
6. `b3528338b53f_add_broadcasts_table.py` (down_revision: f7c8d2e1a5b3)

**`.env.example` o'zgaruvchilari:**
`PROJECT_NAME`, `VERSION`, `APP_ENV`, `DEBUG`, `DATABASE_URL`, `REDIS_URL`, `CORS_ORIGINS`, `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `BOT_TOKEN`, `STORAGE_CHANNEL_ID`.

---

## 2. Bot Holati (MAVJUD VA TEKSHIRILGAN)

Bot `aiogram` da ishlangan va `.venv` ichida yurgizilishi shart.
- **handlers/:** `start.py` (ro'yxatdan o'tish), `search.py` (sarlavha bo'yicha qidirish), `check_sub.py` (obunani tekshirish).
- **middlewares/:** `subscription_check.py` (Foydalanuvchi majburiy kanallarga a'zo bo'lmaguncha botni bloklaydi).
- **services/:** `api_client.py` (Backend bilan muloqot qiladi).
- **keyboards/:** `inline.py` (Obuna bo'lish, qidiruv natijalari uchun tugmalar).
- **utils/:** `movie_sender.py` (Videolarni yuborish mantiqi).
- **`main.py` routerlar:** `start_router`, `check_sub_router`, `search_router` ulangan.

---

## 3. Admin Panel Holati (MAVJUD VA TEKSHIRILGAN)

Panel API'ga `fetchApi` (credentials: 'include') bilan ulangan va to'liq ishlashga tayyor.
- Mavjud sahifalar: `/login`, `/movies`, `/categories`, `/channels`, `/broadcasts`.
- **Eslatma:** `broadcasts` UI sahifasi oxirgi ishlarda qo'shildi va u ham API bilan to'liq ulangan (shu jumladan "Test yuborish" formasi bilan).

---

## 4. Website Holati (KUZATISH REJIMI)

**DIQQAT: FOYDALANUVCHI TOMONIDAN MUSTAQIL OLIB BORILMOQDA. AGENT TEGMAYDI!**
- Papka: `website/` (Next.js App Router, Tailwind CSS, TypeScript).
- Hozirgi holati: `package.json`, `next.config.mjs`, `tailwind.config.ts`, `app/page.tsx` mavjud. Foydalanuvchi "Phase 3: Public Website" vizual qismini mustaqil yozmoqda.

---

## 5. Agent Qoidalari (.agents/rules/)

Agentlarga ishlash davomida quyidagi qoidalar rahbarlik qiladi:
- `security-env.md` (`always_on`): `.env` faylini o'qimaslik.
- `verification-protocol.md` (`always_on`): O'zgarishlarni tekshirish protokoli.
- `bot-thin-client.md` (`glob: bot/**`): Bot faqat API orqali ishlashi, to'g'ridan-to'g'ri DB'ga ulanmasligi.
- `clean-architecture-boundaries.md` (Always-On): Qatlamlararo qat'iy qaramlik qoidalari.
- `database-migrations.md` (`glob: backend/alembic/**`): Migratsiyalar ustida qoidalar.

*Eslatma: Avvalgi `PROJECT_STATE.md` dagi "Phase 3 qoldi", "Broadcast UI yozilmagan" degan ma'lumotlar HAQIQIY kodda allaqachon bajarilgan yoki jarayonga o'zgartirilganligi sababli, bu versiyada haqiqatga to'g'rilandi.*

---

## Muhim texnik eslatmalar (kelajakda takrorlanmasligi uchun):

1. **Botni ishga tushirish:** Bot `bot/.venv` orqali ishga tushirilishi SHART (`.\.venv\Scripts\Activate.ps1` → `python main.py`), aks holda `ModuleNotFoundError` beradi va bot butunlay ishlamay qoladi.
2. **Alembic:** Alembic buyruqlari `python -m alembic` shaklida ishlatilishi kerak — aks holda `ModuleNotFoundError: app` xatosi chiqadi.
3. **Pydantic Entities:** Barcha entity'larda `model_config = ConfigDict(from_attributes=True)` bo'lishi SHART, aks holda API 500 xato beradi.
4. Backend Docker orqali ishlaydi; kod o'zgargandan keyin `docker-compose up -d --build backend` MAJBURIY, aks holda eski kod ishlab qoladi.
5. `alembic/env.py` da `from app.infrastructure.db import models` qatori bo'lishi SHART, aks holda autogenerate yangi model qo'shilganda eski jadvallarni DROP qiladi.
6. `get_db_session()` har bir tranzaksiyadan so'ng o'ziga qilingan o'zgarishlarni `commit()` qilishi kerak.
7. Tashqi API bilan ishlashda xatoni jimgina yutish (bare except) mumkin emas, log yozish majburiy.
8. 5432-port boshqa loyiha konteyneri bilan to'qnashishi mumkin, `docker ps -a` bilan tekshirish kerak.
9. `.env` fayllari qo'lda `.env.example` dan nusxalanishi va to'ldirilishi kerak.
10. `models/__init__.py` ga yangi model qo'shilganda import qo'shish SHART (Alembic discovery uchun).
11. Admin panel `fetchApi` wrapper'da `credentials: 'include'` bor — bu cookie yuborilishi uchun zarur, umuman olib tashlanmasin.
