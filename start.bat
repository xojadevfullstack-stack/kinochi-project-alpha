@echo off
cd /d "%~dp0"
chcp 65001 > nul
title Kinochi - Parser, Grabber va Tizim Boshqaruvi

if not exist "backend\.venv\Scripts\python.exe" (
    echo [XATO] backend\.venv topilmadi!
    pause
    exit /b
)

if not "%1"=="" (
    set choice=%1
    goto process_choice
)

:menu
cls
echo ======================================================================
echo           KINOCHI - PARSER VA GRABBER BOSHQARUV PANELI
echo ======================================================================
echo.
echo   [ VEB SAYT / ADMIN PANEL ORQALI ISHLATISH ]
echo   1) Saytdan boshqarish (Backend + Admin Panelni yoqish va brauzerda ochish)
echo.
echo   [ TERMINALDA PARSER (Saytlardan katalog yig'ish) ]
echo   2) Uzmovi saytidan katalog yig'ish (Parse)
echo   3) Asilmedia saytidan katalog yig'ish (Parse)
echo   4) AniToob anime katalogini yig'ish (@ANITOOBUZ_BOT / bot.anitoobtv.uz)
echo   5) Animeelar bot/katalogidan anime yig'ish (Parse)
echo.
echo   [ TERMINALDA GRABBER (Telegram botdan kinolarni yuklash) ]
echo   6) Uzmovi botidan yuklash (@UzmovieTV_Bot)
echo   7) Asilmedia botidan yuklash (@asilmediabot)
echo   8) AniToob botidan anime yuklash (@ANITOOBUZ_BOT)
echo   9) Animeelar botidan anime yuklash (@Animeelar_Bot)
echo   10) Muayyan film kodi yoki anime bo'yicha yuklash (masalan: 15 yoki 1-5 yoki 4)
echo.
echo   [ NAVBAT VA DUBLIKATLARNI BOSHQARISH ]
echo   11) Navbatdagi dublikatlarni tozalash (--clean-duplicates)
echo   12) Navbat statistikasini ko'rish (--stats)
echo.
echo   [ TO'LIQ TIZIM ]
echo   13) Barcha xizmatlarni yoqish (Backend + Bot + Admin Panel + Website)
echo.
echo   0) Chiqish
echo ======================================================================
echo.

set choice=
set /p choice="Tanlovingizni kiriting (0-13): "

if "%choice%"=="" exit /b

:process_choice
if "%choice%"=="1" goto opt_web
if "%choice%"=="web" goto opt_web
if "%choice%"=="2" goto opt_parse_uzmovi
if "%choice%"=="3" goto opt_parse_asilmedia
if "%choice%"=="4" goto opt_parse_anitoob
if "%choice%"=="5" goto opt_parse_animeelar
if "%choice%"=="6" goto opt_grab_uzmovi
if "%choice%"=="7" goto opt_grab_asilmedia
if "%choice%"=="8" goto opt_grab_anitoob
if "%choice%"=="9" goto opt_grab_animeelar
if "%choice%"=="10" goto opt_grab_codes
if "%choice%"=="11" goto opt_clean
if "%choice%"=="12" goto opt_stats
if "%choice%"=="stats" goto opt_stats
if "%choice%"=="13" goto opt_all
if "%choice%"=="0" exit /b

echo.
echo [!] Noto'g'ri tanlov kiritildi: %choice%
if not "%1"=="" exit /b
ping 127.0.0.1 -n 2 > nul
goto menu

:opt_web
cls
echo ======================================================================
echo   VEB SAYT / ADMIN PANEL ISHGA TUSHIRILMOQDA...
echo ======================================================================
echo.
echo 1. Backend (FastAPI - Port 8000) alohida oynada ishga tushirilmoqda...
start "Kinochi Backend (Port 8000)" cmd /k "cd backend && call .venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

echo 2. Admin Panel (Next.js - Port 3001) alohida oynada ishga tushirilmoqda...
start "Kinochi Admin Panel (Port 3001)" cmd /k "cd admin-panel && npm run dev -- -p 3001"

echo.
echo Xizmatlar yuklanmoqda, 3 soniyadan so'ng brauzer ochiladi...
ping 127.0.0.1 -n 4 > nul
start http://localhost:3001/scraper

echo.
echo [OK] Sayt ochildi: http://localhost:3001/scraper
echo Ushbu sahifada Parser va Grabberni qulay vizual tugmalar orqali boshqarishingiz mumkin!
echo.
if not "%1"=="" exit /b
pause
goto menu

:opt_parse_uzmovi
cls
echo ======================================================================
echo   UZMOVI SAYTIDAN PARSE QILISH
echo ======================================================================
echo.
set pages=3
if "%1"=="" (
    set /p pages="Nechta sahifa yig'ilsin? [Standart: 3]: "
)
echo.
echo Boshlanmoqda...
backend\.venv\Scripts\python.exe scraper/run_scraper.py --parse --source uzmovi --pages %pages%
echo.
if not "%1"=="" exit /b
pause
goto menu

:opt_parse_asilmedia
cls
echo ======================================================================
echo   ASILMEDIA SAYTIDAN PARSE QILISH
echo ======================================================================
echo.
set pages=3
if "%1"=="" (
    set /p pages="Nechta sahifa yig'ilsin? [Standart: 3]: "
)
echo.
echo Boshlanmoqda...
backend\.venv\Scripts\python.exe scraper/run_scraper.py --parse --source asilmedia --pages %pages%
echo.
if not "%1"=="" exit /b
pause
goto menu

:opt_parse_anitoob
cls
echo ======================================================================
echo   ANITOOB ANIME PARSE QILISH (@ANITOOBUZ_BOT / bot.anitoobtv.uz)
echo ======================================================================
echo.
set pages=3
if "%1"=="" (
    set /p pages="Nechta sahifa yig'ilsin? (Har sahifa 20 ta anime) [Standart: 3]: "
)
echo.
echo Boshlanmoqda...
backend\.venv\Scripts\python.exe scraper/run_scraper.py --parse --source anitoob --pages %pages%
echo.
if not "%1"=="" exit /b
pause
goto menu

:opt_parse_animeelar
cls
echo ======================================================================
echo   ANIMEELAR BOTIDAN ANIME PARSE QILISH
echo ======================================================================
echo.
set pages=3
if "%1"=="" (
    set /p pages="Nechta sahifa yig'ilsin? [Standart: 3]: "
)
echo.
echo Boshlanmoqda...
backend\.venv\Scripts\python.exe scraper/run_scraper.py --parse --source animeelar --pages %pages%
echo.
if not "%1"=="" exit /b
pause
goto menu

:opt_grab_uzmovi
cls
echo ======================================================================
echo   UZMOVI BOTIDAN YUKLASH (@UzmovieTV_Bot)
echo ======================================================================
echo.
set count=5
if "%1"=="" (
    set /p count="Nechta kino yuklansin? [Standart: 5]: "
)
echo.
echo Boshlanmoqda...
backend\.venv\Scripts\python.exe scraper/run_scraper.py --download --target uzmovi --limit %count%
echo.
if not "%1"=="" exit /b
pause
goto menu

:opt_grab_asilmedia
cls
echo ======================================================================
echo   ASILMEDIA BOTIDAN YUKLASH (@asilmediabot)
echo ======================================================================
echo.
set count=5
if "%1"=="" (
    set /p count="Nechta kino yuklansin? [Standart: 5]: "
)
echo.
echo Boshlanmoqda...
backend\.venv\Scripts\python.exe scraper/run_scraper.py --download --target asilmedia --limit %count%
echo.
if not "%1"=="" exit /b
pause
goto menu

:opt_grab_anitoob
cls
echo ======================================================================
echo   ANITOOB BOTIDAN ANIME YUKLASH (@ANITOOBUZ_BOT)
echo ======================================================================
echo.
set count=5
if "%1"=="" (
    set /p count="Nechta anime yuklansin? [Standart: 5]: "
)
echo.
echo Boshlanmoqda...
backend\.venv\Scripts\python.exe scraper/run_scraper.py --download --target anitoob --limit %count%
echo.
if not "%1"=="" exit /b
pause
goto menu

:opt_grab_animeelar
cls
echo ======================================================================
echo   ANIMEELAR BOTIDAN YUKLASH (@Animeelar_Bot)
echo ======================================================================
echo.
set count=5
if "%1"=="" (
    set /p count="Nechta anime yuklansin? [Standart: 5]: "
)
echo.
echo Boshlanmoqda...
backend\.venv\Scripts\python.exe scraper/run_scraper.py --download --target animeelar --limit %count%
echo.
if not "%1"=="" exit /b
pause
goto menu

:opt_grab_codes
cls
echo ======================================================================
echo   KOD BO'YICHA YUKLASH
echo ======================================================================
echo.
echo Qaysi bot orqali yuklamoqchisiz?
echo 1) Uzmovi bot (@UzmovieTV_Bot)
echo 2) Asilmedia bot (@asilmediabot)
echo 3) AniToob anime bot (@ANITOOBUZ_BOT)
echo 4) Animeelar bot (@Animeelar_Bot)
set /p bot_choice="Tanlovingiz (1-4) [Standart: 3]: "

set target=uzmovi
if "%bot_choice%"=="2" set target=asilmedia
if "%bot_choice%"=="3" set target=anitoob
if "%bot_choice%"=="4" set target=animeelar

echo.
set codes=
set /p codes="Film/Anime kodlari (masalan: 4 yoki 1-5 yoki 43): "
if "%codes%"=="" (
    echo [!] Kod kiritilmadi!
    if not "%1"=="" exit /b
    pause
    goto menu
)

echo.
echo Boshlanmoqda (Bot: %target%, Kodlar: %codes%)...
backend\.venv\Scripts\python.exe scraper/run_scraper.py --download --target %target% --codes %codes%
echo.
if not "%1"=="" exit /b
pause
goto menu

:opt_clean
cls
echo ======================================================================
echo   NAVBATDAGI DUBLIKATLARNI TOZALASH
echo ======================================================================
echo.
backend\.venv\Scripts\python.exe scraper/run_scraper.py --clean-duplicates
echo.
if not "%1"=="" exit /b
pause
goto menu

:opt_stats
cls
echo ======================================================================
echo   NAVBAT STATISTIKASI
echo ======================================================================
echo.
backend\.venv\Scripts\python.exe scraper/run_scraper.py --stats
echo.
if not "%1"=="" exit /b
pause
goto menu

:opt_all
cls
echo ======================================================================
echo   BARCHA XIZMATLARNI ISHGA TUSHIRISH
echo ======================================================================
echo.
echo 1. Backend (FastAPI - Port 8000)...
start "Kinochi Backend" cmd /k "cd backend && call .venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

echo 2. Kinochi Telegram Bot...
start "Kinochi Bot" cmd /k "cd bot && call .venv\Scripts\activate && python main.py"

echo 3. Admin Panel (Next.js - Port 3001)...
start "Kinochi Admin Panel" cmd /k "cd admin-panel && npm run dev -- -p 3001"

echo 4. Website (Next.js - Port 3000)...
start "Kinochi Website" cmd /k "cd website && npm run dev -- -p 3000"

echo.
echo Barcha xizmatlar alohida oynalarda ishga tushirildi!
echo • Backend: http://localhost:8000
echo • Admin Panel (Scraper): http://localhost:3001/scraper
echo • Website: http://localhost:3000
echo.
ping 127.0.0.1 -n 4 > nul
start http://localhost:3001/scraper
if not "%1"=="" exit /b
pause
goto menu
