# Kinochi Project

A complete movie and series bot ecosystem built with FastAPI, Aiogram 3, and a modern frontend.

## 🏗 Umumiy Arxitektura (Architecture)

Loyihaning arxitekturasi Clean Architecture tamoyillariga asoslangan bo'lib, quyidagi qismlardan iborat:
- **Backend (FastAPI)**: Asosiy biznes logika, API va ma'lumotlar bazasi bilan ishlash (PostgreSQL + SQLAlchemy). Backend Domain-Driven Design (DDD) va Clean Architecture asosida qatlamlarga bo'lingan: `api`, `application`, `domain`, `infrastructure`.
- **Bot (Aiogram 3)**: Foydalanuvchilar bilan muloqot qiluvchi Telegram bot. Backend API'ga ulanadi, mustaqil DB'ga ega emas.
- **Admin Panel / Frontend (Next.js)**: Filmlarni boshqarish, kanal va obunalarni sozlash uchun interfeys. JWT orqali himoyalangan.

## 🚀 Deployment Qadamlari

Loyihani serverga joylashtirish (deploy qilish) uchun quyidagi amallarni bajaring:

1. Serverda kerakli dasturlarni o'rnating: `Docker`, `Docker Compose`, `Git`.
2. Repozitoriyni klon qiling:
   ```bash
   git clone <repo-url>
   cd kinochi-project
   ```
3. `.env` fayllarni yarating (namunalar pastda ko'rsatilgan).
4. Docker Compose orqali barcha servislarni ishga tushiring:
   ```bash
   docker-compose up -d --build
   ```
5. Bazaga migratsiyalarni qo'llang (agar avtomatik bo'lmasa):
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

## ⚙️ .env O'zgaruvchilari

Loyihani ishga tushirish uchun ikkita `.env` fayli kerak (backend va bot uchun).

### `backend/.env`
```env
# Loyiha
PROJECT_NAME="Kinochi"
VERSION="0.1.0"
APP_ENV="production"
DEBUG="False"

# Database & Redis
DATABASE_URL="postgresql+asyncpg://user:pass@db:5432/kinochi_db"
REDIS_URL="redis://redis:6379/0"

# Xavfsizlik
SECRET_KEY="generate-a-strong-32-byte-secret"
ACCESS_TOKEN_EXPIRE_MINUTES="30"
REFRESH_TOKEN_EXPIRE_DAYS="7"
BOT_API_SECRET="shared-secret-between-bot-and-backend"

# Telegram
BOT_TOKEN="your-telegram-bot-token"
STORAGE_CHANNEL_ID="-1001234567890"

# CORS
CORS_ORIGINS='["https://your-website.com"]'
```

### `bot/.env`
```env
BOT_TOKEN="your-telegram-bot-token"
BACKEND_API_URL="http://backend:8000/api/v1"
STORAGE_CHANNEL_ID="-1001234567890"
BOT_API_SECRET="shared-secret-between-bot-and-backend"
WEBSITE_URL="https://your-website.com"
```
