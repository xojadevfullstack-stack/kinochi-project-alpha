@echo off
cd /d "%~dp0"
chcp 65001 > nul
title Kinochi - Admin Panel Avtopilot & Grabber Launcher

echo ======================================================================
echo          KINOCHI - ADMIN PANEL AVTOPILOT & GRABBER LAUNCHER
echo ======================================================================
echo.

:: 1. Talab qilinadigan fayllar tekshiruvi
if not exist "backend\.venv\Scripts\python.exe" (
    echo [XATO] backend\.venv muhiti topilmadi!
    echo Iltimos, avval backend virtual muhitini o'rnating.
    pause
    exit /b 1
)

if not exist "backend\.env" (
    echo [XATO] backend\.env sozlamalar fayli topilmadi!
    pause
    exit /b 1
)

if not exist "admin-panel\node_modules" (
    echo [OGOHLANTIRISH] admin-panel\node_modules topilmadi. Kutubxonalar o'rnatilmoqda...
    cd admin-panel && call npm install && cd ..
)

echo [1/4] Eskidan qolgan jarayonlar va port konfliktlari tozalanmoqda...

:: 2. Port 8000 va 3001 dagi eski jarayonlarni tozalash
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ports = @(8000, 3001); " ^
    "foreach ($port in $ports) { " ^
    "    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue; " ^
    "    if ($conns) { " ^
    "        $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique; " ^
    "        foreach ($p in $pids) { " ^
    "            if ($p -gt 0) { " ^
    "                Stop-Process -Id $p -Force -ErrorAction SilentlyContinue; " ^
    "                Write-Host \"[OK] Port $port dagi eski jarayon (PID $p) to'xtatildi.\"; " ^
    "            } " ^
    "        } " ^
    "    } " ^
    "}"

:: 3. Telegram sessionni qulflab qo'ygan eski run_scraper jarayonlarini tozalash
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | " ^
    "Where-Object { $_.CommandLine -like '*run_scraper.py*' } | " ^
    "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; Write-Host \"[OK] Eski scraper jarayoni (PID $($_.ProcessId)) to'xtatildi.\" }"

:: 4. Qoldiq lock fayllarni tozalash
if exist "scraper\.scraper_cli.pid" del /f /q "scraper\.scraper_cli.pid" >nul 2>&1
if exist "scraper\.scraper_pid" del /f /q "scraper\.scraper_pid" >nul 2>&1

echo.
echo [2/4] Backend API (FastAPI - Port 8000) ishga tushirilmoqda...
start "Kinochi - Backend API (Port 8000)" cmd /k "cd /d "%~dp0backend" && call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

:: Backend yuklanishini 3 soniya kutish
timeout /t 3 /nobreak > nul

echo [3/4] Admin Panel (Next.js - Port 3001) ishga tushirilmoqda...
start "Kinochi - Admin Panel (Port 3001)" cmd /k "cd /d "%~dp0admin-panel" && npm run dev -- -p 3001"

:: Admin Panel yuklanishini 4 soniya kutish
timeout /t 4 /nobreak > nul

echo [4/4] Brauzerda Avtopilot boshqaruv sahifasi ochilmoqda...
start http://localhost:3001/scraper

echo.
echo ======================================================================
echo  BARCHA XIZMATLAR KONFLIKTSIZ ISHGA TUSHIRILDI!
echo ======================================================================
echo  1. Backend API:   http://127.0.0.1:8000/docs
echo  2. Admin Panel:   http://localhost:3001/scraper
echo.
echo  Endi Admin Panel brauzer oynasida:
echo  - "Avtopilotni boshlash" (aniqlash + avto yuklash)
echo  - "Katalog yig'ish (Parse)" (sayt va botlardan yangi kontent yig'ish)
echo  - "Navbatni yuklash" (qismlar va kinolarni Telegramdan tortib olish)
echo  amallarini bir tugma orqali to'liq boshqarishingiz mumkin.
echo.
echo  [ESLATMA] Jarayonlarni to'xtatish uchun ushbu oynani yopishingiz
echo  yoki STOP_ALL_SERVICES.bat faylini ishga tushirishingiz mumkin.
echo ======================================================================
echo.
pause
