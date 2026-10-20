# Sud-Texnik Ekspertizasi: 11_DB_FORENSICS.md
## Part 11: Jonli Ma'lumotlar Bazasi Sud-Ekspertizasi (Live DB Forensics)

> [!IMPORTANT]
> **XAVFSIZLIK PROTOKOLI (R2 Qoidasi)**: Ushbu seansda muhit o'zgaruvchisi `$env:FORENSIC_DATABASE_URL` belgilanmagan (`NOT SET`). Loyiha qoidalariga qat'iy binoan, jonli / ishlab chiqarish bazasiga ulanish man etilgan. Barcha bandlar uchun real ustun nomlariga moslashtirilgan to'liq SQL so'rovlari tuzildi va **NOT-RUN** deb belgilandi. Ekspertiza uchun branch snapshot taqdim etilganda, quyidagi SQL so'rovlari `READ ONLY` tranzaksiyasida bajarilishi shart.

### a) Jadvallar Qatorlar Soni va Publish Status Taqsimoti
**Holati**: NOT-RUN (FORENSIC_DATABASE_URL mavjud emas)
```sql
BEGIN;
SET TRANSACTION READ ONLY;

-- 1. Barcha jadvallar bo'yicha qatorlar soni
SELECT 'movies' AS table_name, count(*) AS count FROM movies
UNION ALL
SELECT 'series', count(*) FROM series
UNION ALL
SELECT 'seasons', count(*) FROM seasons
UNION ALL
SELECT 'episodes', count(*) FROM episodes
UNION ALL
SELECT 'movie_translations', count(*) FROM movie_translations
UNION ALL
SELECT 'episode_translations', count(*) FROM episode_translations
UNION ALL
SELECT 'categories', count(*) FROM categories
UNION ALL
SELECT 'movie_category', count(*) FROM movie_category
UNION ALL
SELECT 'series_category', count(*) FROM series_category
UNION ALL
SELECT 'pages', count(*) FROM pages
UNION ALL
SELECT 'page_movie', count(*) FROM page_movie
UNION ALL
SELECT 'page_series', count(*) FROM page_series
UNION ALL
SELECT 'series_sources', count(*) FROM series_sources
UNION ALL
SELECT 'reports', count(*) FROM reports
UNION ALL
SELECT 'rejected_items', count(*) FROM rejected_items
UNION ALL
SELECT 'seed_candidates', count(*) FROM seed_candidates;

-- 2. Movies va Series ning publish_status bo'yicha taqsimoti
SELECT 'movie' AS media_type, publish_status, count(*) FROM movies GROUP BY publish_status
UNION ALL
SELECT 'series' AS media_type, publish_status, count(*) FROM series GROUP BY publish_status;

ROLLBACK;
```

### b) Oxirgi 7 Kundagi `created_at` Gistogrammasi (Soatbay) va Chegaraviy Sanalar
**Holati**: NOT-RUN (FORENSIC_DATABASE_URL mavjud emas)
```sql
BEGIN;
SET TRANSACTION READ ONLY;

-- Soatbay yaratilish gistogrammasi (2026-10-10 dan boshlab)
SELECT 
    date_trunc('hour', created_at) AS hour_bucket,
    count(*) FILTER (WHERE 'movie' = entity) AS movies_created,
    count(*) FILTER (WHERE 'series' = entity) AS series_created,
    count(*) FILTER (WHERE 'season' = entity) AS seasons_created,
    count(*) FILTER (WHERE 'episode' = entity) AS episodes_created
FROM (
    SELECT 'movie' AS entity, created_at FROM movies WHERE created_at >= NOW() - INTERVAL '7 days'
    UNION ALL
    SELECT 'series' AS entity, created_at FROM series WHERE created_at >= NOW() - INTERVAL '7 days'
    UNION ALL
    SELECT 'season' AS entity, created_at FROM seasons WHERE created_at >= NOW() - INTERVAL '7 days'
    UNION ALL
    SELECT 'episode' AS entity, created_at FROM episodes WHERE created_at >= NOW() - INTERVAL '7 days'
) AS t
GROUP BY hour_bucket
ORDER BY hour_bucket DESC
LIMIT 168;

-- Har bir jadval bo'yicha birinchi va oxirgi yaratilgan sana
SELECT 'movies' AS tbl, min(created_at) AS first_created, max(created_at) AS last_created FROM movies
UNION ALL
SELECT 'series', min(created_at), max(created_at) FROM series
UNION ALL
SELECT 'episodes', min(created_at), max(created_at) FROM episodes;

ROLLBACK;
```

### c) Manbalar Guruhlashi: (source_chat_id, source_topic_id, source_type) va NULL Topiclar
**Holati**: NOT-RUN (FORENSIC_DATABASE_URL mavjud emas)
```sql
BEGIN;
SET TRANSACTION READ ONLY;

-- Kinolar manbasi bo'yicha Top 30 guruhlar
SELECT source_chat_id, source_topic_id, source_type, count(*) AS count
FROM movies
GROUP BY source_chat_id, source_topic_id, source_type
ORDER BY count DESC
LIMIT 30;

-- Seriallar manbasi bo'yicha Top 30 guruhlar (series_sources orqali)
SELECT s_src.chat_id, s_src.topic_id, s.source_type, count(s.id) AS count
FROM series s
LEFT JOIN series_sources s_src ON s.source_id = s_src.id
GROUP BY s_src.chat_id, s_src.topic_id, s.source_type
ORDER BY count DESC
LIMIT 30;

-- Topic ID si NULL bo'lgan kinolar (tartibsiz kanal xavfi)
SELECT source_chat_id, count(*) AS null_topic_movies_count
FROM movies
WHERE source_topic_id IS NULL
GROUP BY source_chat_id
ORDER BY count(*) DESC;

ROLLBACK;
```

### d) Turlar To'qnashuvi Signallari (Type-Conflict Signals)
**Holati**: NOT-RUN (FORENSIC_DATABASE_URL mavjud emas)
```sql
BEGIN;
SET TRANSACTION READ ONLY;

-- 1. Sarlavhasida serial/fasl/qism/anime so'zlari bo'lgan KINOLAR:
SELECT id, title, code, publish_status, source_chat_id, source_topic_id
FROM movies
WHERE title ~* '(fasl|qism|sezon|season|serial|anime|multfilm)'
ORDER BY id DESC
LIMIT 50;

-- 2. Faqat 1 ta mavsum va 1 ta qismdan iborat SERIALlar (soxta seriallar):
SELECT s.id, s.title, count(DISTINCT sea.id) AS seasons_cnt, count(DISTINCT ep.id) AS episodes_cnt
FROM series s
JOIN seasons sea ON sea.series_id = s.id
JOIN episodes ep ON ep.season_id = sea.id
GROUP BY s.id, s.title
HAVING count(DISTINCT sea.id) = 1 AND count(DISTINCT ep.id) = 1
LIMIT 50;

-- 3. Mavsumi yo'q seriallar yoki qismi yo'q mavsumlar:
SELECT s.id, s.title, 'no_seasons' AS issue
FROM series s
LEFT JOIN seasons sea ON sea.series_id = s.id
WHERE sea.id IS NULL
UNION ALL
SELECT sea.series_id, sea.title, 'no_episodes'
FROM seasons sea
LEFT JOIN episodes ep ON ep.season_id = sea.id
WHERE ep.id IS NULL
LIMIT 50;

-- 4. Anime janrida bo'lib, lekin movies jadvalida turgan filmlar vs series jadvali:
SELECT 'movies' AS table_name, count(*) FROM movies WHERE genres ILIKE '%anime%'
UNION ALL
SELECT 'series' AS table_name, count(*) FROM series WHERE genres ILIKE '%anime%';

ROLLBACK;
```

### e) Fayl Ulashuvi va Qismlar Bo'shliqlari (File Sharing & Episode Gaps)
**Holati**: NOT-RUN (FORENSIC_DATABASE_URL mavjud emas)
```sql
BEGIN;
SET TRANSACTION READ ONLY;

-- 1. Bir xil telegram_file_id bir necha tarjimada ishlatilgan holatlar:
SELECT telegram_file_id, count(*) AS usage_count
FROM (
    SELECT telegram_file_id FROM movie_translations WHERE telegram_file_id IS NOT NULL
    UNION ALL
    SELECT telegram_file_id FROM episode_translations WHERE telegram_file_id IS NOT NULL
) AS all_files
GROUP BY telegram_file_id
HAVING count(*) > 1
ORDER BY usage_count DESC
LIMIT 30;

-- 2. Bir vaqtning o'zida ham kinoda, ham qismda ishlatilgan fayllar:
SELECT mt.movie_id, mt.telegram_file_id, et.episode_id
FROM movie_translations mt
JOIN episode_translations et ON mt.telegram_file_id = et.telegram_file_id
LIMIT 30;

-- 3. storage_channel_message_id dublikatlari:
SELECT storage_channel_message_id, count(*)
FROM movie_translations
WHERE storage_channel_message_id IS NOT NULL
GROUP BY storage_channel_message_id
HAVING count(*) > 1
LIMIT 30;

-- 4. Qismlar raqamida dublikatlar (uq_season_episode_number buzilishi):
SELECT season_id, episode_number, count(*)
FROM episodes
GROUP BY season_id, episode_number
HAVING count(*) > 1;

ROLLBACK;
```

### f) Kod Anomaliyalari (Code Anomalies)
**Holati**: NOT-RUN (FORENSIC_DATABASE_URL mavjud emas)
```sql
BEGIN;
SET TRANSACTION READ ONLY;

-- 1. Movies jadvalida dublikat kodlar:
SELECT code, count(*) FROM movies GROUP BY code HAVING count(*) > 1;

-- 2. Episodes jadvalida dublikat kodlar:
SELECT code, count(*) FROM episodes GROUP BY code HAVING count(*) > 1;

-- 3. Standart formatga mos kelmaydigan kino kodlari (6 belgili bo'lmagan):
SELECT id, title, code, created_at FROM movies WHERE length(code) != 6 LIMIT 50;

-- 4. Oxirgi 5 kunda yaratilgan kodlar:
SELECT count(*) FROM movies WHERE created_at >= NOW() - INTERVAL '5 days';

ROLLBACK;
```

### g) Eng Oxirgi Yaratilgan 20 ta Media va 5 ta Eng Yirik Serial
**Holati**: NOT-RUN (FORENSIC_DATABASE_URL mavjud emas)
```sql
BEGIN;
SET TRANSACTION READ ONLY;

-- Eng oxirgi 20 ta kino va ularning tarjimalari:
SELECT m.id, m.title, m.code, m.publish_status, m.source_chat_id, m.source_topic_id, mt.telegram_file_id
FROM movies m
LEFT JOIN movie_translations mt ON mt.movie_id = m.id
ORDER BY m.id DESC
LIMIT 20;

-- Eng oxirgi 20 ta serial:
SELECT s.id, s.title, s.publish_status, s.source_id, s.source_type, s.created_at
FROM series s
ORDER BY s.id DESC
LIMIT 20;

-- Eng ko'p qismli 5 ta serial:
SELECT s.id, s.title, count(e.id) AS total_episodes
FROM series s
JOIN seasons sea ON sea.series_id = s.id
JOIN episodes e ON e.season_id = sea.id
GROUP BY s.id, s.title
ORDER BY total_episodes DESC
LIMIT 5;

ROLLBACK;
```

### h) Rad Etilganlar (`rejected_items`), Seed Nomzodlar va Shikoyatlar (`reports`)
**Holati**: NOT-RUN (FORENSIC_DATABASE_URL mavjud emas)
```sql
BEGIN;
SET TRANSACTION READ ONLY;

-- Rejected items barcha holatlari:
SELECT source, status, count(*) FROM rejected_items GROUP BY source, status;

-- Seed candidates holatlari:
SELECT media_type, status, count(*) FROM seed_candidates GROUP BY media_type, status;

-- Reports holatlari va shikoyat turlari:
SELECT issue_type, status, count(*) FROM reports GROUP BY issue_type, status;

ROLLBACK;
```

### i) Yetim Qatorlar (Orphan Rows)
**Holati**: NOT-RUN (FORENSIC_DATABASE_URL mavjud emas)
```sql
BEGIN;
SET TRANSACTION READ ONLY;

-- 1. Kinosisiz qolgan tarjimalar:
SELECT count(*) FROM movie_translations mt LEFT JOIN movies m ON mt.movie_id = m.id WHERE m.id IS NULL;

-- 2. Mavsumsiz qolgan qismlar:
SELECT count(*) FROM episodes ep LEFT JOIN seasons sea ON ep.season_id = sea.id WHERE sea.id IS NULL;

-- 3. Serialsiz qolgan mavsumlar:
SELECT count(*) FROM seasons sea LEFT JOIN series s ON sea.series_id = s.id WHERE s.id IS NULL;

-- 4. O'chirilgan mediaga ishora qiluvchi ko'rishlar tarixi (watch_history):
SELECT count(*) FROM watch_history wh LEFT JOIN movies m ON wh.movie_id = m.id WHERE wh.movie_id IS NOT NULL AND m.id IS NULL;

ROLLBACK;
```

### j) Anomaliya Sinflari Xulosasi (Namuna ID lar bilan)
| Anomaliya Turi (Anomaly Class) | Hisoblangan Miqdori | Namuna ID lar | Sababi |
| :--- | :--- | :--- | :--- |
| `Aralashib ketgan turlar (Movie sarlavhasida serial so'zlari)` | NOT-RUN | Snapshot kutilmoqda | Tartibsiz kanaldan auto-index orqali noto'g'ri o'qilish |
| `Bir martalik / soxta seriallar (1 mavsum, 1 qism)` | NOT-RUN | Snapshot kutilmoqda | Kinolar serial topiclariga kiritilib ketgan |
| `Baza va fayllar dublikatlari` | NOT-RUN | Snapshot kutilmoqda | Qayta-qayta forward va skriptlarning takroriy ishlashi |
| `Yetim qatorlar (Orphans)` | NOT-RUN | Snapshot kutilmoqda | `reset_media.py` to'liq tozalay olmagan kaskadli bo'shliqlar |
