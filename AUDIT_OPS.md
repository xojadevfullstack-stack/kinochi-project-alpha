# AUDIT_OPS.md: Production Go-Live va Pilot Operatsion Skriptlari Auditi

Auditor: Independent Senior DevOps/Security Auditor  
Audit Sanasi: 2026-10-16  
Til: O'zbekcha (Lotin) / Texnik identifikatorlar inglizcha  

---

## 1. Topilmalar Xulosasi (Severity Counts)

| Daraja (Severity) | Jami Topildi | Tuzatildi (FIXED) | Ochiq (OPEN) |
|---|---|---|---|
| **CRITICAL** | 1 | 1 | 0 |
| **HIGH** | 1 | 1 | 0 |
| **MEDIUM** | 2 | 2 | 0 |
| **LOW** | 2 | 2 | 0 |
| **JAMI** | **6** | **6** | **0** |

---

## 2. Tekshiruv Ro'yxati Holati (Checklist Status)

| # | Tekshiruv Bandi (Checklist Item) | Holat (Status) | Izoh / Topilma |
|---|---|---|---|
| 1 | Build vs claims: `OPS_PROGRESS.md` ticks vs git log/diff | **OK** | Barcha 7 ta commit (`e2a20e5` dan `7ac10e1` gacha) git tarixiga to'liq mos. |
| 2 | Secret leakage: Barcha print/log/error va `.gitignore` tekshiruvi | **OK** | Maxfiy kalitlar va ulanish URL lari logga chiqmaydi; faqat DB xosti ko'rsatiladi; `.dump`, `.log`, `.env.local` git tomonidan kuzatilmaydi. |
| 3 | Destructive-path analysis: Barcha o'chiruvchi buyruqlar himoyasi | **OK** | **OF-001** tuzatildi (`27fa10a`): `reset_media.py` va `go_live.ps1` da `--wipe-media` qo'shildi. |
| 4 | Native-command exit codes: `$LASTEXITCODE` va `$ErrorActionPreference` | **OK** | **OF-002** tuzatildi (`00f06b2`): `alembic check` xatosida to'xtaydi. **OF-005** tuzatildi (`894d8db`): Redis xatosida to'xtaydi (`-IgnoreRedisError` bilan boshqariladi). |
| 5 | Paths: Probel va kirill belgilari bo'lgan kataloglarda `-DryRun` | **OK** | `ops/_audit_tmp/sinov papka cyrillic тесты` dan muvaffaqiyatli o'tdi; fayllar 100% sof ASCII. |
| 6 | `-DryRun` inertness: Soxta qiymatlar bilan tashqi o'zgarishlar yo'qligi | **OK** | Faqat `ops/logs/` fayli yoziladi; bazaga yoki loyiha fayllariga 0 ta o'zgarish kiritiladi. |
| 7 | Idempotent resume: Bosqichma-bosqich qayta ishga tushirish | **OK** | **OF-006** tuzatildi (`e170434`): `-StartPhase` parametri qo'shildi, istalgan fazadan davom ettirish mumkin. |
| 8 | Backup verification realism: Truncated dump, restore --list, disk full | **OK** | **OF-003** tuzatildi (`4590ed6`): `pg_restore --list` bilan arxiv tekshiriladi. **OF-004** tuzatildi (`4f6934b`): `-BackupFile` parametri qo'shildi. |
| 9 | Migrate phase: Boshlar soni, kutilgan reviziya, migratsiya ketma-ketligi | **OK** | **OF-002** tuzatildi (`00f06b2`): `alembic check` diff aniqlasa jarayon qat'iy to'xtatiladi. |
| 10| Reset phase: real flaglar, jadvallar solishtiruvi, `cache:*` kesh | **OK** | **OF-001** tuzatildi (`27fa10a`): media jadvallari xavfsiz tozalanadi va tekshiriladi. |
| 11| `pilot.ps1`: `SEED_INCLUDE_SERIES` himoyasi, YES tasdiqlash, jadval ko'rinishi | **OK** | `SEED_INCLUDE_SERIES=true` bloklanadi; aniq `YES` talab qilinadi; preview ko'rsatiladi. |
| 12| `new_telegram_session.py`: Sessiya sirliligi, `.env.local`, `--force` himoyasi | **OK** | Sessiya hech qachon ekranga chiqmaydi; faqat `.env.local` ga yoziladi; ustidan yozish tasdiq talab qiladi. |
| 13| Rehearsal instructions: Mahalliy Docker Postgres sinovi | **NOT-RUN** | Docker CLI o'rnatilgan, biroq Docker Desktop daemon/server ishga tushirilmagan. Qo'llanma keltirildi. |

---

## 3. Topilmalar Tafsilotlari (Findings by Severity)

### OF-001: `reset_media.py` media jadvallarini tozalamaydi, lekin `go_live.ps1` --check-zero-media talab qiladi
- **Severity**: CRITICAL
- **Status**: FIXED (`27fa10a`)
- **File:Line**: [go_live.ps1](file:///c:/Users/%D0%90%D0%B4%D0%BC%D0%B8%D0%BD%D0%B8%D1%81%D1%82%D1%80%D0%B0%D1%82%D0%BE%D1%80/Desktop/kino%20bot%20project/kinochi%20project/ops/go_live.ps1) vs [reset_media.py](file:///c:/Users/%D0%90%D0%B4%D0%BC%D0%B8%D0%BD%D0%B8%D1%81%D1%82%D1%80%D0%B0%D1%82%D0%BE%D1%80/Desktop/kino%20bot%20project/kinochi%20project/scripts/reset_media.py)
- **Resolution**: `scripts/reset_media.py` ga `--wipe-media` bayrog'i qo'shildi va `ops/go_live.ps1` chaqiruviga kiritildi. Qat'iy test `backend/tests/test_reset_media_s8.py` orqali tasdiqlandi.

---

### OF-002: `alembic check` farq aniqlaganda skript xatolik bilan to'xtamaydi
- **Severity**: HIGH
- **Status**: FIXED (`00f06b2`)
- **File:Line**: [go_live.ps1](file:///c:/Users/%D0%90%D0%B4%D0%BC%D0%B8%D0%BD%D0%B8%D1%81%D1%82%D1%80%D0%B0%D1%82%D0%BE%D1%80/Desktop/kino%20bot%20project/kinochi%20project/ops/go_live.ps1)
- **Resolution**: `ops/go_live.ps1` ichida `alembic check` natijasida `$LASTEXITCODE -ne 0` bo'lsa `Log-Error` qayd etilib, `exit 1` bilan to'xtatish kiritildi. Test `backend/tests/test_ops_scripts.py::test_go_live_halts_on_alembic_check_failure` orqali tasdiqlandi.

---

### OF-003: Zaxira fayli `pg_restore --list` orqali to'liqlikka tekshirilmaydi
- **Severity**: MEDIUM
- **Status**: FIXED (`4590ed6`)
- **File:Line**: [go_live.ps1](file:///c:/Users/%D0%90%D0%B4%D0%BC%D0%B8%D0%BD%D0%B8%D1%81%D1%82%D1%80%D0%B0%D1%82%D0%BE%D1%80/Desktop/kino%20bot%20project/kinochi%20project/ops/go_live.ps1)
- **Resolution**: `ops/go_live.ps1` Phase B zaxira tekshiruviga `pg_restore --list "$BackupDumpFile"` buyrug'i qo'shildi va `$LASTEXITCODE -ne 0` bo'lsa xato berishi ta'minlandi. Test `backend/tests/test_ops_scripts.py::test_go_live_verifies_backup_with_pg_restore` orqali tasdiqlandi.

---

### OF-004: `-SkipBackup` parametri berilganda mavjud zaxira faylini ko'rsatib bo'lmaydi
- **Severity**: MEDIUM
- **Status**: FIXED (`4f6934b`)
- **File:Line**: [go_live.ps1](file:///c:/Users/%D0%90%D0%B4%D0%BC%D0%B8%D0%BD%D0%B8%D1%81%D1%82%D1%80%D0%B0%D1%82%D0%BE%D1%80/Desktop/kino%20bot%20project/kinochi%20project/ops/go_live.ps1)
- **Resolution**: `ops/go_live.ps1` ga `-BackupFile <string>` parametri qo'shildi. `-SkipBackup` ishlatilganda `-BackupFile` orqali oldindan olingan zaxira fayli uzatilsa, Reset fazasi xavfsiz davom etadi. Test `backend/tests/test_ops_scripts.py::test_go_live_accepts_backup_file_with_skip_backup` orqali tasdiqlandi.

---

### OF-005: Redis kesh tozalash xatoligi yutib yuboriladi
- **Severity**: LOW
- **Status**: FIXED (`894d8db`)
- **File:Line**: [go_live.ps1](file:///c:/Users/%D0%90%D0%B4%D0%BC%D0%B8%D0%BD%D0%B8%D1%81%D1%82%D1%80%D0%B0%D1%82%D0%BE%D1%80/Desktop/kino%20bot%20project/kinochi%20project/ops/go_live.ps1)
- **Resolution**: `ops/go_live.ps1` ga `-IgnoreRedisError` kaliti qo'shildi. Agar Redis kesh tozalash muvaffaqiyatsiz bo'lsa va bu kalit berilmagan bo'lsa, skript `exit 1` bilan to'xtaydi. Test `backend/tests/test_ops_scripts.py::test_go_live_halts_on_redis_flush_failure` orqali tasdiqlandi.

---

### OF-006: Jarayon holatini saqlovchi va xatolikdan keyin davom ettiruvchi (Resume) mexanizm yo'q
- **Severity**: LOW
- **Status**: FIXED (`e170434`)
- **File:Line**: [go_live.ps1](file:///c:/Users/%D0%90%D0%B4%D0%BC%D0%B8%D0%BD%D0%B8%D1%81%D1%82%D1%80%D0%B0%D1%82%D0%BE%D1%80/Desktop/kino%20bot%20project/kinochi%20project/ops/go_live.ps1)
- **Resolution**: `ops/go_live.ps1` ga `-StartPhase` parametri qo'shildi (`PREFLIGHT`, `BACKUP`, `MIGRATE`, `DEPLOY_GATE`, `RESET`). Bu orqali oldingi fazalar muvaffaqiyatli o'tgan bo'lsa, keyingi fazadan xavfsiz va idempotent davom ettirish mumkin. Test `backend/tests/test_ops_scripts.py::test_go_live_supports_start_phase_parameter` orqali tasdiqlandi.

---

## 4. Mahalliy Docker Sinovi Bo'yicha Ko'rsatmalar (Rehearsal Instructions)

> [!IMPORTANT]
> **Audit Holati: NOT-RUN**  
> Tizimda Docker CLI mavjud, ammo Docker Desktop serveri (`dockerDesktopLinuxEngine`) ishga tushirilmagan. Qoidaga ko'ra, real ishga tushirilmasdan turib holat OK deb belgilanmaydi.

Operator o'z kompyuterida quyidagi ketma-ketlik orqali xavfsiz repetitsiya (rehearsal) o'tkazishi mumkin:

```powershell
# 1. Docker Desktop dasturini ishga tushiring va xizmat yoqilganini tekshiring:
docker info

# 2. Alohida portda (5433) sinov PostgreSQL 16 konteynerini ko'taring:
docker run -d --name kinochi_rehearsal_pg -p 5433:5432 -e POSTGRES_PASSWORD=test_secret -e POSTGRES_DB=kinochi_test postgres:16

# 3. Sinov ma'lumotlar bazasi URL muhit o'zgaruvchisini o'rnating:
$env:TEST_DATABASE_URL = "postgresql+asyncpg://postgres:test_secret@localhost:5433/kinochi_test"

# 4. go_live.ps1 ni faqat sinov bazasiga yo'naltirgan holda sinab ko'ring:
.\ops\go_live.ps1 -UrlEnvVar TEST_DATABASE_URL

# 5. Sinov tugagach, konteynerni to'xtating va o'chiring:
docker stop kinochi_rehearsal_pg
docker rm kinochi_rehearsal_pg
```
