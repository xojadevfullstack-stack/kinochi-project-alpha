@echo off
cd /d "%~dp0"
chcp 65001 > nul
echo ==============================================
echo KINOCHI AUTO GRABBER (UZMOVI VA ASILMEDIA)
echo ==============================================
echo.

if not exist "backend\.venv\Scripts\python.exe" (
    echo [XATO] backend\.venv topilmadi!
    pause
    exit /b
)

echo Tanlang:
echo 1) Uzmovi botidan kinolarni yuklash (Dublikatlar tekshiriladi)
echo 2) Asilmedia botidan kinolarni yuklash (Dublikatlar tekshiriladi)
echo 3) Uzmovi saytidan katalog yig'ish (parse)
echo 4) Asilmedia saytidan katalog yig'ish (parse)
echo 5) Navbatdagi dublikatlarni tozalash (Bazadagilarini ajratish)
echo 6) Navbat statistikasini ko'rish
echo.
set /p choice="Tanlovingiz (1-6): "

if "%choice%"=="1" goto opt_uzmovi
if "%choice%"=="2" goto opt_asilmedia
if "%choice%"=="3" goto opt_parse_uzmovi
if "%choice%"=="4" goto opt_parse_asilmedia
if "%choice%"=="5" goto opt_clean
if "%choice%"=="6" goto opt_stats
echo Noto'g'ri tanlov.
goto end

:opt_uzmovi
set codes=
set /p codes="Film kodlari (masalan: 15 yoki 1-5 yoki 10,20) [Bo'sh qoldirsangiz navbatdan olinadi]: "
if not "%codes%"=="" (
    backend\.venv\Scripts\python.exe scraper/run_scraper.py --download --target uzmovi --codes %codes%
    goto end
)
set count=5
set /p count="Nechta kino yuklansin? [Standart: 5, masalan: 10, 20, 50, 100]: "
backend\.venv\Scripts\python.exe scraper/run_scraper.py --download --target uzmovi --limit %count%
goto end

:opt_asilmedia
set count=5
set /p count="Nechta kino yuklansin? [Standart: 5, masalan: 10, 20, 50, 100]: "
backend\.venv\Scripts\python.exe scraper/run_scraper.py --download --target asilmedia --limit %count%
goto end

:opt_parse_uzmovi
set pages=3
set /p pages="Nechta sahifa yig'ilsin? [Standart: 3, masalan: 5, 10]: "
backend\.venv\Scripts\python.exe scraper/run_scraper.py --parse --source uzmovi --pages %pages%
goto end

:opt_parse_asilmedia
set pages=3
set /p pages="Nechta sahifa yig'ilsin? [Standart: 3, masalan: 5, 10]: "
backend\.venv\Scripts\python.exe scraper/run_scraper.py --parse --source asilmedia --pages %pages%
goto end

:opt_clean
backend\.venv\Scripts\python.exe scraper/run_scraper.py --clean-duplicates
goto end

:opt_stats
backend\.venv\Scripts\python.exe scraper/run_scraper.py --stats
goto end

:end
echo.
pause
