# BUILD_PROGRESS_SEED.md

Ushbu hujjat Kinochi loyihasida TMDb Oltin Kolleksiya (Top 1000 filmlar va 500 seriallar) urug'lantirish (Seed Ingestor) tizimini bosqichma-bosqich ishlab chiqish protokoli hisoblanadi.

## Checklist

- [x] **S1**: TMDb client kengaytmasi (`backend/app/infrastructure/external/tmdb_client.py`). `list_top_rated(kind, page)`, `list_popular(kind, page)`, `get_details(tmdb_id, kind)` with `append_to_response=videos,credits,translations,external_ids`. Rate limiter, retry-after (429), timeouts, response caching, xavfsiz API key. (Commit: `33a75f5`)
- [x] **S2**: Markazlashtirilgan sozlamalar (`SEED_MOVIE_TARGET=1000`, `SEED_TV_TARGET=500`, `SEED_INCLUDE_SERIES=false`, `SEED_MIN_VOTE_COUNT=1000`, `SEED_MIN_RATING=7.0`, `SEED_EXCLUDE_ADULT=true`, `SEED_BATCH_SIZE=20`, `SEED_NOT_FOUND_RETRY_DAYS=30`, `SEED_PRIORITY=100`, anime routing qoidasi). (Commit: `eb6ab85`)
- [x] **S3**: `seed_candidates` jadvali va modeli (SQLAlchemy + Alembic additiv migratsiya). `id`, `kind`, `tmdb_id`, `title_en`, `title_ru`, `original_title`, `release_year`, `vote_average`, `vote_count`, `popularity`, `is_anime`, `status`, `matches`, `attempts`, `last_searched_at`, `created_at`, `updated_at`, `UNIQUE(kind, tmdb_id)`. (Commit: `0947d3b`)
- [x] **S4**: `scraper/tmdb_top_ingestor.py` CLI: (Commit: `491204e`)
  - `--build-seeds`: TMDb ro'yxatlarini sahifalab filtrlar bilan yig'ish, idempotent upsert.
  - `--search --limit N`: status=new bo'yicha `site_search` orqali manbalardan qidirish (nom + yil + qism raqami tekshiruvi). 1 ta mos kelsa -> found, bir nechta -> ambiguous, 0 ta -> not_found.
  - `--enqueue --limit N`: default DRY-RUN, `--execute` bilan haqiqiy navbatga qo'yish (`priority=SEED_PRIORITY`, to'liq TMDb metadata payload).
  - `--stats`: Holat va rad etish sabablari statistikasi.
- [x] **S5**: Ambiguous va noto'g'ri mosliklarni `rejected_items` jadvaliga yozish (`source='tmdb_seed'`, `defect='ambiguous_source_match'`), Admin paneldan qayta qidirish imkoniyati. (Commit: `491204e`)
- [ ] **S6**: Pipeline integratsiyasi: Navbatdagi seed elementlari `tmdb_id` ga ega bo'ladi, Admission Gate qoidalaridan o'tadi. Tasdiqlansa `ingested`, rad etilsa `skipped`.
- [ ] **S7**: `start.bat` menyusiga integratsiya: build seeds, search, enqueue dry-run, enqueue execute (tasdiq so'raladi), seed stats, reset dry-run.
- [ ] **S8**: `scripts/reset_media.py` kengaytmasi: `seed_candidates` holatlarini yangilash va scraper json fayllarini tozalash (3 ta guard: `--execute`, tasdiqlash, quruq rejim).
- [ ] **S9**: Avtomatlashtirilgan testlar (TMDb va O'zbek manbalari mock/fixture bilan, 0 ta tashqi tarmoq so'rovi).
- [ ] **S10**: Hujjatlashtirish: `docs/SEED_INGESTOR.md` (o'zbek tilida to'liq qo'llanma, parametrlar va pilot reja).

## Decisions
- Production ma'lumotlar bazasiga hech qachon tegmaslik. Barcha testlar va mocklar xavfsiz muhitda bajariladi.
- Hech qanday kalitlar (API keys) va sirlar loglarga chiqarilmaydi.
- Mavjud `title_cleaner`, `smart_enricher`, `site_search`, `duplicate_checker`, `admission_gate`, `QueueManager` modullaridagi kodlarni takrorlamasdan to'g'ridan-to'g'ri qayta ishlatish.
- Seed ingestor hech qachon `movies`/`series` jadvallariga to'g'ridan-to'g'ri insert qilmaydi, faqat `seed_candidates`, `rejected_items` va navbatga yozadi. Oxirgi nashrni har doim `Admission Gate` hal qiladi.
