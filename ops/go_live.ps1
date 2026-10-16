# ops/go_live.ps1: Kinochi Production Go-Live va Xavfsiz Reset Skripti
# Windows PowerShell 5.1 mosligi uchun ASCII formatida yozilgan.

[CmdletBinding()]
param (
    [Parameter(Mandatory = $false)]
    [string]$UrlEnvVar = "DATABASE_URL",

    [Parameter(Mandatory = $false)]
    [string]$BackupFile = "",

    [Parameter(Mandatory = $false)]
    [switch]$DryRun,

    [Parameter(Mandatory = $false)]
    [switch]$SkipReset,

    [Parameter(Mandatory = $false)]
    [switch]$SkipBackup,

    [Parameter(Mandatory = $false)]
    [switch]$RehearsalAutoConfirm,

    [Parameter(Mandatory = $false)]
    [switch]$IgnoreRedisError,

    [Parameter(Mandatory = $false)]
    [switch]$IgnoreAlembicCheck,

    [Parameter(Mandatory = $false)]
    [ValidateSet("PREFLIGHT", "BACKUP", "MIGRATE", "DEPLOY_GATE", "RESET", "FINAL")]
    [string]$StartPhase = "PREFLIGHT"
)

$PhaseOrder = @{
    "PREFLIGHT"   = 1
    "BACKUP"      = 2
    "MIGRATE"     = 3
    "DEPLOY_GATE" = 4
    "RESET"       = 5
    "FINAL"       = 6
}
$StartPhaseNum = $PhaseOrder[$StartPhase.ToUpper()]

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

function Convert-ToLibpqUrl {
    param([string]$RawUrl)
    if ([string]::IsNullOrWhiteSpace($RawUrl)) { return "" }
    $Converted = $RawUrl -replace "^postgres(?:ql)?\+[a-zA-Z0-9_]+://", "postgresql://"
    $Converted = $Converted -replace "^postgres://", "postgresql://"
    $Converted = $Converted -replace "([?&])ssl=([a-zA-Z0-9_-]+)", '$1sslmode=$2'
    $Converted = $Converted -replace "([?&])sslmode=true", '$1sslmode=require'
    # Neon direct connection: pg_dump/pg_restore requires direct unpooled connection (strip -pooler)
    $Converted = $Converted -replace "-pooler\.", "."
    return $Converted
}

function Convert-ToAsyncpgUrl {
    param([string]$RawUrl)
    if ([string]::IsNullOrWhiteSpace($RawUrl)) { return "" }
    $u = $RawUrl -replace "-pooler\.", "."
    if ($u -match "^postgres(?:ql)?://") {
        $u = $u -replace "^postgres(?:ql)?://", "postgresql+asyncpg://"
    }
    $u = $u -replace "([?&])sslmode=([a-zA-Z0-9_-]+)", '$1ssl=$2'
    $u = $u -replace "([?&])sslmode=", '$1ssl='
    $u = $u -replace "[?&]channel_binding=[^&]+", ""
    $u = $u -replace "[?&]gssencmode=[^&]+", ""
    if ($u -notmatch "\?" -and $u -match "&") {
        $u = [regex]::new("&").Replace($u, "?", 1)
    }
    $u = ($u -replace "\?&", "?").TrimEnd("?&")
    return $u
}

# Python va Alembic dasturlarini aniqlash
$VenvScripts = Join-Path $RepoRoot "backend\.venv\Scripts"
if (Test-Path $VenvScripts) {
    $env:PATH = "$VenvScripts;$env:PATH"
}
$PgPaths = @(
    "C:\Program Files\PostgreSQL\18\bin",
    "C:\Program Files\PostgreSQL\17\bin",
    "C:\Program Files\PostgreSQL\16\bin",
    "C:\Program Files\PostgreSQL\15\bin"
)
foreach ($P in $PgPaths) {
    if (Test-Path $P) {
        $env:PATH = "$P;$env:PATH"
        break
    }
}
$PythonExe = Join-Path $VenvScripts "python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = "python"
}
$env:PYTHONPATH = "$RepoRoot;$BackendDir;$env:PYTHONPATH"

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
$DirectDbUrl = Convert-ToAsyncpgUrl -RawUrl $TargetDbUrl

# Rehearsal auto-confirm faqat localhost yoki 127.0.0.1 uchun ruxsat etiladi
if ($RehearsalAutoConfirm) {
    if ($DbHost -ne "localhost" -and $DbHost -ne "127.0.0.1") {
        Log-Error "-RehearsalAutoConfirm faqat localhost yoki 127.0.0.1 xosti uchun ruxsat etilgan! Joriy xost: $DbHost" -Phase "INIT"
        exit 1
    }
    Log-Warn "-RehearsalAutoConfirm faollashtirildi (faqat mahalliy sinov bazasi: $DbHost uchun)." -Phase "INIT"
}

if ($DryRun) {
    Log-Warn "DIQQAT: -DryRun rejimi faol. Hech qanday ma'lumot o'zgartirilmaydi." -Phase "INIT"
}

# -------------------------------------------------------------
# FAZA A: PREFLIGHT
# -------------------------------------------------------------
if ($StartPhaseNum -le 1) {
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
        $DockerPgAvailable = $false
        if ($DbHost -in @("localhost", "127.0.0.1")) {
            $DockerInspect = & docker inspect kinochi_rehearsal_pg 2>$null
            if ($LASTEXITCODE -eq 0) {
                $DockerPgAvailable = $true
            }
        }

        if ($DockerPgAvailable) {
            Log-Success "Xostda pg_dump yo'q, lekin Docker 'kinochi_rehearsal_pg' konteyneri mavjud (rehearsal rejimi)." -Phase "PREFLIGHT"
        } elseif ($DryRun) {
            Log-Warn "pg_dump PATH da topilmadi. O'rnatish: winget install PostgreSQL.PostgreSQL" -Phase "PREFLIGHT"
        } else {
            Log-Error "pg_dump tizimda (PATH) topilmadi!" -Phase "PREFLIGHT"
            Log-Error "PostgreSQL CLI vositalarini o'rnatish uchun quyidagi buyruqni bajaring:" -Phase "PREFLIGHT"
            Log-Error "  winget install PostgreSQL.PostgreSQL" -Phase "PREFLIGHT"
            exit 1
        }
    } else {
        $PgDumpVer = (& $PgDumpCmd.Source --version 2>&1 | Out-String).Trim()
        Log-Success "pg_dump vositasi topildi: $($PgDumpCmd.Source) ($PgDumpVer)" -Phase "PREFLIGHT"
    }

    # A.4. DB ulanishi tekshiruvi
    if ($DryRun) {
        Log-Message "[DRY-RUN] DB ulanishi tekshiruvi o'tkazib yuborildi (simulyatsiya)." -Phase "PREFLIGHT"
    } else {
        Log-Message "DB ulanishi va jadvallar tekshirilmoqda..." -Phase "PREFLIGHT"
        $PrevEnv = $env:DATABASE_URL
        try {
            $env:DATABASE_URL = $DirectDbUrl
            & $PythonExe -m ops.db_checks --url-env-var $UrlEnvVar --allow-empty
            if ($LASTEXITCODE -ne 0) {
                Log-Error "DB preflight tekshiruvi muvaffaqiyatsiz tugadi (kod: $LASTEXITCODE)!" -Phase "PREFLIGHT"
                exit 1
            }
        } finally {
            $env:DATABASE_URL = $PrevEnv
        }
        Log-Success "DB preflight tekshiruvi muvaffaqiyatli yakunlandi." -Phase "PREFLIGHT"
    }
} else {
    Log-Message "PREFLIGHT fazasi o'tkazib yuborildi (-StartPhase $StartPhase)" -Phase "PREFLIGHT"
}

# -------------------------------------------------------------
# FAZA B: BACKUP (ZAXIRA NUSXA OLISH)
# -------------------------------------------------------------
$BackupDumpFile = Join-Path $BackupsDir "kinochi_pre_reset_$Timestamp.dump"
$MinDumpSize = if ($RehearsalAutoConfirm) { 10240 } else { 1048576 }

if ($StartPhaseNum -le 2) {
    Write-Host "`n>>> FAZA B: ZAXIRA NUSXA OLISH..." -ForegroundColor Yellow

    if ($SkipBackup -or (-not [string]::IsNullOrWhiteSpace($BackupFile) -and (Test-Path $BackupFile))) {
        if (-not [string]::IsNullOrWhiteSpace($BackupFile)) {
            if (-not (Test-Path $BackupFile)) {
                Log-Error "Ko'rsatilgan -BackupFile fayli topilmadi: '$BackupFile'" -Phase "BACKUP"
                exit 1
            }
            $DumpSize = (Get-Item $BackupFile).Length
            if ($DumpSize -lt $MinDumpSize) {
                Log-Error "Ko'rsatilgan -BackupFile hajmi kutilgan minimal hajmdan ($MinDumpSize bayt) kichik! Zaxira to'liq emas bo'lishi mumkin." -Phase "BACKUP"
                exit 1
            }
            $BackupDumpFile = (Resolve-Path $BackupFile).Path
            Log-Success "Mavjud zaxira fayli tasdiqlandi: $BackupDumpFile" -Phase "BACKUP"
        } else {
            Log-Warn "OGOHLANTIRISH: -SkipBackup tanlangan va -BackupFile ko'rsatilmadi! Zaxira nusxa olinmadi. Bu XAVFLI!" -Phase "BACKUP"
            $BackupDumpFile = $null
        }
    } elseif ($DryRun) {
        Log-Message "[DRY-RUN] pg_dump simulyatsiyasi: '$BackupDumpFile' yaratilishi kerak edi." -Phase "BACKUP"
        $BackupDumpFile = "SIMULATED_BACKUP"
    } else {
        Log-Message "pg_dump orqali zaxira olinmoqda..." -Phase "BACKUP"
        $DumpSuccess = $false
        $PgDumpError = ""
        $OldEAP = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            if ($PgDumpCmd) {
                $LibpqDbUrl = Convert-ToLibpqUrl -RawUrl $TargetDbUrl
                $PgDumpOutput = & pg_dump -Fc --no-owner --dbname "$LibpqDbUrl" -f "$BackupDumpFile" 2>&1
                if ($LASTEXITCODE -eq 0 -and (Test-Path $BackupDumpFile) -and ((Get-Item $BackupDumpFile).Length -ge $MinDumpSize)) {
                    $DumpSuccess = $true
                } else {
                    $PgDumpError = ($PgDumpOutput | Out-String).Trim()
                }
            } else {
                $PyDumpOutput = & $PythonExe -m ops.db_checks --url-env-var $UrlEnvVar --create-backup "$BackupDumpFile" 2>&1
                if ($LASTEXITCODE -eq 0 -and (Test-Path $BackupDumpFile) -and ((Get-Item $BackupDumpFile).Length -ge $MinDumpSize)) {
                    $DumpSuccess = $true
                } else {
                    $PgDumpError = ($PyDumpOutput | Out-String).Trim()
                }
            }
        } finally {
            $ErrorActionPreference = $OldEAP
        }
        if (-not $DumpSuccess) {
            if (Test-Path $BackupDumpFile) {
                Remove-Item -Path $BackupDumpFile -Force -ErrorAction SilentlyContinue
            }
            if ($PgDumpError) {
                # Maxfiy ma'lumotlarni yashirish
                $SanitizedErr = $PgDumpError -replace "://[^@]+@", "://***@"
                Log-Warn "pg_dump tafsiloti: $SanitizedErr" -Phase "BACKUP"
            }
            Log-Error "pg_dump xatolik bilan tugadi!" -Phase "BACKUP"
            exit 1
        }

        $DumpSize = (Get-Item $BackupDumpFile).Length
        if ($DumpSize -lt $MinDumpSize) {
            Log-Error "Zaxira hajmi minimal hajmdan ($MinDumpSize bayt) kichik!" -Phase "BACKUP"
            exit 1
        }

        Log-Message "Zaxira yaxlitligi (pg_restore --list) tekshirilmoqda..." -Phase "BACKUP"
        $VerifySuccess = $false
        if (Get-Command "pg_restore" -ErrorAction SilentlyContinue) {
            & pg_restore --list "$BackupDumpFile" | Out-Null
            if ($LASTEXITCODE -eq 0) { $VerifySuccess = $true }
        }
        if (-not $VerifySuccess) {
            & $PythonExe -m ops.db_checks --url-env-var $UrlEnvVar --verify-backup "$BackupDumpFile"
            if ($LASTEXITCODE -eq 0) { $VerifySuccess = $true }
        }
        if (-not $VerifySuccess) {
            Log-Error "Zaxira fayli yaxlitligi tekshiruvidan o'tmadi (pg_restore xatosi)!" -Phase "BACKUP"
            exit 1
        }

        $FileHash = (Get-FileHash -Algorithm SHA256 -Path $BackupDumpFile).Hash
        Log-Success "Zaxira muvaffaqiyatli olindi: $BackupDumpFile ($DumpSize bayt, $DumpSizeMB MB)" -Phase "BACKUP"
        Log-Message "Zaxira SHA256: $FileHash" -Phase "BACKUP"
    }
} else {
    Log-Message "BACKUP fazasi o'tkazib yuborildi (-StartPhase $StartPhase)" -Phase "BACKUP"
    if (-not [string]::IsNullOrWhiteSpace($BackupFile) -and (Test-Path $BackupFile)) {
        $BackupDumpFile = (Resolve-Path $BackupFile).Path
        Log-Message "Oldindan mavjud zaxira fayli biriktirildi: $BackupDumpFile" -Phase "BACKUP"
    }
}

# -------------------------------------------------------------
# FAZA C: MIGRATE (ALEMBIC HEADS & UPGRADE)
# -------------------------------------------------------------
if ($StartPhaseNum -le 3) {
    Write-Host "`n>>> FAZA C: MIGRATSIYA..." -ForegroundColor Yellow
    if ($DryRun) {
        Log-Message "[DRY-RUN] alembic upgrade head simulyatsiyasi." -Phase "MIGRATE"
    } else {
        Push-Location $BackendDir
        $OldEAP = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        try {
            $env:DATABASE_URL = $DirectDbUrl

            # alembic heads
            Log-Message "Alembic boshlarini tekshirish..." -Phase "MIGRATE"
            $HeadsOutput = & alembic heads 2>&1
            if ($LASTEXITCODE -ne 0) {
                $SanitizedHeadsErr = ($HeadsOutput | Out-String).Trim() -replace "://[^@]+@", "://***@"
                Log-Error "Alembic heads buyrug'i xatolik berdi: $SanitizedHeadsErr" -Phase "MIGRATE"
                exit 1
            }
            $HeadCount = ($HeadsOutput | Where-Object { $_ -match "\S+" }).Count
            if ($HeadCount -gt 1) {
                Log-Error "Bazada birdan ortiq alembic head mavjud! Tarmoqlanishni bartaraf eting." -Phase "MIGRATE"
                exit 1
            }

            # alembic upgrade head
            Log-Message "Alembic upgrade head ishga tushirilmoqda..." -Phase "MIGRATE"
            $UpgradeOutput = & alembic upgrade head 2>&1
            if ($LASTEXITCODE -ne 0) {
                $SanitizedUpErr = ($UpgradeOutput | Out-String).Trim() -replace "://[^@]+@", "://***@"
                Log-Error "Alembic upgrade head xatolik bilan tugadi: $SanitizedUpErr" -Phase "MIGRATE"
                exit 1
            }

            # alembic check
            Log-Message "Alembic modellar sinxronligini tekshirish (alembic check)..." -Phase "MIGRATE"
            $CheckOutput = & alembic check 2>&1
            if ($LASTEXITCODE -ne 0) {
                if (-not $IgnoreAlembicCheck) {
                    Log-Error "Alembic check farq aniqladi! Yangi migratsiya talab etiladi." -Phase "MIGRATE"
                    exit 1
                }
                Log-Warn "Alembic check model va baza o'rtasida farq aniqladi, lekin -IgnoreAlembicCheck sababli davom etilmoqda." -Phase "MIGRATE"
            }

            # db_checks orqali tasdiqlash
            Log-Message "Baza holati (alembic_version va pending default) tekshirilmoqda..." -Phase "MIGRATE"
            & $PythonExe -m ops.db_checks --url-env-var $UrlEnvVar --expected-alembic "e8f9a0b1c2d3" --expected-default "pending"
            if ($LASTEXITCODE -ne 0) {
                Log-Error "Migratsiyadan keyingi DB tekshiruvi muvaffaqiyatsiz bo'ldi!" -Phase "MIGRATE"
                exit 1
            }
        } finally {
            $ErrorActionPreference = $OldEAP
            Pop-Location
        }
        Log-Success "Migratsiya muvaffaqiyatli yakunlandi." -Phase "MIGRATE"
    }
} else {
    Log-Message "MIGRATE fazasi o'tkazib yuborildi (-StartPhase $StartPhase)" -Phase "MIGRATE"
}

# -------------------------------------------------------------
# FAZA D: DEPLOY GATE
# -------------------------------------------------------------
if ($StartPhaseNum -le 4) {
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

    # Gate deploy qilinganini tasdiqlash
    if (-not $DryRun) {
        if ($RehearsalAutoConfirm) {
            Log-Message "[RehearsalAutoConfirm] DEPLOYED avtomatik tasdiqlandi." -Phase "DEPLOY_GATE"
        } else {
            $TypedGate = Read-Host "Davom etishdan oldin backend SEED_GATE_MODE bilan yangilanganini tasdiqlang ('DEPLOYED' deb yozing)"
            if ($TypedGate -ne "DEPLOYED") {
                Log-Error "Tasdiqlash kodi noto'g'ri kiritildi ('$TypedGate'). Jarayon to'xtatildi!" -Phase "DEPLOY_GATE"
                exit 1
            }
        }
    }
} else {
    Log-Message "DEPLOY_GATE fazasi o'tkazib yuborildi (-StartPhase $StartPhase)" -Phase "DEPLOY_GATE"
}

# -------------------------------------------------------------
# FAZA E: RESET (MEDIA JADVALLARINI TOZALASH)
# -------------------------------------------------------------
if ($StartPhaseNum -le 5) {
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

        # E.0. Media tozalashni tasdiqlash
        if ($RehearsalAutoConfirm) {
            Log-Message "[RehearsalAutoConfirm] WIPE-MEDIA avtomatik tasdiqlandi." -Phase "RESET"
        } else {
            $TypedReset = Read-Host "Media jadvallarini tozalashni tasdiqlash uchun 'WIPE-MEDIA' deb yozing"
            if ($TypedReset -ne "WIPE-MEDIA") {
                Log-Error "Tasdiqlash kodi noto'g'ri kiritildi ('$TypedReset'). Jarayon to'xtatildi!" -Phase "RESET"
                exit 1
            }
        }

        # E.1. Saqlanadigan jadvallar bazasini yozib olish
        Log-Message "Qatorlar soni saqlanmoqda: $BaselineCountsPath" -Phase "RESET"
        $env:DATABASE_URL = $DirectDbUrl
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
            if ($IgnoreRedisError) {
                Log-Warn "Redis keshini tozalashda xatolik yuz berdi, lekin -IgnoreRedisError sababli davom etilmoqda." -Phase "RESET"
            } else {
                Log-Error "Redis keshini tozalash muvaffaqiyatsiz bo'ldi! To'xtatildi (o'tkazib yuborish uchun -IgnoreRedisError bering)." -Phase "RESET"
                exit 1
            }
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
} else {
    Log-Message "RESET fazasi o'tkazib yuborildi (-StartPhase $StartPhase)" -Phase "RESET"
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
