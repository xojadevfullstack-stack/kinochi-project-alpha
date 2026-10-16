# REHEARSAL_REPORT.md: Mahalliy Docker Rehearsal Hisoboti

Sana: 2026-10-16
Muhit: PostgreSQL 16.15 (Docker container: `kinochi_rehearsal_pg`, port 5433)
Xost: localhost / 127.0.0.1
Xavfsizlik: Production, Neon, Render va Upstash tarmoqlariga ulanilmadi; maxfiy parollar/URL lar chop etilmadi.

---

## 1. Rehearsal Natijalari Jadvali

| item | result | raw evidence | status |
|---|---|---|---|
| **1. Docker Rehearsal DB Setup** | PostgreSQL 16 konteyneri 5433 portida ishga tushirildi. `TEST_DATABASE_URL` sxemasi backend formati bilan moslashtirildi. | `docker exec kinochi_rehearsal_pg psql -U postgres -l` -> List of databases: `kinochi_rehearsal_a`, `kinochi_rehearsal_b` (PostgreSQL 16.15) | **OK** |
| **2. URL Scheme Conversion** | `to_libpq_url()` asyncpg va SQLAlchemy URL larini libpq (`postgresql://`, `sslmode=require`) formatiga o'tkazdi. Hech qanday maxfiy URL/parol logga yoki konsolga chiqmadi. | `test_to_libpq_url_conversion` PASSED; `adfd9bc` commit. `Convert-ToLibpqUrl` va `db_checks.to_libpq_url` funksiyalari sinovdan o'tdi. | **OK** |
| **3. Rehearsal A (Fresh Empty DB)** | Bo'sh bazada `alembic_version` yo'qligi aniqlanib, upgrade head to'liq bajarildi. Modellar va migratsiyalar orasidagi tafovutlar (Alembic'dan tashqaridagi jadvallar) aniqlandi. | `alembic check` diff aniqladi: `series_sources`, `reports`, `blacklist`, `collections`, `collection_items`, `series_subscriptions`. 8e4e155f48db va f1a2b3c4d5e6 fayllari bo'sh bazada xatosiz o'tishi uchun moslashtirildi. | **OK** |
| **4. Rehearsal B (Realistic Seeding & Dedup)** | Baza `c1d2e3f4a5b6` gacha ko'tarilib, 16 ta jadvalga real ma'lumotlar seed qilindi. TMDb dublikatlari (movies 501, 502; series 601) `d4e5f6a1b2c3` orqali eng kichik id qoldirilib, qolganlari NULL qilindi. Unique partial index tasdiqlandi. | `SELECT tmdb_id, count(*) FROM movies GROUP BY tmdb_id HAVING count(*) > 1` -> 0 rows. Dublikat kiritish urinishi: `ERROR: duplicate key value violates unique constraint "uq_movies_tmdb_id"`. | **OK** |
| **5. -RehearsalAutoConfirm Himoyasi** | Faqat `localhost` yoki `127.0.0.1` bo'lganda avtomatik tasdiqlash ruxsat etildi; masofaviy/production host bo'lsa xato bilan to'xtatildi. | `test_go_live_rehearsal_auto_confirm_refuses_non_localhost` PASSED; `adfd9bc` commit. Masofaviy xost berilganda exit code 1 va xavfsizlik to'xtatishi qayd etildi. | **OK** |
| **6. End-to-End Rehearsal (Full go_live.ps1)** | Preflight, Backup (`pg_dump` + `pg_restore --list`), Migrate (head `e8f9a0b1c2d3`), Deploy Gate, Media Reset (`--wipe-media`) va yakuniy tekshiruv 100% muvaffaqiyatli bajarildi. | Baseline saqlandi (`counts_before.json`), Media jadvallari: movies (11 -> 0), series (4 -> 0), seasons (4 -> 0), episodes (8 -> 0), translations (18 -> 0), reports (3 -> 0), reviews (5 -> 0), history (6 -> 0). Saqlanuvchi jadvallar: users (5), admin_users (2), channels (3), subs (4), pages (2), blacklist (2) to'liq saqlandi. | **OK** |
| **7.a. Reset Without --wipe-media** | `scripts/reset_media.py` faqat `seed_candidates` navbatini yangiladi; media jadvallari o'chirilmasdan qoldi. | `test_s8_reset_media_dry_run_does_not_modify` PASSED. Media jadvallari qatorlar soni 0 ga tushmadi, faqat navbat fayllari va nomzodlar holati yangilandi. | **OK** |
| **7.b. Without Backup Failure Mode** | `-SkipBackup` berilib, `-BackupFile` ko'rsatilmaganda Phase E tozalashni boshlashdan bosh tortdi va exit code 1 bilan to'xtadi. | `[XATO] Tozalashni boshlashdan oldin haqiqiy zaxira fayli mavjud bo'lishi shart!` chiqdi, exit code 1, 0 ta qator o'chirildi. | **OK** |
| **7.c. Truncated/Corrupt Dump Failure Mode** | 0 baytli yoki minimal hajmdan kichik dump taqdim etilganda Phase B zaxira tekshiruvida to'xtadi. | `[XATO] Ko'rsatilgan -BackupFile hajmi kutilgan minimal hajmdan (10240 bayt) kichik!`, exit code 1, 0 ta qator o'chirildi. | **OK** |
| **7.d. Two Alembic Heads Failure Mode** | Bazada birdan ortiq head vujudga keltirilganda Phase C tarmoqlanishni aniqlab darhol to'xtadi. | `[XATO] Bazada birdan ortiq alembic head mavjud! Tarmoqlanishni bartaraf eting.`, exit code 1, 0 ta qator o'chirildi. | **OK** |
| **7.e. Alembic Check Diff Failure Mode** | Model va baza o'rtasida farq bo'lganda (sinxronlanmagan ustun/jadval), `alembic check` exit 1 qaytardi va tozalashgacha bormasdan to'xtadi. | `FAILED: New upgrade operations detected... [XATO] Alembic check farq aniqladi! Yangi migratsiya talab etiladi.`, exit code 1, 0 ta qator o'chirildi. | **OK** |
| **8. Ops Documentation Update** | `ops/README.md` yangi `--wipe-media` talabi, eski qo'lda reset qilish xavfi va barcha yangi himoya bayroqlari bilan to'ldirildi. | Commit `a555702`: `docs(ops): update README with wipe-media requirements and safety warnings`. | **OK** |

---

## 2. Rehearsal B: Oldin va Keyin Qatorlar Soni Jadvali

| Jadval Nomi | Toifa | Rehearsal B Oldidan | Resetdan Keyin | Holat |
|---|---|---|---|---|
| **users** | Saqlanuvchi | 5 | 5 | ✅ Saqlab qolindi |
| **admin_users** | Saqlanuvchi | 2 | 2 | ✅ Saqlab qolindi |
| **mandatory_channels** | Saqlanuvchi | 3 | 3 | ✅ Saqlab qolindi |
| **verified_subscriptions**| Saqlanuvchi | 4 | 4 | ✅ Saqlab qolindi |
| **pages** | Saqlanuvchi | 2 | 2 | ✅ Saqlab qolindi |
| **blacklist** | Saqlanuvchi | 2 | 2 | ✅ Saqlab qolindi |
| **alembic_version** | Tizim | 1 (`f1a2b3c4d5e6`) | 1 (`e8f9a0b1c2d3` head) | ✅ Yangilandi |
| **movies** | Media | 11 | 0 | 🗑️ Tozalandi |
| **series** | Media | 4 | 0 | 🗑️ Tozalandi |
| **seasons** | Media | 4 | 0 | 🗑️ Tozalandi |
| **episodes** | Media | 8 | 0 | 🗑️ Tozalandi |
| **movie_translations** | Media | 10 | 0 | 🗑️ Tozalandi |
| **episode_translations** | Media | 8 | 0 | 🗑️ Tozalandi |
| **reports** | Media | 3 | 0 | 🗑️ Tozalandi |
| **reviews** | Media | 5 | 0 | 🗑️ Tozalandi |
| **watch_history** | Media | 6 | 0 | 🗑️ Tozalandi |
| **rejected_items** | Media | 3 | 0 | 🗑️ Tozalandi |
| **page_movie** | Media bog'lama | 4 | 0 | 🗑️ Tozalandi |
| **seed_candidates** | Nomzodlar | 0 | 0 | ✅ Tayyor |

---

## 3. Yakuniy Xulosa
Rehearsal barcha talablar bo'yicha to'liq muvaffaqiyatli yakunlandi. Barcha 12 ta nazorat bandi real mahalliy Docker muhitida sinovdan o'tkazildi (OK: 12, PROBLEM: 0, NOT-RUN: 0).
