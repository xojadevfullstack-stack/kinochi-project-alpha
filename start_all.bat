@echo off
echo ==============================================
echo KINOCHI PROJECT LOCAL STARTUP SCRIPT
echo ==============================================
echo.

echo Starting Backend (FastAPI) on port 8000...
start "Kinochi Backend" cmd /k "cd backend && call .venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

echo Starting Bot (Aiogram)...
start "Kinochi Bot" cmd /k "cd bot && call .venv\Scripts\activate && python main.py"

echo Starting Admin Panel (Next.js) on port 3001...
start "Kinochi Admin Panel" cmd /k "cd admin-panel && npm run dev -- -p 3001"

echo Starting Website (Next.js) on port 3000...
start "Kinochi Website" cmd /k "cd website && npm run dev -- -p 3000"

echo.
echo Barcha xizmatlar alohida oynalarda ishga tushirildi!
echo Backend: http://localhost:8000
echo Admin Panel: http://localhost:3001
echo Website: http://localhost:3000
echo.
pause
