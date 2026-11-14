# KINOCHI — PRODUCTION BACKUP & DISASTER RECOVERY RUNBOOK

**Maqsad:** PostgreSQL ma'lumotlar bazasini xavfsiz zaxiralash (backup), zaxira butunligini tekshirish, toza serverga qayta tiklash (restore) va nosozlik paytida rollback qilishning qat'iy operatsion ko'rsatmasi.  
**Xavfsizlik qoidasi:** Ushbu buyruqlar avtomatlashtirilgan yoki tasdiqlangan vaqtda bajariladi. Haqiqiy ishlayotgan production bazasida destructive (o'chiruvchi) amallar bajarilmaydi.

---

## 1. BACKUP OLISH (ZAXIRALASH TARTIBI)

### 1.1. Standart Siqilgan Backup (Custom Format)
Production bazadan barcha jadvallar, ma'lumotlar va ketma-ketliklarni (sequences) siqilgan holatda olish:

```bash
# Format: YYYY-MM-DD_HHMMSS
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="kinochi_backup_${TIMESTAMP}.dump"

# pg_dump buyrug'i (Custom format, siqilgan)
PGPASSWORD="${DB_PASSWORD}" pg_dump \
  -h "${DB_HOST}" \
  -p "${DB_PORT:-5432}" \
  -U "${DB_USER}" \
  -d "${DB_NAME}" \
  -F c \
  -b \
  -v \
  -f "${BACKUP_FILE}"
```

### 1.2. Schema-Only (Faqat struktura) Backup
Migratsiyalar va sxemani alohida zaxiralash:
```bash
PGPASSWORD="${DB_PASSWORD}" pg_dump \
  -h "${DB_HOST}" \
  -p "${DB_PORT:-5432}" \
  -U "${DB_USER}" \
  -d "${DB_NAME}" \
  --schema-only \
  -f "kinochi_schema_${TIMESTAMP}.sql"
```

---

## 2. BACKUP FAYLINI TEKSHIRISH (INTEGRITY CHECK)

Zaxira faylini tiklashdan oldin uning butunligi va buzilmaganligini tekshirish majburiydir:

### 2.1. Hash Tekshiruvi (Checksum)
```bash
# SHA256 checksum yaratish
sha256sum "${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"

# Checksum tekshirish
sha256sum -c "${BACKUP_FILE}.sha256"
```

### 2.2. pg_restore Orqali Tarkibni Ko'rish (TOC Verification)
Fayl ochilishi va jadvallar ro'yxati to'liqligini tekshirish:
```bash
pg_restore -l "${BACKUP_FILE}" | head -n 30
```
Agar buyruq xatosiz (exit code 0) bilan chiqsa va `movies`, `episodes`, `alembic_version` kabi jadvallarni ko'rsatsa, backup sog'lom hisoblanadi.

---

## 3. TOZA BAZAGA RESTORE QILISH (TIKLASH TARTIBI)

> [!CAUTION]
> Hech qachon aktiv ishlab turgan production bazasini to'g'ridan-to'g'ri ustidan yozmang (`overwrite`). Har doim avval staging yoki vaqtinchalik toza bazada tiklab, so'ng DNS yoki ulanish manzilini o'zgartiring.

### 3.1. Yangi Toza Baza Yaratish
```bash
# Baza yaratish (agar mavjud bo'lmasa)
PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -U "${DB_USER}" -c "CREATE DATABASE kinochi_restored;"
```

### 3.2. Tiklash Buyrug'i
```bash
PGPASSWORD="${DB_PASSWORD}" pg_restore \
  -h "${DB_HOST}" \
  -p "${DB_PORT:-5432}" \
  -U "${DB_USER}" \
  -d "kinochi_restored" \
  --clean \
  --if-exists \
  --no-owner \
  --no-privileges \
  -v \
  "${BACKUP_FILE}"
```

---

## 4. RESTORE'DAN KEYINGI TEKSHIRUV (POST-RESTORE VERIFICATION)

Tiklash yakunlangach, quyidagi 3 ta tekshiruv majburiy o'tkaziladi:

### 4.1. Alembic Migratsiya Holati
Ma'lumotlar bazasidagi migratsiya versiyasi loyihadagi eng oxirgi `head` versiyaga mosligini tasdiqlash:
```bash
# Backend papkasida:
alembic current
```
*Kutilayotgan natija:* `b2c3d4e5f6a7 (head)`

### 4.2. Yozuvlar Soni va Butunligi (Sanity Count)
```sql
SELECT 
  (SELECT count(*) FROM movies) AS movies_count,
  (SELECT count(*) FROM episodes) AS episodes_count,
  (SELECT count(*) FROM collections) AS collections_count,
  (SELECT count(*) FROM users) AS users_count;
```

### 4.3. Foreign Key va Constraints Butunligi
```sql
-- Yetim qolgan (orphaned) qismlar yo'qligini tekshirish
SELECT count(*) FROM episodes WHERE movie_id NOT IN (SELECT id FROM movies);
-- Kutilgan natija: 0
```

---

## 5. XATOLIK YUZ BERGANDA ROLLBACK / RECOVERY TARTIBI

Agar yangi versiya chiqarilganda (release/deployment paytida) yoki migratsiyada halokatli nosozlik yuz bersa:

1. **Trafikni Vaqtincha To'xtatish (Maintenance Mode):**
   - Vercel va Botda "Profilaktika ishlari olib borilmoqda" rejimini yoqish.
2. **Faol Bog'lanishlarni Uzish (Disconnect Idle Clients):**
   ```sql
   SELECT pg_terminate_backend(pid) 
   FROM pg_stat_activity 
   WHERE datname = 'kinochi_db' AND pid <> pg_backend_pid();
   ```
3. **Oldingi Barqaror Snapshot/Backup'ni Tiklash:**
   - Yangi bo'sh bazaga avvalgi zaxira tiklanadi.
   - Backend `DATABASE_URL` parametriga tiklangan barqaror baza ulanishi beriladi.
4. **Backend Qayta Ishga Tushiriladi:**
   - `python run.py` yoki container qayta start beriladi.
5. **Health-Check Tekshiruvi:**
   - `curl -f http://localhost:8000/health` orqali `status: healthy` olinishi tasdiqlangach, maintenance mode o'chiriladi.

---
*Ushbu runbook Kinochi muhandislik guruhi uchun favqulodda vaziyatlar rasmiy qo'llanmasi hisoblanadi.*
