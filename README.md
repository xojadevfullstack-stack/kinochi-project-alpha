# Kinochi Project

A complete movie and series bot ecosystem built with FastAPI, Aiogram 3, and a modern frontend.

## 🏗 Umumiy Arxitektura (Architecture)

Loyihaning arxitekturasi Clean Architecture tamoyillariga asoslangan bo'lib, quyidagi qismlardan iborat:
- **Backend (FastAPI)**: Asosiy biznes logika, API va ma'lumotlar bazasi bilan ishlash (PostgreSQL + SQLAlchemy). Backend Domain-Driven Design (DDD) va Clean Architecture asosida qatlamlarga bo'lingan: `api`, `application`, `domain`, `infrastructure`.
- **Bot (Aiogram 3)**: Foydalanuvchilar bilan muloqot qiluvchi Telegram bot. Backend API'ga ulanadi, mustaqil DB'ga ega emas.
- **Admin Panel / Frontend (Next.js)**: Filmlarni boshqarish, kanal va obunalarni sozlash uchun interfeys. JWT orqali himoyalangan.

## 🚀 Deployment Qadamlari (Render uchun)

Loyihani serverga (Render PaaS kabi) bitta jarayonda (Bot + Backend) deploy qilish uchun quyidagi amallarni bajaring:

1. Render da yangi **Web Service** yarating va GitHub repozitoriyangizni ulang.
2. Quyidagi sozlamalarni kiriting:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python run.py`
3. Environment Variables (Muhit O'zgaruvchilari) ni Render dashboard'ida barchasini (ham Bot, ham Backend uchun) **bitta joyga** kiriting. Ular bitta process da ishlagani uchun umumiy `.env` dan o'qiydi.
4. "Deploy" tugmasini bosing!

> **Eslatma**: `run.py` orqali FastAPI (API) va Aiogram (Telegram bot) bitta resurs (512MB RAM) ichida parallel ishga tushadi. 

## ⚙️ .env O'zgaruvchilari (Umumiy)

Barcha kerakli muhit o'zgaruvchilar ro'yxati (Render dashboard ga qo'shiladi):

```env
# Loyiha
PROJECT_NAME="Kinochi"
VERSION="0.1.0"
APP_ENV="production"
DEBUG="False"

# Database & Redis (Masalan Neon va Upstash URL lari)
DATABASE_URL="postgresql+asyncpg://user:pass@neon.tech/kinochi_db"
REDIS_URL="redis://your-upstash-redis-url"

# Xavfsizlik
SECRET_KEY="generate-a-strong-32-byte-secret"
ACCESS_TOKEN_EXPIRE_MINUTES="30"
REFRESH_TOKEN_EXPIRE_DAYS="7"
BOT_API_SECRET="shared-secret-between-bot-and-backend"
JWT_SECRET_KEY="front-end-admin-panel-secret"

# Telegram
BOT_TOKEN="your-telegram-bot-token"
STORAGE_CHANNEL_ID="-1001234567890"

# URL'lar (CORS va Bot API uchun)
CORS_ORIGINS='["https://your-website.com"]'
BACKEND_API_URL="http://127.0.0.1:8000/api/v1" # Ichki tarmoqda ishlagani uchun localhost yetarli!
WEBSITE_URL="https://your-website.com"
```
