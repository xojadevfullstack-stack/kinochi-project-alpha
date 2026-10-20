# Sud-Texnik Ekspertizasi: 04_DATA_MODEL.md
## Part 4: Ma'lumotlar Modeli, Sxema Tahlili va Kontent Turlari (Content Types)

### 1. Baza Modellarining To'liq Sxemasi (SQLAlchemy Models)
Loyiha backendida (`backend/app/infrastructure/db/models/`) quyidagi asosiy jadvallar aniqlangan:

#### A. `movies` (Filmlar jadvali)
| Ustun (Column) | Turi | Nullable | Standart Qiymat | FK / Indeks / Cheklov |
| :--- | :--- | :--- | :--- | :--- |
| `id` | Integer | NOT NULL | Auto-increment PK | Primary Key, Index |
| `title` | String(255) | NOT NULL | - | Index |
| `original_title`| String(255) | NULL | - | - |
| `description` | Text | NULL | - | - |
| `imdb_rating` | Float | NULL | - | - |
| `tmdb_rating` | Float | NULL | - | - |
| `tmdb_id` | Integer | NULL | - | Index, Unique (`uq_movies_tmdb_id` partial WHERE tmdb_id IS NOT NULL) |
| `kinochi_rating`| Float | NULL | - | - |
| `kinochi_votes_count`| Integer | NOT NULL | 0 | - |
| `genres` | String(255) | NULL | - | - |
| `cast` | Text | NULL | - | - |
| `director` | String(255) | NULL | - | - |
| `release_year` | Integer | NULL | - | Index |
| `runtime` | Integer | NULL | - | - |
| `poster_url` | String(1024)| NULL | - | - |
| `trailer_url` | String(1024)| NULL | - | - |
| `code` | String(8) | NOT NULL | - | UNIQUE, Index |
| `publish_status`| String(50) | NOT NULL | 'pending' | Index ('draft', 'pending', 'published', 'hidden', 'rejected') |
| `is_18_plus` | Boolean | NOT NULL | False | - |
| `source_chat_id`| BigInteger | NULL | - | Index |
| `source_topic_id`| Integer | NULL | - | Index |
| `source_type` | String(50) | NULL | 'uzmovi' | - |
| `custom_source_name`| String(255)| NULL | - | - |
| `custom_source_logo`| String(1024)| NULL| - | - |
| `created_at` | DateTime | NOT NULL | now() | - |
| `updated_at` | DateTime | NOT NULL | now() | onupdate now() |

#### B. `series` (Seriallar jadvali)
| Ustun (Column) | Turi | Nullable | Standart Qiymat | FK / Indeks / Cheklov |
| :--- | :--- | :--- | :--- | :--- |
| `id` | Integer | NOT NULL | Auto-increment PK | Primary Key, Index |
| `title` | String(255) | NOT NULL | - | Index |
| `description` | Text | NULL | - | - |
| `poster_url` | String(1024)| NULL | - | - |
| `trailer_url` | String(1024)| NULL | - | - |
| `status` | String(50) | NOT NULL | 'ongoing' | 'ongoing', 'completed' |
| `publish_status`| String(50) | NOT NULL | 'pending' | Index ('draft', 'pending', 'published', 'hidden', 'rejected') |
| `is_18_plus` | Boolean | NOT NULL | False | - |
| `imdb_rating` | Float | NULL | - | - |
| `tmdb_id` | Integer | NULL | - | Index, Unique (`uq_series_tmdb_id` partial) |
| `kinochi_rating`| Float | NULL | - | - |
| `kinochi_votes_count`| Integer | NOT NULL | 0 | - |
| `release_year` | Integer | NULL | - | Index |
| `director` | String(255) | NULL | - | - |
| `cast` | Text | NULL | - | - |
| `source_id` | Integer | NULL | - | FK -> `series_sources.id` ON DELETE SET NULL, Index |
| `source_type` | String(50) | NULL | 'uzmovi' | - |
| `created_at` | DateTime | NOT NULL | now() | - |
| `updated_at` | DateTime | NOT NULL | now() | onupdate now() |

#### C. `seasons` va `episodes`
- `seasons`: `id` (PK), `series_id` (FK -> `series.id` ON DELETE CASCADE), `season_number` (Integer), `title`, `description`, `poster_url`, `episode_count`, `status`.
- `episodes`: `id` (PK), `season_id` (FK -> `seasons.id` ON DELETE CASCADE), `episode_number` (Integer), `code` (String(20), UNIQUE), `display_code` (String(50)), `title`, `duration` (Integer), `source_message_id` (BigInteger).
  - Cheklov: `UniqueConstraint('season_id', 'episode_number', name='uq_season_episode_number')`.

#### D. `movie_translations` va `episode_translations`
- `movie_translations`: `id` (PK), `movie_id` (FK -> `movies.id` ON DELETE CASCADE), `language` (String(255)), `telegram_file_id` (String(255)), `storage_channel_message_id` (Integer).
- `episode_translations`: `id` (PK), `episode_id` (FK -> `episodes.id` ON DELETE CASCADE), `language` (String(255)), `telegram_file_id` (String(255)), `storage_channel_message_id` (Integer).

#### E. Boshqa Jadvallar
- `categories` va m2m: `movie_category`, `series_category`.
- `pages` va m2m: `page_movie`, `page_series` (`page_id`, `movie_id`/`series_id` PK).
- `series_sources`: `id` (PK), `name`, `type` ('kanal'/'superguruh'), `chat_id` (BigInteger), `topic_id` (Integer).
- `rejected_items`: `id` (PK), `source`, `source_key`, `title`, `media_type`, `defects` (JSONB/Text), `status`, `attempts`, `created_at`.
- `reports`: `id` (PK), `media_type`, `movie_id`, `series_id`, `episode_id`, `issue_type`, `status` ('pending', 'resolved', 'dismissed').
- `seed_candidates`: `id` (PK), `tmdb_id`, `media_type` ('movie'/'tv'), `title`, `status` ('discovered', 'matched', 'enqueued', 'completed', 'not_found').

### 2. Kontent Turi (Content TYPE / KIND) Qanday Belgilanadi va O'qiladi?
Loyiha arxitekturasida ma'lumotlar turini (Movie vs Series vs Anime vs Cartoon) belgilash bo'yicha **FUNDAMENTAL STRUKTURAVIY NOANIQLIK** mavjud:

1. **Kino va Serial Alohida Jadvallarda**:
   - Bazada yagona `media` jadvali yo'q. Kinolar `movies` jadvalida, seriallar esa `series` jadvalida saqlanadi.
   - `movies` jadvalida filmning turi (kinomi, multfilmmi, animemi) haqida ALOHIDA USTUN YO'Q!
   - `series` jadvalida ham serialning turi (oddiy teleserialmi, anime serialmi, multserialmi) haqida ALOHIDA USTUN YO'Q!

2. **Anime va Multfilm Turi Qanday Belgilanadi?**:
   - **Metod 1: Janrlar (`genres` ustuni)**: Matnli string, masalan: `'Animatsiya, Sarguzasht'` yoki `'Anime'`.
   - **Metod 2: Sahifalar (`pages` va `page_movie` / `page_series` bog'lanishlari)**: Website da `pages.slug = 'anime'` yoki `'multfilm'` bo'lgan sahifalarga id lar bog'lanadi.
   - **Metod 3: Kategoriyalar (`categories` va `movie_category` / `series_category`)**:
   - **Metod 4: TMDb Ingestor anime qoidasi (`is_tmdb_anime`)**: Faqat TMDb janr id=16 bo'lib, `original_language == 'ja'` bo'lsa anime deb hisoblanadi.

3. **Oqibat (CONFIRMED)**:
   - Agar AI agent yoki auto-index script serialni (masalan, Bleach yoki Kurtlar Vadisi) `movies` jadvaliga yozib qo'ysa, butun tizim uni yakka film deb hisoblaydi va barcha qismlarini bitta film ichida yo'qotadi.
   - Agar to'liq metrajli filmni (masalan, Interstellar yoki Titanic) `series` jadvaliga kiritib, 1-qism qilib qo'yilsa, sayt va bot uni serial sifatida taqdim etadi.
   - Hech qanday ma'lumotlar bazasi cheklovi (constraint) yoki trigger bunga to'sqinlik qilmaydi!

### 3. Migratsiyalar Zanjiri vs Modellar vs Jonli Baza (Three-Way Diff)
Alembic migratsiyalar zanjiri (`backend/alembic/versions/`):
1. `9b8c7d6e5f4a_initial_schema.py` -> Asosiy jadvallar (`movies`, `categories`, `users`, `channels`).
2. `a1b2c3d4e5f6_add_series_tables.py` -> `series`, `seasons`, `episodes`, `series_sources`.
3. `b2c3d4e5f6a1_add_translations_tables.py` -> `movie_translations`, `episode_translations`.
4. `c3d4e5f6a1b2_add_pages_tables.py` -> `pages`, `page_movie`, `page_series`.
5. `c1f2a3b4c5d6_add_publish_status_to_media.py` -> `publish_status` ustuni `movies` va `series` ga.
6. `d2e3f4a5b6c7_add_rejection_reason_to_media.py` -> `rejection_reason`.
7. `e3f4a5b6c7d8_add_reports_table.py` -> `reports` jadvali.
8. `f4a5b6c7d8e9_add_seed_candidates_table.py` -> `seed_candidates` jadvali.
9. `a5b6c7d8e9f0_add_source_type_to_media.py` -> `source_type` ustuni `movies` va `series` ga.

### 4. Jonli Bazani Tekshirish So'rovlari (Live DB Schema Forensics)
> [!IMPORTANT]
> R2 Xavfsizlik Qoidasiga muvofiq: `FORENSIC_DATABASE_URL` muhitda o'rnatilmagan (NOT SET). Shuning uchun ishlab chiqarish bazasiga ulanilmadi. Quyidagi SQL so'rovlari `FORENSIC_DATABASE_URL` berilganda bajarilishi lozim va hozirda **NOT-RUN** holatida qayd etildi.

```sql
-- 1. Jonli bazadagi jadvallar va ustunlar ro'yxati
SELECT table_name, column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;

-- 2. Jonli bazadagi indekslar
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- 3. Jonli bazadagi cheklovlar (Constraints)
SELECT conname, contype, conrelid::regclass AS table_name, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE connamespace = 'public'::regnamespace;

-- 4. Joriy Alembic migratsiya versiyasi
SELECT version_num FROM alembic_version;
```
