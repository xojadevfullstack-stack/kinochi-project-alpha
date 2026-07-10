@echo off
echo Kinochi Loyihasini ishga tushirish...
echo.

echo 1. Docker (PostgreSQL, Redis) yoqilmoqda...
docker-compose up -d

echo 2. Backend (FastAPI) yangi oynada ochilmoqda...
start "Backend API (8000)" cmd /k "cd backend && .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload"

echo 3. Telegram Bot yangi oynada ochilmoqda...
start "Telegram Bot" cmd /k "cd bot && .\.venv\Scripts\python.exe main.py"

echo 4. Veb-sayt yangi oynada ochilmoqda...
start "Website (3000)" cmd /k "cd website && npm run dev"

echo 5. Admin Panel yangi oynada ochilmoqda...
start "Admin Panel (3001)" cmd /k "cd admin panel && npm run dev -- -p 3001"

echo.
echo Barcha xizmatlar muvaffaqiyatli ishga tushirildi! Oynalar avtomatik ochiladi.
echo Dasturlarni to'xtatish uchun o'sha ochilgan (qora) oynalarni yopishingiz kifoya.
pause
