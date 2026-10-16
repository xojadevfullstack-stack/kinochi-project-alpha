# OPS_PROGRESS.md: Production Go-Live va Pilot Operatsion Protoko'li

Ushbu hujjat Kinochi tizimini Production muhitiga xavfsiz o'tkazish (Go-Live) va Pilot urug'lantirish (TMDb Seed Ingestor Pilot) operatsion skriptlarini bosqichma-bosqich ishlab chiqish protokoli hisoblanadi.

## Checklist

- [x] **OP1**: `.gitignore` ga `*.dump`, `ops/logs/`, `.env.local`, `backups/` qoidalarini qo'shish. (Commit: `e2a20e5`)
- [x] **OP2**: `ops/db_checks.py` va `ops/redis_flush_cache.py` yordamchi skriptlarini yaratish (faqat DB xosti va hisoblarni ko'rsatish, parollarni chiqarmaslik, `cache:*` ni tozalash). (Commit: `80f9028`)
- [x] **OP3**: `ops/new_telegram_session.py` (interaktiv Telethon StringSession generatori, `.env.local` ga xavfsiz yozish, unit testlar bilan qamrab olish). (Commit: `15c8d2b`)
- [x] **OP4**: `ops/go_live.ps1` (Preflight, Backup, Migrate, Deploy Gate, Reset, Final fazalari, `-DryRun`, `-UrlEnvVar`, ASCII xabarlar, xavfsiz log). (Commit: `fa01e76`)
- [x] **OP5**: `ops/pilot.ps1` (`SEED_INCLUDE_SERIES` tekshiruvi, build-seeds, stats, search limit 20, manual tekshirish jadvali, dry-run va tasdiqli enqueue). (Commit: `0660712`)
- [x] **OP6**: `ops/README.md` (O'zbek tilida to'liq qo'llanma, qo'lda bajariladigan amallar, parollarni almashtirish va 10 qatorlik troubleshooting jadvali). (Commit: `9565189`)
- [x] **OP7**: Avtomatlashtirilgan testlar: PowerShell sintaksisi (`[scriptblock]::Create`), `-DryRun` tekshiruvi, Python unit testlari (`backend/tests/test_ops_scripts.py`), compileall va pytest. (Commit: `7ac10e1`)

## Decisions
- Barcha PowerShell xabarlari ASCII formatda (emojisiz) yoziladi, chunki Windows cp1251/cp866 konsollarida Unicode belgilar crash keltirib chiqarishi mumkin.
- Hech qanday ma'lumotlar bazasi paroli yoki to'liq ulanish URL satri konsolga va log fayllarga chiqarilmaydi, faqat DB xosti (`Database Host: ...`) ko'rsatiladi.
- Barcha yo'llar qo'shtirnoqqa olinadi va `$PSScriptRoot` orqali dinamik hisoblanadi, chunki loyiha yo'lida probel va kirill belgilari mavjud.
- Skriptlar faqat yoziladi, agent hech qachon production bazasiga ulanmaydi va haqiqiy migratsiya yoki tozalashni avtomatik ishga tushirmaydi.
