@echo off
cd /d "%~dp0"
chcp 65001 > nul
title Kinochi - Barcha Xizmatlarni To'xtatish

echo ======================================================================
echo          KINOCHI - BARCHA XIZMATLARNI TO'XTATISH (CLEANUP)
echo ======================================================================
echo.

echo [1/3] Portlardagi jarayonlar (8000, 3001, 3000) to'xtatilmoqda...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ports = @(8000, 3001, 3000); " ^
    "foreach ($port in $ports) { " ^
    "    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue; " ^
    "    if ($conns) { " ^
    "        $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique; " ^
    "        foreach ($p in $pids) { " ^
    "            if ($p -gt 0) { " ^
    "                Stop-Process -Id $p -Force -ErrorAction SilentlyContinue; " ^
    "                Write-Host \"[OK] Port $port dagi jarayon (PID $p) to'xtatildi.\"; " ^
    "            } " ^
    "        } " ^
    "    } " ^
    "}"

echo [2/3] Scraper va Telegram MTProto jarayonlari to'xtatilmoqda...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | " ^
    "Where-Object { $_.CommandLine -like '*run_scraper.py*' } | " ^
    "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; Write-Host \"[OK] Scraper jarayoni (PID $($_.ProcessId)) to'xtatildi.\" }"

echo [3/3] Qoldiq lock fayllari tozalanmoqda...
if exist "scraper\.scraper_cli.pid" del /f /q "scraper\.scraper_cli.pid" >nul 2>&1
if exist "scraper\.scraper_pid" del /f /q "scraper\.scraper_pid" >nul 2>&1

echo.
echo ======================================================================
echo [OK] Barcha portlar va fon jarayonlari muvaffaqiyatli tozalandi!
echo ======================================================================
echo.
pause
