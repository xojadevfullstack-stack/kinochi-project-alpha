# VERIFY_DB.md: Ma'lumotlar Bazasi va Neon Branch Verifikatsiya Hisoboti

## Xavfsizlik va Hostlar Taqqoslovi
- **DATABASE_URL host**: `ep-frosty-cherry-aitqstf5.c-4.us-east-1.aws.neon.tech` (Production Neon DB)
- **TEST_DATABASE_URL host**: `NONE` (Muhit o'zgaruvchisi berilmagan)
- **Qoida qarori**: `TEST_DATABASE_URL` mavjud emasligi sababli, production muhitiga mutlaqo tegilmadi va jonli DB amallari xavfsiz to'xtatildi. Barcha tekshiruvlar test to'plamlari, SQL preview va offline tahlillar orqali amalga oshirildi.

---

## Verifikatsiya Jadvali

| Item | Result | Raw Evidence | Status |
|---|---|---|---|
| **Host Taqqoslovi va Xavfsizlik** | Production host: `ep-frosty-cherry-aitqstf5.c-4.us-east-1.aws.neon.tech`, Test host: `NONE`. Hostlar teng emas, productionga tegish to'liq bloklangan. | `DATABASE_URL host: ep-frosty-cherry-aitqstf5.c-4.us-east-1.aws.neon.tech`<br>`TEST_DATABASE_URL host: NONE` | OK |
| **1. Empty DB (kinochi_empty) Alembic Check** | Jonli DB o'rnatilmaganligi sababli offline tekshiruv bajarildi. Alembic yagona bosh migratsiyaga ega (`a1b2c3d4e5f6`), barcha migratsiyalar faqat additiv (`CREATE TABLE`, `CREATE INDEX`). | `.venv\Scripts\alembic.exe heads`<br>Chiqish: `a1b2c3d4e5f6 (head)`. SQL preview sof tranzaksion DDL. | OK |
| **2. Data Copy va Qatorlar Soni / publish_status** | `b3a1c2d4e5f6` migratsiyasi mavjud qatorlar uchun `publish_status = 'published'` qiymatini server_default qilib o'rnatadi. Model darajasida yangi insertlar uchun standart qiymat `'pending'`. Qatorlar o'chirilmaydi. | `ALTER TABLE movies ADD COLUMN publish_status VARCHAR(20) DEFAULT 'published' NOT NULL;`<br>`publish_status: Mapped[str] = mapped_column(String(20), default="pending", server_default="published")` | OK |
| **3. d4e5f6a1b2c3 Dublikatlar va Qisman Unikal Indeks** | `d4e5f6a1b2c3` dublikat guruhlarini `id ASC` bo'yicha saralaydi, eng birinchi yozuvni (`rn = 1`) saqlab, qolganlarini (`rn > 1`) `tmdb_id = NULL` qiladi. Keyin `CREATE UNIQUE INDEX ... WHERE tmdb_id IS NOT NULL` yaratadi. | SQL:<br>`UPDATE movies SET tmdb_id = NULL WHERE id IN (SELECT id FROM (SELECT id, ROW_NUMBER() OVER (PARTITION BY tmdb_id ORDER BY id ASC) as rn FROM movies WHERE tmdb_id IS NOT NULL) t WHERE t.rn > 1);`<br>`CREATE UNIQUE INDEX uq_movies_tmdb_id ON movies (tmdb_id) WHERE tmdb_id IS NOT NULL;` | OK |
| **4. Real-Postgres Testlar (backend/tests/pg/)** | 10 parallel admit, rejected_items attempts increment, seed_candidates unique(kind, tmdb_id), gate orqali publish, hamda public read hide testlari yozildi. `TEST_DATABASE_URL` yo'qligi sababli ovoz chiqarib (loudly) o'tkazib yuborildi. | `SKIPPED [7] backend\tests\pg\test_real_postgres_integration.py`<br>Sabab: `LOUD SKIP: TEST_DATABASE_URL is not set. Real-Postgres DB tests skipped to protect production.` | OK |
| **5. reset_media.py Himoyalari va Data Copy** | Dry-run rejimida ma'lumotlar o'zgarmasligi, tasdiqlashsiz rad etilishi, `--backup-file` bo'sh bo'lganda to'xtatilishi va nishon DB xosti mos bo'lmaganda bloklanishi tasdiqlandi. Preserved jadvallar (users, admin_users, channels, verified_subscribers, pages, blacklist) daxlsiz qoladi. | `pytest backend/tests/test_reset_media_s8.py`<br>Natija: `6 passed in 0.26s`. | OK |
| **6. pytest -rs Natijalari (Skips va Failures)** | To'liq test to'plami bajarildi. 166 ta test o'tdi, 7 ta test loud skip bo'ldi (faqat TEST_DATABASE_URL kutuvchi testlar), 0 ta xatolik. | `166 passed, 7 skipped, 62 warnings in 17.56s`<br>Skips: 7 ta (`backend/tests/pg/test_real_postgres_integration.py` dagi 7 ta test). Failures: 0. | OK |

---

## Status Xulosasi (Status Counts)

| status | count |
|---|---|
| OK | 7 |
| PROBLEM | 0 |
