# ops/go_live.ps1: Kinochi Production Go-Live va Xavfsiz Reset Skripti
# Windows PowerShell 5.1 mosligi uchun ASCII formatida yozilgan.

[CmdletBinding()]
param (
    [Parameter(Mandatory = $false)]
    [string]$UrlEnvVar = "DATABASE_URL",

    [Parameter(Mandatory = $false)]
    [switch]$DryRun,

    [Parameter(Mandatory = $false)]
    [switch]$SkipReset,

    [Parameter(Mandatory = $false)]
    [switch]$SkipBackup
)

$ErrorActionPreference = 'Stop'

# Asosiy kataloglar
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$BackendDir = Join-Path $RepoRoot "backend"
$OpsLogsDir = Join-Path $RepoRoot "ops\logs"
$BackupsDir = Join-Path $RepoRoot "backups"

# Jildlarni yaratish
if (-not (Test-Path $OpsLogsDir)) {
    New-Item -ItemType Directory -Path $OpsLogsDir -Force | Out-Null
}
if (-not (Test-Path $BackupsDir)) {
    New-Item -ItemType Directory -Path $BackupsDir -Force | Out-Null
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $OpsLogsDir "go_live_$Timestamp.log"

function Log-Message {
    param (
        [string]$Message,
        [string]$Phase = "GENERAL",
        [string]$Level = "INFO",
        [ConsoleColor]$Color = [ConsoleColor]::White
    )
    $TimeStr = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$TimeStr] [$Phase] [$Level] $Message"
    Add-Content -Path $LogFile -Value $LogEntry -Encoding UTF8
    Write-Host "[$Level] $Message" -ForegroundColor $Color
}

function Log-Success {
    param([string]$Message, [string]$Phase = "GENERAL")
    Log-Message -Message $Message -Phase $Phase -Level "OK" -Color Green
}

function Log-Warn {
    param([string]$Message, [string]$Phase = "GENERAL")
    Log-Message -Message $Message -Phase $Phase -Level "OGOHLANTIRISH" -Color Yellow
}

function Log-Error {
    param([string]$Message, [string]$Phase = "GENERAL")
    Log-Message -Message $Message -Phase $Phase -Level "XATO" -Color Red
}

function Get-DbHostName {
    param([string]$RawUrl)
    if ([string]::IsNullOrWhiteSpace($RawUrl)) { return "NONE" }
    try {
        $Cleaned = $RawUrl -replace "^postgres(?:ql)?(?:\+[a-zA-Z0-9_]+)?://", "http://"
        $Uri = [System.Uri]$Cleaned
        return $Uri.Host
    } catch {
        return "UNKNOWN_HOST"
    }
}

# Python dasturini aniqlash
$PythonExe = Join-Path $RepoRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "          KINOCHI PRODUCTION GO-LIVE VA RESET PROTOKOLI          " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Log-Message -Message "Go-Live skripti boshlandi. Log fayli: $LogFile" -Phase "INIT"

# 1. URL va DB Xost tekshiruvi
$TargetDbUrl = [System.Environment]::GetEnvironmentVariable($UrlEnvVar)
if ([string]::IsNullOrWhiteSpace($TargetDbUrl)) {
    Log-Error "Belgilangan '$UrlEnvVar' muhit o'zgaruvchisi topilmadi yoki bo'sh!" -Phase "INIT"
    exit 1
}
$DbHost = Get-DbHostName -RawUrl $TargetDbUrl
Log-Message -Message "Nishon DB Xosti: $DbHost (Muhit: $UrlEnvVar)" -Phase "INIT"

if ($DryRun) {
    Log-Warn "DIQQAT: -DryRun rejimi faol. Hech qanday ma'lumot o'zgartirilmaydi." -Phase "INIT"
}

# -------------------------------------------------------------
# FAZA A: PREFLIGHT
# -------------------------------------------------------------
Write-Host "`n>>> FAZA A: PREFLIGHT TEKSHIRUVLARI..." -ForegroundColor Yellow

# A.1. Disk bo'sh joyini tekshirish (kamida 2 GB)
$DriveName = (Get-Item $RepoRoot).PSDrive.Name
$DriveObj = Get-PSDrive -Name $DriveName
$FreeSpaceGB = [math]::Round($DriveObj.Free / 1GB, 2)
if ($FreeSpaceGB -lt 2.0) {
    Log-Error "Diskda yetarli joy yo'q ($($DriveName):). Kamida 2.0 GB kerak, mavjud: $FreeSpaceGB GB" -Phase "PREFLIGHT"
    exit 1
}
Log-Success "Diskda yetarli joy mavjud: $FreeSpaceGB GB bo'sh ($($DriveName):)." -Phase "PREFLIGHT"

# A.2. Scraper lock faylini tekshirish
$LockPath = Join-Path $RepoRoot "scraper\.scraper_cli.lock"
$PidPath = Join-Path $RepoRoot "scraper\.scraper_cli.pid"
if (Test-Path $LockPath) {
    $IsLocked = $false
    try {
        $FileStream = [System.IO.File]::Open($LockPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
        if ($FileStream) {
            $FileStream.Close()
            $FileStream.Dispose()
        }
    } catch {
        $IsLocked = $true
    }

    $ScraperRunning = $false
    if (Test-Path $PidPath) {
        $ScraperPid = (Get-Content $PidPath -ErrorAction SilentlyContinue | Out-String).Trim()
        if ($ScraperPid -match '^\d+$') {
            $Proc = Get-Process -Id [int]$ScraperPid -ErrorAction SilentlyContinue
            if ($Proc) { $ScraperRunning = $true }
        }
    }

    if ($IsLocked -or $ScraperRunning) {
        Log-Error "Scraper jarayoni hozirda ishlamoqda (lock band)! Avval scraperni to'xtating." -Phase "PREFLIGHT"
        exit 1
    } else {
        Log-Message "Eski (stale) lock fayli aniqlandi (jarayon ishlamayapti). Lock tozalanmoqda..." -Phase "PREFLIGHT"
        Remove-Item -Path $LockPath -Force -ErrorAction SilentlyContinue
        if (Test-Path $PidPath) { Remove-Item -Path $PidPath -Force -ErrorAction SilentlyContinue }
    }
}
Log-Success "Scraper lock fayli yo'q, hech qanday scraper ishlamayapti." -Phase "PREFLIGHT"

# A.3. pg_dump tekshiruvi
$PgDumpCmd = Get-Command "pg_dump" -ErrorAction SilentlyContinue
if (-not $PgDumpCmd) {
    if ($DryRun) {
        Log-Warn "pg_dump PATH da topilmadi. O'rnatish: winget install PostgreSQL.PostgreSQL" -Phase "PREFLIGHT"
    } else {
        Log-Error "pg_dump tizimda (PATH) topilmadi!" -Phase "PREFLIGHT"
        Log-Error "PostgreSQL CLI vositalarini o'rnatish uchun quyidagi buyruqni bajaring:" -Phase "PREFLIGHT"
        Log-Error "  winget install PostgreSQL.PostgreSQL" -Phase "PREFLIGHT"
        exit 1
    }
} else {
    Log-Success "pg_dump vositasi topildi: $($PgDumpCmd.Source)" -Phase "PREFLIGHT"
}

# A.4. DB ulanishi tekshiruvi
if ($DryRun) {
    Log-Message "[DRY-RUN] DB ulanishi tekshiruvi o'tkazib yuborildi (simulyatsiya)." -Phase "PREFLIGHT"
} else {
    Log-Message "DB ulanishi va jadvallar tekshirilmoqda..." -Phase "PREFLIGHT"
    $PrevEnv = $env:DATABASE_URL
    try {
        $env:DATABASE_URL = $TargetDbUrl
        & $PythonExe -m ops.db_checks --url-env-var $UrlEnvVar
        if ($LASTEXITCODE -ne 0) {
            Log-Error "DB preflight tekshiruvi muvaffaqiyatsiz tugadi (kod: $LASTEXITCODE)!" -Phase "PREFLIGHT"
            exit 1
        }
    } finally {
        $env:DATABASE_URL = $PrevEnv
    }
    Log-Success "DB preflight tekshiruvi muvaffaqiyatli yakunlandi." -Phase "PREFLIGHT"
}

# -------------------------------------------------------------
# FAZA B: BACKUP (ZAXIRA NUSXA OLISH)
# -------------------------------------------------------------
Write-Host "`n>>> FAZA B: ZAXIRA NUSXA OLISH..." -ForegroundColor Yellow
$BackupDumpFile = Join-Path $BackupsDir "kinochi_pre_reset_$Timestamp.dump"

if ($SkipBackup) {
    Log-Warn "OGOHLANTIRISH: -SkipBackup tanlangan! Zaxira nusxa olinmadi. Bu XAVFLI!" -Phase "BACKUP"
    $BackupDumpFile = $null
} elseif ($DryRun) {
    Log-Message "[DRY-RUN] pg_dump simulyatsiyasi: '$BackupDumpFile' yaratilishi kerak edi." -Phase "BACKUP"
    $BackupDumpFile = "SIMULATED_BACKUP"
} else {
    Log-Message "pg_dump orqali zaxira olinmoqda..." -Phase "BACKUP"
    # Maxfiy URL ni faqat native process argumentida beramiz, konsol/logga chiqarmaymiz
    & pg_dump -Fc --no-owner --dbname "$TargetDbUrl" -f "$BackupDumpFile"
    if ($LASTEXITCODE -ne 0 -or (-not (Test-Path $BackupDumpFile))) {
        Log-Error "pg_dump xatolik bilan tugadi yoki fayl yaratilmadi!" -Phase "BACKUP"
        exit 1
    }

    $DumpSize = (Get-Item $BackupDumpFile).Length
    $DumpSizeMB = [math]::Round($DumpSize / 1MB, 2)
    if ($DumpSize -lt 1048576) {
        Log-Error "Zaxira fayli hajmi 1 MB dan kichik ($DumpSizeMB MB)! Zaxira to'liq emas bo'lishi mumkin." -Phase "BACKUP"
        exit 1
    }

    $FileHash = (Get-FileHash -Algorithm SHA256 -Path $BackupDumpFile).Hash
    Log-Success "Zaxira muvaffaqiyatli olindi: $BackupDumpFile ($DumpSizeMB MB)" -Phase "BACKUP"
    Log-Message "Zaxira SHA256: $FileHash" -Phase "BACKUP"
}

# -------------------------------------------------------------
# FAZA C: MIGRATE (ALEMBIC HEADS & UPGRADE)
# -------------------------------------------------------------
Write-Host "`n>>> FAZA C: MIGRATSIYA..." -ForegroundColor Yellow
if ($DryRun) {
    Log-Message "[DRY-RUN] alembic upgrade head simulyatsiyasi." -Phase "MIGRATE"
} else {
    Push-Location $BackendDir
    try {
        $env:DATABASE_URL = $TargetDbUrl

        # alembic heads
        Log-Message "Alembic boshlarini tekshirish..." -Phase "MIGRATE"
        $HeadsOutput = & alembic heads
        if ($LASTEXITCODE -ne 0) {
            Log-Error "Alembic heads buyrug'i xatolik berdi!" -Phase "MIGRATE"
            exit 1
        }
        $HeadCount = ($HeadsOutput | Where-Object { $_ -match "\S+" }).Count
        if ($HeadCount -gt 1) {
            Log-Error "Bazada birdan ortiq alembic head mavjud! Tarmoqlanishni bartaraf eting." -Phase "MIGRATE"
            exit 1
        }

        # alembic upgrade head
        Log-Message "Alembic upgrade head ishga tushirilmoqda..." -Phase "MIGRATE"
        & alembic upgrade head
        if ($LASTEXITCODE -ne 0) {
            Log-Error "Alembic upgrade head xatolik bilan tugadi!" -Phase "MIGRATE"
            exit 1
        }

        # alembic check
        Log-Message "Alembic modellar sinxronligini tekshirish (alembic check)..." -Phase "MIGRATE"
        & alembic check
        if ($LASTEXITCODE -ne 0) {
            Log-Warn "Alembic check model va baza o'rtasida farq aniqladi (yoki ogohlantirish berdi)." -Phase "MIGRATE"
        }

        # db_checks orqali tasdiqlash
        Log-Message "Baza holati (alembic_version va pending default) tekshirilmoqda..." -Phase "MIGRATE"
        & $PythonExe -m ops.db_checks --url-env-var $UrlEnvVar --expected-alembic "e8f9a0b1c2d3" --expected-default "pending"
        if ($LASTEXITCODE -ne 0) {
            Log-Error "Migratsiyadan keyingi DB tekshiruvi muvaffaqiyatsiz bo'ldi!" -Phase "MIGRATE"
            exit 1
        }
    } finally {
        Pop-Location
    }
    Log-Success "Migratsiya muvaffaqiyatli yakunlandi." -Phase "MIGRATE"
}

# -------------------------------------------------------------
# FAZA D: DEPLOY GATE
# -------------------------------------------------------------
Write-Host "`n>>> FAZA D: DEPLOY GATE VA BACKEND RESTART..." -ForegroundColor Yellow
Log-Message "Backend muhitida SEED_GATE_MODE faolligi tekshirilmoqda..." -Phase "DEPLOY_GATE"
Log-Message "Eslatma: Agar backend alohida serverda (Render/VPS) ishlayotgan bo'lsa," -Phase "DEPLOY_GATE"
Log-Message "SEED_GATE_MODE o'zgaruvchisi kiritilganini tekshiring va servisni qayta ishga tushiring." -Phase "DEPLOY_GATE"

# Mahalliy backend ishlayotgan bo'lsa healthcheck
try {
    $HealthRes = Invoke-RestMethod -Uri "http://localhost:8000/docs" -TimeoutSec 3 -ErrorAction SilentlyContinue
    if ($HealthRes) {
        Log-Success "Mahalliy backend (port 8000) javob bermoqda." -Phase "DEPLOY_GATE"
    }
} catch {
    Log-Message "Mahalliy backend (port 8000) hozir ishlamayapti (masofaviy server tekshirilishi kerak)." -Phase "DEPLOY_GATE"
}

# -------------------------------------------------------------
# FAZA E: RESET (MEDIA JADVALLARINI TOZALASH)
# -------------------------------------------------------------
Write-Host "`n>>> FAZA E: MEDIA JADVALLARINI TOZALASH..." -ForegroundColor Yellow
$BaselineCountsPath = Join-Path $BackupsDir "counts_before.json"

if ($SkipReset) {
    Log-Warn "-SkipReset tanlangan. Media tozalash bosqichi o'tkazib yuborildi." -Phase "RESET"
} elseif ($DryRun) {
    Log-Message "[DRY-RUN] reset_media va redis_flush_cache simulyatsiya qilindi." -Phase "RESET"
} else {
    if (-not $BackupDumpFile -or (-not (Test-Path $BackupDumpFile))) {
        Log-Error "Tozalashni boshlashdan oldin haqiqiy zaxira fayli mavjud bo'lishi shart!" -Phase "RESET"
        exit 1
    }

    # E.1. Saqlanadigan jadvallar bazasini yozib olish
    Log-Message "Qatorlar soni saqlanmoqda: $BaselineCountsPath" -Phase "RESET"
    $env:DATABASE_URL = $TargetDbUrl
    & $PythonExe -m ops.db_checks --url-env-var $UrlEnvVar --save-baseline "$BaselineCountsPath"
    if ($LASTEXITCODE -ne 0) {
        Log-Error "Baseline qatorlar sonini saqlashda xatolik yuz berdi!" -Phase "RESET"
        exit 1
    }

    # E.2. scripts/reset_media.py ni chaqirish
    $ResetScript = Join-Path $RepoRoot "scripts\reset_media.py"
    Log-Message "scripts/reset_media.py orqali media jadvallar tozalanmoqda..." -Phase "RESET"
    & $PythonExe "$ResetScript" --backup-file "$BackupDumpFile" --execute --confirm YES --i-am-wiping-production --wipe-media
    if ($LASTEXITCODE -ne 0) {
        Log-Error "Media jadvallarni tozalash (reset_media.py) xatolik bilan tugadi!" -Phase "RESET"
        exit 1
    }

    # E.3. Redis keshini tozalash (faqat cache:*)
    Log-Message "Redis 'cache:*' kesh kalitlari tozalanmoqda..." -Phase "RESET"
    & $PythonExe -m ops.redis_flush_cache --execute --confirm YES
    if ($LASTEXITCODE -ne 0) {
        Log-Warn "Redis keshini tozalashda ogohlantirish yoki xatolik yuz berdi." -Phase "RESET"
    }

    # E.4. Natijani qayta tekshirish
    Log-Message "Tozalash natijasi tekshirilmoqda (--check-zero-media va --check-preserved-counts)..." -Phase "RESET"
    & $PythonExe -m ops.db_checks --url-env-var $UrlEnvVar --check-zero-media --check-preserved-counts "$BaselineCountsPath"
    if ($LASTEXITCODE -ne 0) {
        Log-Error "Tozalashdan keyingi tekshiruvda nomuvofiqlik aniqlandi!" -Phase "RESET"
        exit 1
    }
    Log-Success "Media jadvallari muvaffaqiyatli tozalandi (0 ta qator) va saqlanuvchi ma'lumotlar saqlandi." -Phase "RESET"
}

# -------------------------------------------------------------
# FAZA F: FINAL XULOSA
# -------------------------------------------------------------
Write-Host "`n=================================================================" -ForegroundColor Cyan
Write-Host "                GO-LIVE YAKUNIY HISOBOTI JADVALI                 " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

$FinalRevision = if ($DryRun) { "e8f9a0b1c2d3 (simulyatsiya)" } else { "e8f9a0b1c2d3" }
$FinalBackup = if ($BackupDumpFile) { $BackupDumpFile } else { "Yo'q (-SkipBackup)" }
$ResetStatus = if ($SkipReset) { "O'tkazib yuborildi" } elseif ($DryRun) { "Simulyatsiya" } else { "Muvaffaqiyatli (0 media qatorlari)" }

Write-Host "  Nishon DB Xosti    : $DbHost"
Write-Host "  Alembic Revision   : $FinalRevision"
Write-Host "  Zaxira fayli       : $FinalBackup"
Write-Host "  Media Reset Holati : $ResetStatus"
Write-Host "  Keyingi qadam      : ops/pilot.ps1 skriptini ishga tushirish"
Write-Host "=================================================================" -ForegroundColor Cyan
Log-Success "Go-Live jarayoni muvaffaqiyatli yakunlandi." -Phase "FINAL"

exit 0
