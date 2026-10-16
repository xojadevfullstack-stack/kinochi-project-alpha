# ops/pilot.ps1: Kinochi TMDb Pilot Urug'lantirish (Seed Ingestor Pilot) Skripti
# Windows PowerShell 5.1 mosligi uchun ASCII formatida yozilgan.

[CmdletBinding()]
param (
    [Parameter(Mandatory = $false)]
    [int]$Limit = 20,

    [Parameter(Mandatory = $false)]
    [switch]$DryRun,

    [Parameter(Mandatory = $false)]
    [switch]$AutoConfirm
)

$ErrorActionPreference = 'Stop'

# Asosiy kataloglar
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$PythonExe = Join-Path $RepoRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}
$IngestorScript = Join-Path $RepoRoot "scraper\tmdb_top_ingestor.py"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "         KINOCHI TMDB TOP SEED INGESTOR: PILOT BOSQICHI          " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "[INFO] Limit: $Limit ta film"
if ($DryRun) {
    Write-Host "[OGOHLANTIRISH] -DryRun rejimi faol. Hech qanday ma'lumot o'zgartirilmaydi." -ForegroundColor Yellow
}

# 1. SEED_INCLUDE_SERIES tekshiruvi (faqat filmlar uchun ruxsat berilgan)
$SeedIncludeSeries = [System.Environment]::GetEnvironmentVariable("SEED_INCLUDE_SERIES")
if ($SeedIncludeSeries -and ($SeedIncludeSeries.Trim().ToLower() -eq "true" -or $SeedIncludeSeries.Trim() -eq "1")) {
    Write-Host "[XATO] SEED_INCLUDE_SERIES muhit o'zgaruvchisi 'true' deb sozlangan!" -ForegroundColor Red
    Write-Host "Ushbu pilot faqat filmlar (movies only) uchun mo'ljallangan." -ForegroundColor Red
    Write-Host "Iltimos, SEED_INCLUDE_SERIES=false qilib qayta ishga tushiring." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] SEED_INCLUDE_SERIES 'true' emas. Pilot faqat filmlarga mo'ljallangan." -ForegroundColor Green

# 2. Ingestor skripti mavjudligini tekshirish
if (-not (Test-Path $IngestorScript)) {
    Write-Host "[XATO] Ingestor skripti topilmadi: $IngestorScript" -ForegroundColor Red
    exit 1
}

# 3. TMDb urug'larini yig'ish (--build-seeds)
Write-Host "`n>>> QADAM 1: TMDB URUG'LARINI YIG'ISH (--build-seeds)..." -ForegroundColor Yellow
if ($DryRun) {
    Write-Host "[DRY-RUN] 'python scraper/tmdb_top_ingestor.py --build-seeds' simulyatsiya qilindi."
} else {
    & $PythonExe "$IngestorScript" --build-seeds
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[XATO] build-seeds buyrug'i muvaffaqiyatsiz tugadi (kod: $LASTEXITCODE)!" -ForegroundColor Red
        exit 1
    }
}

# 4. Hozirgi statistika (--stats)
Write-Host "`n>>> QADAM 2: TIZIM STATISTIKASI (--stats)..." -ForegroundColor Yellow
if ($DryRun) {
    Write-Host "[DRY-RUN] 'python scraper/tmdb_top_ingestor.py --stats' simulyatsiya qilindi."
} else {
    & $PythonExe "$IngestorScript" --stats
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[XATO] stats buyrug'i muvaffaqiyatsiz tugadi (kod: $LASTEXITCODE)!" -ForegroundColor Red
        exit 1
    }
}

# 5. O'zbek manbalaridan nomzodlarni qidirish (--search --limit 20)
Write-Host "`n>>> QADAM 3: O'ZBEK MANBALARIDAN QIDIRISH (--search --limit $Limit)..." -ForegroundColor Yellow
if ($DryRun) {
    Write-Host "[DRY-RUN] 'python scraper/tmdb_top_ingestor.py --search --limit $Limit' simulyatsiya qilindi."
} else {
    & $PythonExe "$IngestorScript" --search --limit $Limit
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[XATO] search buyrug'i muvaffaqiyatsiz tugadi (kod: $LASTEXITCODE)!" -ForegroundColor Red
        exit 1
    }
}

# 6. Qo'lda ko'rib chiqish (Manual Review) bo'yicha ko'rsatmalar
Write-Host "`n=================================================================" -ForegroundColor Cyan
Write-Host "             NOMZODLARNI QO'LDA TEKSHIRISH (MANUAL REVIEW)       " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "Qidiruv natijasida topilgan nomzodlarni tekshirish usullari:"
Write-Host "  1. Admin Panel orqali: http://localhost:3001/admin/scraper"
Write-Host "     'Seed Candidates' bo'limida topilgan nomzodlar va ularning"
Write-Host "     match_status hamda confidence ko'rsatkichlarini ko'ring."
Write-Host "  2. Baza so'rovi orqali (Neon SQL Editor):"
Write-Host "     SELECT id, tmdb_id, title_uz, title_original, match_status, confidence"
Write-Host "     FROM seed_candidates WHERE match_status = 'found' LIMIT $Limit;"
Write-Host "=================================================================" -ForegroundColor Cyan

# 7. Navbatga qo'yish (Dry-run: --enqueue --limit 20)
Write-Host "`n>>> QADAM 4: NAVBATGA QO'YISH PREVIEW (DRY-RUN)..." -ForegroundColor Yellow
if ($DryRun) {
    Write-Host "[DRY-RUN] 'python scraper/tmdb_top_ingestor.py --enqueue --limit $Limit' simulyatsiya qilindi."
} else {
    & $PythonExe "$IngestorScript" --enqueue --limit $Limit
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[XATO] enqueue preview buyrug'i muvaffaqiyatsiz tugadi!" -ForegroundColor Red
        exit 1
    }
}

# 8. Haqiqiy navbatga qo'yishdan oldin tasdiqlash
Write-Host "`n>>> QADAM 5: HAQIQIY ENQUEUE TASDIQLASH..." -ForegroundColor Yellow
if ($DryRun) {
    Write-Host "[DRY-RUN] Haqiqiy enqueue o'tkazib yuborildi."
} else {
    $Confirm = "NO"
    if ($AutoConfirm) {
        $Confirm = "YES"
        Write-Host "[INFO] -AutoConfirm parametri orqali avtomatik 'YES' qabul qilindi."
    } else {
        Write-Host "Haqiqatan ham yuqoridagi $Limit ta nomzodni yuklash navbatiga qo'shmoqchimisiz?" -ForegroundColor Yellow
        $Typed = Read-Host "Tasdiqlash uchun aniq 'YES' deb yozing"
        if ($Typed) { $Confirm = $Typed.Trim() }
    }

    if ($Confirm -ne "YES") {
        Write-Host "`n[RAD ETILDI] Enqueue bekor qilindi. Baza o'zgarishsiz qoldi." -ForegroundColor Yellow
        exit 0
    }

    Write-Host "`nNomzodlar navbatga kiritilmoqda (--execute)..."
    & $PythonExe "$IngestorScript" --enqueue --limit $Limit --execute
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[XATO] Haqiqiy enqueue muvaffaqiyatsiz tugadi (kod: $LASTEXITCODE)!" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] $Limit ta film muvaffaqiyatli navbatga qo'shildi!" -ForegroundColor Green
}

# 9. Keyingi qadamlar (Worker va Monitoring)
Write-Host "`n=================================================================" -ForegroundColor Green
Write-Host "         PILOT UCHUN KEYINGI QADAMLAR (GRABBER VA MONITORING)    " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "1. Worker / Grabberni ishga tushirish (navbatdagi filmlarni yuklash):"
Write-Host "   .\start_grabber.bat"
Write-Host "   (yoki to'g'ridan-to'g'ri: python -m scraper.run_scraper --mode grabber --limit $Limit)"
Write-Host ""
Write-Host "2. Navbat va yuklanish holatini kuzatish:"
Write-Host "   python -m scraper.tmdb_top_ingestor --stats"
Write-Host "   (yoki Admin panelda: /admin/scraper bo'limi)"
Write-Host "=================================================================" -ForegroundColor Green

exit 0
