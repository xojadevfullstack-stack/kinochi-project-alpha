# Sud-Texnik Ekspertizasi: 01_INVENTORY_a.md
## Part 1 (A-qism): Loyiha Fayllari Inventarizatsiyasi, Muhit va Bog'liqliklar

**Tizim Muhiti:**
- Python versiyasi: `Python 3.14.6` (`C:\Python314\python.exe`)
- Node.js versiyasi: `v20.20.2`
- NPM versiyasi: `10.8.2`
- Git versiyasi: `2.55.0.windows.5`
- Jami Git kuzatuvidagi fayllar soni (`git ls-files`): **520 ta**
- `git status --porcelain` bo'yicha o'zgartirilgan va yangi fayllar soni: **173 ta**

### 1. Bog'liqlik (Dependency) Fayllari
| Fayl yo'li | Turi | Tavsif |
| :--- | :--- | :--- |
| `requirements.txt` | Python Pip | Asosiy loyiha python bog'liqliklari (FastAPI, aiogram, sqlalchemy, asyncpg, redis, pydantic) |
| `backend/requirements.txt` | Python Pip | Backend xizmati bog'liqliklari |
| `backend/pyproject.toml` | Python PEP 518/621 | Backend loyihasi metama'lumotlari va ruff/pytest sozlamalari |
| `bot/pyproject.toml` | Python PEP 518/621 | Telegram bot moduli metama'lumotlari |
| `website/package.json` | Node.js NPM | Website Next.js 14/15, TailwindCSS, React bog'liqliklari |
| `website/package-lock.json` | Node.js Lockfile | Website paketlarining qat'iy versiyalari |
| `admin-panel/package.json` | Node.js NPM | Admin panel Next.js, Radix UI, TailwindCSS bog'liqliklari |
| `admin-panel/package-lock.json` | Node.js Lockfile | Admin panel paketlarining qat'iy versiyalari |

### 2. .gitignore Qoidalari Tahlili
`.gitignore` fayli 109 qatordan iborat bo'lib, quyidagi muhim operatsion xususiyatlarga ega:
- Python keshlari (`__pycache__/`, `*.pyc`, `.venv/`, `env/`) chetlatilgan.
- Maxfiy fayllar (`.env`, `.env.*`) chetlatilgan, faqat `!.env.example` ochiq qoldirilgan.
- Scraper vaqtinchalik ma'lumotlari (`scraper/downloads/`, `downloads/`, `scraper/*.bak`, `scraper/state.json`) chetlatilgan.
- **KRITIK FORENSIC XUSUSIYAT**: `backend/*.json`, `backend/*summary*.txt`, `backend/unknown_errors.txt`, `unknown_errors.txt`, `ops/logs/`, `backups/`, `*.dump`, `*.sql` fayllari qat'iy ignore qilingan. Bu shuni anglatadiki, oxirgi reset va migratsiya paytidagi barcha loglar (`ops/logs/go_live_*.log`) va zaxira nusxalari (`backups/*.dump`) gitga kirmagan holda mahalliy diskda qolgan.

### 3. Git Kuzatuvidagi Fayllar Guruhlari (Top-Level Folders)
#### Papka: `(root)` (51 ta fayl)
| Fayl yo'li | Qatorlar soni | Maqsadi |
| :--- | :--- | :--- |
| `.gitignore` | 108 | Loyiha resurs fayli |
| `AUDIT_FINDINGS.md` | 563 | Hujjatlashtirish fayli |
| `AUDIT_OPS.md` | 115 | Hujjatlashtirish fayli |
| `AUDIT_REPORT.md` | 108 | Hujjatlashtirish fayli |
| `AUDIT_REPORT_2.md` | 1075 | Hujjatlashtirish fayli |
| `AUDIT_SEED.md` | 224 | Hujjatlashtirish fayli |
| `BUILD_PROGRESS.md` | 46 | Hujjatlashtirish fayli |
| `BUILD_PROGRESS_SEED.md` | 26 | Hujjatlashtirish fayli |
| `Dockerfile` | 18 | Loyiha resurs fayli |
| `FIX_OPS_REPORT.md` | 41 | Hujjatlashtirish fayli |
| `FIX_REPORT.md` | 23 | Hujjatlashtirish fayli |
| `FIX_SEED_REPORT.md` | 39 | Hujjatlashtirish fayli |
| `Kinochi_PRD_Technical_Documentation.md` | 516 | Hujjatlashtirish fayli |
| `OPS_PROGRESS.md` | 19 | Hujjatlashtirish fayli |
| `README.md` | 62 | Hujjatlashtirish fayli |
| `REHEARSAL_REPORT.md` | 56 | Hujjatlashtirish fayli |
| `VERIFY_DB.md` | 29 | Hujjatlashtirish fayli |
| `VERIFY_SEED.md` | 21 | Hujjatlashtirish fayli |
| `add_series_sources.sql` | 12 | Loyiha resurs fayli |
| `check_brgrns.py` | 21 | Python dastur kodi |
| `check_db.py` | 19 | Python dastur kodi |
| `check_db2.py` | 24 | Python dastur kodi |
| `check_specific_movie.py` | 24 | Python dastur kodi |
| `docker-compose.yml` | 73 | Konfiguratsiya yoki metadata fayli |
| `git_log.txt` | 0 | Konfiguratsiya yoki metadata fayli |
| `kinochi_senior_architecture.html` | 1664 | Loyiha resurs fayli |
| `neon_migration.sql` | 34 | Loyiha resurs fayli |
| `requirements.txt` | 24 | Python paket bog'liqliklari (dependencies) |
| `run.py` | 88 | Asosiy ilovani (bot + backend) ishga tushirish nuqtasi |
| `scratch_trailer_test.py` | 29 | Test moduli |
| `start.bat` | 455 | Operatsion yoki ishga tushirish skripti |
| `start_all.bat` | 25 | Operatsion yoki ishga tushirish skripti |
| `start_grabber.bat` | 74 | Operatsion yoki ishga tushirish skripti |
| `test_api.py` | 29 | Test moduli |
| `test_auto_index.py` | 52 | Test moduli |
| `test_cookies.py` | 11 | Test moduli |
| `test_db.py` | 29 | Test moduli |
| `test_movie.py` | 16 | Test moduli |
| `test_movie_code.py` | 10 | Test moduli |
| `test_movie_send.py` | 38 | Test moduli |
| `test_movie_sender2.py` | 39 | Test moduli |
| `test_pyd.py` | 0 | Test moduli |
| `test_pyrogram_peer.py` | 24 | Test moduli |
| `test_redis.py` | 12 | Test moduli |
| `test_redis2.py` | 12 | Test moduli |
| `test_regex.js` | 9 | Loyiha resurs fayli |
| `test_ui.js` | 39 | Loyiha resurs fayli |
| `test_ui.py` | 37 | Test moduli |
| `test_ui2.py` | 58 | Test moduli |
| `verify_cache.py` | 48 | Python dastur kodi |
| `video_modal_history.txt` | 1254 | Konfiguratsiya yoki metadata fayli |

#### Papka: `.agents` (6 ta fayl)
| Fayl yo'li | Qatorlar soni | Maqsadi |
| :--- | :--- | :--- |
| `.agents/PROJECT_STATE.md` | 84 | Hujjatlashtirish fayli |
| `.agents/rules/bot-thin-client.md` | 12 | Hujjatlashtirish fayli |
| `.agents/rules/clean-architecture-boundaries.md` | 59 | Hujjatlashtirish fayli |
| `.agents/rules/database-migrations.md` | 34 | Hujjatlashtirish fayli |
| `.agents/rules/security-env.md` | 9 | Hujjatlashtirish fayli |
| `.agents/rules/verification-protocol.md` | 34 | Hujjatlashtirish fayli |

#### Papka: `.github` (1 ta fayl)
| Fayl yo'li | Qatorlar soni | Maqsadi |
| :--- | :--- | :--- |
| `.github/workflows/ci.yml` | 52 | Konfiguratsiya yoki metadata fayli |

#### Papka: `admin-panel` (33 ta fayl)
| Fayl yo'li | Qatorlar soni | Maqsadi |
| :--- | :--- | :--- |
| `admin-panel/Dockerfile` | 21 | Loyiha resurs fayli |
| `admin-panel/app/audit/page.tsx` | 1810 | Next.js sahifa komponenti (UI route) |
| `admin-panel/app/blacklist/page.tsx` | 304 | Next.js sahifa komponenti (UI route) |
| `admin-panel/app/broadcasts/page.tsx` | 311 | Next.js sahifa komponenti (UI route) |
| `admin-panel/app/categories/page.tsx` | 204 | Next.js sahifa komponenti (UI route) |
| `admin-panel/app/channels/page.tsx` | 251 | Next.js sahifa komponenti (UI route) |
| `admin-panel/app/collections/page.tsx` | 681 | Next.js sahifa komponenti (UI route) |
| `admin-panel/app/globals.css` | 49 | Loyiha resurs fayli |
| `admin-panel/app/icon.svg` | 4 | Statik rasm/grafika fayli |
| `admin-panel/app/layout.tsx` | 37 | Next.js umumiy layout komponenti |
| `admin-panel/app/login/page.tsx` | 118 | Next.js sahifa komponenti (UI route) |
| `admin-panel/app/movies/page.tsx` | 1457 | Next.js sahifa komponenti (UI route) |
| `admin-panel/app/page.tsx` | 402 | Next.js sahifa komponenti (UI route) |
| `admin-panel/app/pages/page.tsx` | 210 | Next.js sahifa komponenti (UI route) |
| `admin-panel/app/rejected/page.tsx` | 445 | Next.js sahifa komponenti (UI route) |
| `admin-panel/app/reports/page.tsx` | 460 | Next.js sahifa komponenti (UI route) |
| `admin-panel/app/scraper/page.tsx` | 2697 | Next.js sahifa komponenti (UI route) |
| `admin-panel/app/series/[seriesId]/page.tsx` | 602 | Next.js sahifa komponenti (UI route) |
| `admin-panel/app/series/[seriesId]/seasons/[seasonId]/page.tsx` | 410 | Next.js sahifa komponenti (UI route) |
| `admin-panel/app/series/page.tsx` | 1412 | Next.js sahifa komponenti (UI route) |
| `admin-panel/app/sources/page.tsx` | 267 | Next.js sahifa komponenti (UI route) |
| `admin-panel/components/AdminShell.tsx` | 122 | React vizual UI komponenti |
| `admin-panel/components/Sidebar.tsx` | 118 | React vizual UI komponenti |
| `admin-panel/components/VideoUploadModal.tsx` | 390 | React vizual UI komponenti |
| `admin-panel/lib/api.ts` | 252 | Frontend yordamchi funksiyalari |
| `admin-panel/middleware.ts` | 74 | TypeScript/React frontend kodi |
| `admin-panel/next-env.d.ts` | 5 | TypeScript/React frontend kodi |
| `admin-panel/next.config.mjs` | 16 | Loyiha resurs fayli |
| `admin-panel/package-lock.json` | 1656 | Konfiguratsiya yoki metadata fayli |
| `admin-panel/package.json` | 26 | Node.js paket va skriptlar tavsifi |
| `admin-panel/postcss.config.js` | 6 | Loyiha resurs fayli |
| `admin-panel/tailwind.config.ts` | 104 | TypeScript/React frontend kodi |
| `admin-panel/tsconfig.json` | 26 | Konfiguratsiya yoki metadata fayli |

#### Papka: `backend` (237 ta fayl)
| Fayl yo'li | Qatorlar soni | Maqsadi |
| :--- | :--- | :--- |
| `backend/.env.example` | 40 | Loyiha resurs fayli |
| `backend/Dockerfile` | 17 | Loyiha resurs fayli |
| `backend/alembic.ini` | 70 | Loyiha resurs fayli |
| `backend/alembic/alembic.ini` | 43 | Loyiha resurs fayli |
| `backend/alembic/env.py` | 95 | Python dastur kodi |
| `backend/alembic/script.py.mako` | 25 | Loyiha resurs fayli |
| `backend/alembic/versions/.gitkeep` | 3 | Loyiha resurs fayli |
| `backend/alembic/versions/19a7009b0b0b_add_multi_dubbing.py` | 65 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/2fb109c075d0_auto_index_fields.py` | 55 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/51e906b9692f_add_watch_history_table.py` | 52 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/55501de0fffd_add_reviews_and_kinochi_rating.py` | 70 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/5f880cb7b638_add_episode_count_and_duration.py` | 31 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/66bfb6a20149_add_trailer_url_to_seriesmodel.py` | 29 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/7a1b2c3d4e5f_add_tmdb_id_to_movies_and_series.py` | 31 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/80c4dc9b2cdd_initial_movies_and_categories.py` | 135 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/830ed2f920d0_add_series_category_table.py` | 35 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/84dc4619e44e_add_series_models_and_is_series_flag.py` | 62 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/8e4e155f48db_add_dynamic_pages.py` | 100 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/930ed2f920d1_add_poster_url_to_season.py` | 30 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/940ed2f920d2_add_metadata_to_series.py` | 38 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/a1b2c3d4e5f6_create_seed_candidates_table.py` | 59 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/b3a1c2d4e5f6_add_publish_status_to_movies_and_series.py` | 42 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/bd925cf13f66_add_status_to_series_and_seasons.py` | 31 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/c1d2e3f4a5b6_create_rejected_items_table.py` | 53 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/d4e5f6a1b2c3_unique_tmdb_id_on_movies_and_series.py` | 64 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/da3404d65ffd_rebuild_series_architecture.py` | 67 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/e8f9a0b1c2d3_set_default_pending_on_publish_status.py` | 28 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/eea5e498a8e6_add_user_achievements_table.py` | 42 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/f1a2b3c4d5e6_add_telegram_user_id_to_reports.py` | 40 | Ma'lumotlar bazasi migratsiyasi |
| `backend/alembic/versions/f48fc97f1dff_add_subscriber_limit_count_and_verified_.py` | 49 | Ma'lumotlar bazasi migratsiyasi |
| `backend/app/__init__.py` | 1 | Python dastur kodi |
| `backend/app/api/__init__.py` | 7 | Python dastur kodi |
| `backend/app/api/deps.py` | 178 | Python dastur kodi |
| `backend/app/api/limiter.py` | 4 | Python dastur kodi |
| `backend/app/api/v1/__init__.py` | 6 | FastAPI REST API marshruti (endpoint) |
| `backend/app/api/v1/audit.py` | 1423 | FastAPI REST API marshruti (endpoint) |
| `backend/app/api/v1/auth.py` | 191 | FastAPI REST API marshruti (endpoint) |
| `backend/app/api/v1/blacklist.py` | 138 | FastAPI REST API marshruti (endpoint) |
| `backend/app/api/v1/broadcasts.py` | 117 | FastAPI REST API marshruti (endpoint) |
| `backend/app/api/v1/categories.py` | 98 | FastAPI REST API marshruti (endpoint) |
| `backend/app/api/v1/channels.py` | 117 | FastAPI REST API marshruti (endpoint) |
| `backend/app/api/v1/collections.py` | 452 | FastAPI REST API marshruti (endpoint) |
| `backend/app/api/v1/content_lookup.py` | 223 | FastAPI REST API marshruti (endpoint) |
| `backend/app/api/v1/movies.py` | 658 | FastAPI REST API marshruti (endpoint) |
| `backend/app/api/v1/pages.py` | 202 | FastAPI REST API marshruti (endpoint) |
| `backend/app/api/v1/rejected.py` | 137 | FastAPI REST API marshruti (endpoint) |
| `backend/app/api/v1/reports.py` | 498 | FastAPI REST API marshruti (endpoint) |
| `backend/app/api/v1/reviews.py` | 115 | FastAPI REST API marshruti (endpoint) |
| `backend/app/api/v1/scraper.py` | 716 | FastAPI REST API marshruti (endpoint) |
| `backend/app/api/v1/search.py` | 224 | FastAPI REST API marshruti (endpoint) |
| `backend/app/api/v1/series.py` | 813 | FastAPI REST API marshruti (endpoint) |
| `backend/app/api/v1/series_subscriptions.py` | 190 | FastAPI REST API marshruti (endpoint) |
| `backend/app/api/v1/sources.py` | 51 | FastAPI REST API marshruti (endpoint) |
| `backend/app/api/v1/statistics.py` | 111 | FastAPI REST API marshruti (endpoint) |
| `backend/app/api/v1/telegram_auth.py` | 273 | FastAPI REST API marshruti (endpoint) |
| `backend/app/api/v1/users.py` | 321 | FastAPI REST API marshruti (endpoint) |
| `backend/app/application/__init__.py` | 16 | Python dastur kodi |
| `backend/app/application/broadcasts/__init__.py` | 1 | Python dastur kodi |
| `backend/app/application/broadcasts/sender.py` | 83 | Python dastur kodi |
| `backend/app/application/broadcasts/service.py` | 43 | Python dastur kodi |
| `backend/app/application/categories/__init__.py` | 1 | Python dastur kodi |
| `backend/app/application/categories/service.py` | 48 | Python dastur kodi |
| `backend/app/application/channels/__init__.py` | 1 | Python dastur kodi |
| `backend/app/application/channels/service.py` | 58 | Python dastur kodi |
| `backend/app/application/movies/__init__.py` | 1 | Python dastur kodi |
| `backend/app/application/movies/service.py` | 146 | Python dastur kodi |
| `backend/app/application/series/series_service.py` | 253 | Python dastur kodi |
| `backend/app/application/statistics/__init__.py` | 1 | Python dastur kodi |
| `backend/app/application/users/__init__.py` | 1 | Python dastur kodi |
| `backend/app/application/users/service.py` | 35 | Python dastur kodi |
| `backend/app/core/__init__.py` | 7 | Python dastur kodi |
| `backend/app/core/achievements.py` | 150 | Python dastur kodi |
| `backend/app/core/admission_gate.py` | 575 | Python dastur kodi |
| `backend/app/core/cache.py` | 81 | Python dastur kodi |
| `backend/app/core/config.py` | 109 | Konfiguratsiya va sozlamalar |
| `backend/app/core/franchise_canon.py` | 925 | Python dastur kodi |
| `backend/app/core/job_manager.py` | 94 | Python dastur kodi |
| `backend/app/core/recommendations.py` | 175 | Python dastur kodi |
| `backend/app/core/reviews.py` | 258 | Python dastur kodi |
| `backend/app/core/seed_config.py` | 67 | Konfiguratsiya va sozlamalar |
| `backend/app/core/watch_history.py` | 292 | Python dastur kodi |
| `backend/app/domain/__init__.py` | 14 | Python dastur kodi |
| `backend/app/domain/admin_users/__init__.py` | 1 | Python dastur kodi |
| `backend/app/domain/admin_users/entities.py` | 14 | Python dastur kodi |
| `backend/app/domain/broadcasts/__init__.py` | 1 | Python dastur kodi |
| `backend/app/domain/broadcasts/entities.py` | 21 | Python dastur kodi |
| `backend/app/domain/broadcasts/repository.py` | 9 | Python dastur kodi |
| `backend/app/domain/categories/__init__.py` | 1 | Python dastur kodi |
| `backend/app/domain/categories/entities.py` | 15 | Python dastur kodi |
| `backend/app/domain/categories/repository.py` | 33 | Python dastur kodi |
| `backend/app/domain/channels/__init__.py` | 1 | Python dastur kodi |
| `backend/app/domain/channels/entities.py` | 15 | Python dastur kodi |
| `backend/app/domain/channels/repository.py` | 12 | Python dastur kodi |
| `backend/app/domain/movies/__init__.py` | 1 | Python dastur kodi |
| `backend/app/domain/movies/entities.py` | 56 | Python dastur kodi |
| `backend/app/domain/movies/repository.py` | 51 | Python dastur kodi |
| `backend/app/domain/pages/entities.py` | 9 | Python dastur kodi |
| `backend/app/domain/series/entities.py` | 141 | Python dastur kodi |
| `backend/app/domain/series/source_entities.py` | 25 | Python dastur kodi |
| `backend/app/domain/users/__init__.py` | 1 | Python dastur kodi |
| `backend/app/domain/users/entities.py` | 16 | Python dastur kodi |
| `backend/app/domain/users/repository.py` | 9 | Python dastur kodi |
| `backend/app/infrastructure/__init__.py` | 14 | Python dastur kodi |
| `backend/app/infrastructure/cache/__init__.py` | 1 | Python dastur kodi |
| `backend/app/infrastructure/db/__init__.py` | 6 | Python dastur kodi |
| `backend/app/infrastructure/db/models/__init__.py` | 28 | SQLAlchemy ma'lumotlar modeli |
| `backend/app/infrastructure/db/models/achievement.py` | 15 | SQLAlchemy ma'lumotlar modeli |
| `backend/app/infrastructure/db/models/admin_user.py` | 17 | SQLAlchemy ma'lumotlar modeli |
| `backend/app/infrastructure/db/models/blacklist.py` | 18 | SQLAlchemy ma'lumotlar modeli |
| `backend/app/infrastructure/db/models/broadcast.py` | 22 | SQLAlchemy ma'lumotlar modeli |
| `backend/app/infrastructure/db/models/category.py` | 28 | SQLAlchemy ma'lumotlar modeli |
| `backend/app/infrastructure/db/models/channel.py` | 33 | SQLAlchemy ma'lumotlar modeli |
| `backend/app/infrastructure/db/models/collection.py` | 69 | SQLAlchemy ma'lumotlar modeli |
| `backend/app/infrastructure/db/models/movie.py` | 80 | SQLAlchemy ma'lumotlar modeli |
| `backend/app/infrastructure/db/models/page.py` | 45 | SQLAlchemy ma'lumotlar modeli |
| `backend/app/infrastructure/db/models/rejected_item.py` | 36 | SQLAlchemy ma'lumotlar modeli |
| `backend/app/infrastructure/db/models/report.py` | 35 | SQLAlchemy ma'lumotlar modeli |
| `backend/app/infrastructure/db/models/review.py` | 51 | SQLAlchemy ma'lumotlar modeli |
| `backend/app/infrastructure/db/models/seed_candidate.py` | 49 | SQLAlchemy ma'lumotlar modeli |
| `backend/app/infrastructure/db/models/series.py` | 131 | SQLAlchemy ma'lumotlar modeli |
| `backend/app/infrastructure/db/models/series_subscription.py` | 23 | SQLAlchemy ma'lumotlar modeli |
| `backend/app/infrastructure/db/models/source.py` | 23 | SQLAlchemy ma'lumotlar modeli |
| `backend/app/infrastructure/db/models/translation.py` | 36 | SQLAlchemy ma'lumotlar modeli |
| `backend/app/infrastructure/db/models/user.py` | 20 | SQLAlchemy ma'lumotlar modeli |
| `backend/app/infrastructure/db/models/watch_history.py` | 44 | SQLAlchemy ma'lumotlar modeli |
| `backend/app/infrastructure/db/query_filters.py` | 36 | Python dastur kodi |
| `backend/app/infrastructure/db/repositories/__init__.py` | 7 | Baza bilan ishlash repository qatlami |
| `backend/app/infrastructure/db/repositories/broadcast_repo.py` | 66 | Baza bilan ishlash repository qatlami |
| `backend/app/infrastructure/db/repositories/category_repo.py` | 63 | Baza bilan ishlash repository qatlami |
| `backend/app/infrastructure/db/repositories/channel_repo.py` | 107 | Baza bilan ishlash repository qatlami |
| `backend/app/infrastructure/db/repositories/movie_repo.py` | 256 | Baza bilan ishlash repository qatlami |
| `backend/app/infrastructure/db/repositories/series_repository.py` | 527 | Baza bilan ishlash repository qatlami |
| `backend/app/infrastructure/db/repositories/source_repository.py` | 52 | Baza bilan ishlash repository qatlami |
| `backend/app/infrastructure/db/repositories/user_repo.py` | 69 | Baza bilan ishlash repository qatlami |
| `backend/app/infrastructure/db/session.py` | 61 | Python dastur kodi |
| `backend/app/infrastructure/external/__init__.py` | 1 | Python dastur kodi |
| `backend/app/infrastructure/external/genre_mapper.py` | 109 | Python dastur kodi |
| `backend/app/infrastructure/external/tmdb_client.py` | 461 | Python dastur kodi |
| `backend/app/infrastructure/external/translator.py` | 197 | Python dastur kodi |
| `backend/app/infrastructure/security/__init__.py` | 1 | Python dastur kodi |
| `backend/app/infrastructure/security/jwt_handler.py` | 44 | Python dastur kodi |
| `backend/app/infrastructure/security/password_hasher.py` | 18 | Python dastur kodi |
| `backend/app/infrastructure/telegram/__init__.py` | 1 | Python dastur kodi |
| `backend/app/infrastructure/telegram/telegram_client.py` | 498 | Python dastur kodi |
| `backend/app/main.py` | 211 | FastAPI ilovasini ishga tushirish nuqtasi |
| `backend/app/utils/telegram_link_parser.py` | 81 | Python dastur kodi |
| `backend/app/utils/trailer.py` | 92 | Python dastur kodi |
| `backend/apply_all.py` | 83 | Python dastur kodi |
| `backend/apply_migration.py` | 36 | Ma'lumotlar bazasi migratsiyasi |
| `backend/apply_sync.py` | 84 | Python dastur kodi |
| `backend/check_by_source.py` | 18 | Python dastur kodi |
| `backend/check_db.py` | 17 | Python dastur kodi |
| `backend/check_migration.py` | 43 | Ma'lumotlar bazasi migratsiyasi |
| `backend/check_pages.py` | 13 | Python dastur kodi |
| `backend/check_routes.py` | 23 | Python dastur kodi |
| `backend/check_specific_movie.py` | 24 | Python dastur kodi |
| `backend/fix_alembic_version.py` | 73 | Python dastur kodi |
| `backend/fix_slug.py` | 12 | Python dastur kodi |
| `backend/local_test.py` | 14 | Test moduli |
| `backend/local_test_auth.py` | 14 | Test moduli |
| `backend/local_test_auth2.py` | 31 | Test moduli |
| `backend/pyproject.toml` | 64 | Python loyiha konfiguratsiyasi |
| `backend/requirements.txt` | 23 | Python paket bog'liqliklari (dependencies) |
| `backend/run_migration.py` | 28 | Ma'lumotlar bazasi migratsiyasi |
| `backend/run_setup.ps1` | 29 | Operatsion yoki ishga tushirish skripti |
| `backend/scripts/create_superadmin.py` | 76 | Yordamchi/operatsion skript |
| `backend/scripts/init_collections_db.py` | 18 | Yordamchi/operatsion skript |
| `backend/scripts/inspect_and_fix_adult.py` | 172 | Yordamchi/operatsion skript |
| `backend/scripts/inspect_collections_and_movies.py` | 42 | Yordamchi/operatsion skript |
| `backend/scripts/inspect_telegram_titles.py` | 56 | Yordamchi/operatsion skript |
| `backend/scripts/migrate_new_features.py` | 50 | Yordamchi/operatsion skript |
| `backend/scripts/seed_franchises.py` | 139 | Yordamchi/operatsion skript |
| `backend/scripts/test_redis_graceful.py` | 25 | Test moduli |
| `backend/setup.bat` | 31 | Operatsion yoki ishga tushirish skripti |
| `backend/temp_setup.py` | 24 | Python dastur kodi |
| `backend/test_api.py` | 10 | Test moduli |
| `backend/test_create_movie.py` | 25 | Test moduli |
| `backend/test_movie_code.py` | 13 | Test moduli |
| `backend/test_put_500.py` | 31 | Test moduli |
| `backend/tests/__init__.py` | 1 | Test moduli |
| `backend/tests/conftest.py` | 60 | Test moduli |
| `backend/tests/pg/test_real_postgres_integration.py` | 337 | Test moduli |
| `backend/tests/test_admission_gate.py` | 202 | Test moduli |
| `backend/tests/test_admission_gate_s6.py` | 82 | Test moduli |
| `backend/tests/test_adversarial_71_pairs.py` | 149 | Test moduli |
| `backend/tests/test_audit_fixes.py` | 175 | Test moduli |
| `backend/tests/test_auth.py` | 110 | Test moduli |
| `backend/tests/test_auth_ratelimit.py` | 37 | Test moduli |
| `backend/tests/test_blacklist_matching.py` | 85 | Test moduli |
| `backend/tests/test_bot_html_escape.py` | 46 | Test moduli |
| `backend/tests/test_bot_throttling.py` | 91 | Test moduli |
| `backend/tests/test_broadcast_service.py` | 84 | Test moduli |
| `backend/tests/test_category_service.py` | 40 | Test moduli |
| `backend/tests/test_channel_service.py` | 133 | Test moduli |
| `backend/tests/test_circuit_breaker_and_rejected_api.py` | 133 | Test moduli |
| `backend/tests/test_content_lookup.py` | 100 | Test moduli |
| `backend/tests/test_duplicates.py` | 81 | Test moduli |
| `backend/tests/test_fix_f001_ingest_pusu.py` | 72 | Test moduli |
| `backend/tests/test_fix_f002_pipeline_pre_check.py` | 75 | Test moduli |
| `backend/tests/test_fix_f003_series_upload_gate.py` | 89 | Test moduli |
| `backend/tests/test_fix_f005_default_languages.py` | 54 | Test moduli |
| `backend/tests/test_fix_f006_seasons_publish_status.py` | 34 | Test moduli |
| `backend/tests/test_fix_f007_collections_leak.py` | 120 | Test moduli |
| `backend/tests/test_fix_f008_tmdb_concurrency.py` | 49 | Test moduli |
| `backend/tests/test_fix_f009_script_bypass_flags.py` | 29 | Test moduli |
| `backend/tests/test_fix_f010_reports_system.py` | 172 | Test moduli |
| `backend/tests/test_fix_f011_cors_reflection.py` | 43 | Test moduli |
| `backend/tests/test_fix_f012_ssl_verification.py` | 22 | Test moduli |
| `backend/tests/test_fix_f013_swallowed_exceptions.py` | 36 | Test moduli |
| `backend/tests/test_fix_f016_cyrillic_slug.py` | 16 | Test moduli |
| `backend/tests/test_fix_f017_single_instance_lock.py` | 21 | Test moduli |
| `backend/tests/test_health.py` | 25 | Test moduli |
| `backend/tests/test_link_episode_video.py` | 71 | Test moduli |
| `backend/tests/test_movie_service.py` | 87 | Test moduli |
| `backend/tests/test_open_topic.py` | 132 | Test moduli |
| `backend/tests/test_ops_scripts.py` | 434 | Test moduli |
| `backend/tests/test_public_routes_publish_status.py` | 97 | Test moduli |
| `backend/tests/test_publish_status.py` | 71 | Test moduli |
| `backend/tests/test_rejected_items_model.py` | 77 | Test moduli |
| `backend/tests/test_reset_media_s8.py` | 230 | Test moduli |
| `backend/tests/test_root.py` | 10 | Test moduli |
| `backend/tests/test_run_scraper_flood_wait.py` | 89 | Test moduli |
| `backend/tests/test_seed_candidate_model_s3.py` | 92 | Test moduli |
| `backend/tests/test_seed_config_s2.py` | 52 | Test moduli |
| `backend/tests/test_seed_ingestor_full_s9.py` | 231 | Test moduli |
| `backend/tests/test_series_seasons.py` | 168 | Test moduli |
| `backend/tests/test_series_service.py` | 175 | Test moduli |
| `backend/tests/test_storage_locking_and_defaults.py` | 75 | Test moduli |
| `backend/tests/test_telegram_auth.py` | 148 | Test moduli |
| `backend/tests/test_telegram_link_parser.py` | 60 | Test moduli |
| `backend/tests/test_tmdb_client_s1.py` | 144 | Test moduli |
| `backend/tests/test_tmdb_id.py` | 28 | Test moduli |
| `backend/tests/test_tmdb_top_ingestor_s4_s5.py` | 179 | Test moduli |
| `backend/tests/test_trailer_url.py` | 68 | Test moduli |
| `backend/tests/test_translation.py` | 62 | Test moduli |
| `backend/tests/test_user_service.py` | 82 | Test moduli |
| `backend/tests/test_write_paths_gate.py` | 94 | Test moduli |

#### Papka: `bot` (30 ta fayl)
| Fayl yo'li | Qatorlar soni | Maqsadi |
| :--- | :--- | :--- |
| `bot/.env.example` | 4 | Loyiha resurs fayli |
| `bot/Dockerfile` | 15 | Loyiha resurs fayli |
| `bot/config.py` | 23 | Konfiguratsiya va sozlamalar |
| `bot/handlers/auto_index.py` | 594 | Telegram bot xabar/callback handleri |
| `bot/handlers/browsing.py` | 75 | Telegram bot xabar/callback handleri |
| `bot/handlers/catalog.py` | 314 | Telegram bot xabar/callback handleri |
| `bot/handlers/check_sub.py` | 18 | Telegram bot xabar/callback handleri |
| `bot/handlers/episode.py` | 87 | Telegram bot xabar/callback handleri |
| `bot/handlers/history.py` | 145 | Telegram bot xabar/callback handleri |
| `bot/handlers/profile.py` | 136 | Telegram bot xabar/callback handleri |
| `bot/handlers/recommendation.py` | 230 | Telegram bot xabar/callback handleri |
| `bot/handlers/reports.py` | 144 | Telegram bot xabar/callback handleri |
| `bot/handlers/reviews.py` | 346 | Telegram bot xabar/callback handleri |
| `bot/handlers/search.py` | 310 | Telegram bot xabar/callback handleri |
| `bot/handlers/start.py` | 93 | Telegram bot xabar/callback handleri |
| `bot/handlers/trailer.py` | 106 | Telegram bot xabar/callback handleri |
| `bot/handlers/translation_callback.py` | 67 | Telegram bot xabar/callback handleri |
| `bot/keyboards/__init__.py` | 1 | Telegram bot inline/reply klaviaturalari |
| `bot/keyboards/inline.py` | 187 | Telegram bot inline/reply klaviaturalari |
| `bot/keyboards/translations.py` | 19 | Telegram bot inline/reply klaviaturalari |
| `bot/main.py` | 128 | FastAPI ilovasini ishga tushirish nuqtasi |
| `bot/middlewares/__init__.py` | 1 | Middleware (filtrlash, antiflood, audit) |
| `bot/middlewares/subscription_check.py` | 87 | Middleware (filtrlash, antiflood, audit) |
| `bot/middlewares/throttling.py` | 81 | Middleware (filtrlash, antiflood, audit) |
| `bot/pyproject.toml` | 24 | Python loyiha konfiguratsiyasi |
| `bot/services/api_client.py` | 358 | Biznes mantiq xizmati (service) |
| `bot/utils/code_resolver.py` | 172 | Python dastur kodi |
| `bot/utils/episode_sender.py` | 105 | Python dastur kodi |
| `bot/utils/info_sender.py` | 343 | Python dastur kodi |
| `bot/utils/movie_sender.py` | 123 | Python dastur kodi |

#### Papka: `docs` (2 ta fayl)
| Fayl yo'li | Qatorlar soni | Maqsadi |
| :--- | :--- | :--- |
| `docs/AUDIT_STATUS.md` | 37 | Hujjatlashtirish fayli |
| `docs/SEED_INGESTOR.md` | 130 | Hujjatlashtirish fayli |

#### Papka: `ops` (7 ta fayl)
| Fayl yo'li | Qatorlar soni | Maqsadi |
| :--- | :--- | :--- |
| `ops/README.md` | 133 | Hujjatlashtirish fayli |
| `ops/db_checks.py` | 398 | Python dastur kodi |
| `ops/go_live.ps1` | 575 | Operatsion yoki ishga tushirish skripti |
| `ops/new_telegram_session.py` | 209 | Python dastur kodi |
| `ops/pilot.ps1` | 153 | Operatsion yoki ishga tushirish skripti |
| `ops/redis_flush_cache.py` | 141 | Python dastur kodi |
| `ops/test_stability.py` | 62 | Test moduli |

#### Papka: `refs img` (29 ta fayl)
| Fayl yo'li | Qatorlar soni | Maqsadi |
| :--- | :--- | :--- |
| `refs img/1 (1).png` | 0 | Statik rasm/grafika fayli |
| `refs img/1.png` | 0 | Statik rasm/grafika fayli |
| `refs img/10 (1).png` | 0 | Statik rasm/grafika fayli |
| `refs img/10.png` | 0 | Statik rasm/grafika fayli |
| `refs img/11 (1).png` | 0 | Statik rasm/grafika fayli |
| `refs img/11.png` | 0 | Statik rasm/grafika fayli |
| `refs img/12 (1).png` | 0 | Statik rasm/grafika fayli |
| `refs img/12.png` | 0 | Statik rasm/grafika fayli |
| `refs img/13 (1).png` | 0 | Statik rasm/grafika fayli |
| `refs img/13.png` | 0 | Statik rasm/grafika fayli |
| `refs img/14 (1).png` | 0 | Statik rasm/grafika fayli |
| `refs img/14.png` | 0 | Statik rasm/grafika fayli |
| `refs img/15.png` | 0 | Statik rasm/grafika fayli |
| `refs img/2 (1).png` | 0 | Statik rasm/grafika fayli |
| `refs img/2.png` | 0 | Statik rasm/grafika fayli |
| `refs img/3 (1).png` | 0 | Statik rasm/grafika fayli |
| `refs img/3.png` | 0 | Statik rasm/grafika fayli |
| `refs img/4 (1).png` | 0 | Statik rasm/grafika fayli |
| `refs img/4.png` | 0 | Statik rasm/grafika fayli |
| `refs img/5 (1).png` | 0 | Statik rasm/grafika fayli |
| `refs img/5.png` | 0 | Statik rasm/grafika fayli |
| `refs img/6 (1).png` | 0 | Statik rasm/grafika fayli |
| `refs img/6.png` | 0 | Statik rasm/grafika fayli |
| `refs img/7 (1).png` | 0 | Statik rasm/grafika fayli |
| `refs img/7.png` | 0 | Statik rasm/grafika fayli |
| `refs img/8 (1).png` | 0 | Statik rasm/grafika fayli |
| `refs img/8.png` | 0 | Statik rasm/grafika fayli |
| `refs img/9 (1).png` | 0 | Statik rasm/grafika fayli |
| `refs img/9.png` | 0 | Statik rasm/grafika fayli |

#### Papka: `scraper` (32 ta fayl)
| Fayl yo'li | Qatorlar soni | Maqsadi |
| :--- | :--- | :--- |
| `scraper/admission_gate.py` | 34 | Scraper va kontent yig'ish moduli |
| `scraper/animeelar_catalog.json` | 182 | Konfiguratsiya yoki metadata fayli |
| `scraper/animeelar_parser.py` | 206 | Scraper va kontent yig'ish moduli |
| `scraper/anitoob_catalog.json` | 2151 | Konfiguratsiya yoki metadata fayli |
| `scraper/anitoob_parser.py` | 369 | Scraper va kontent yig'ish moduli |
| `scraper/asilmedia_client.py` | 216 | Scraper va kontent yig'ish moduli |
| `scraper/autopilot_v2/__init__.py` | 25 | Scraper va kontent yig'ish moduli |
| `scraper/autopilot_v2/anime_health_router.py` | 91 | Scraper va kontent yig'ish moduli |
| `scraper/autopilot_v2/engine.py` | 102 | Scraper va kontent yig'ish moduli |
| `scraper/autopilot_v2/health_evaluator.py` | 207 | Scraper va kontent yig'ish moduli |
| `scraper/autopilot_v2/quality_manager.py` | 148 | Scraper va kontent yig'ish moduli |
| `scraper/autopilot_v2/quarantine_manager.py` | 172 | Scraper va kontent yig'ish moduli |
| `scraper/autopilot_v2/seed_generator.py` | 104 | Scraper va kontent yig'ish moduli |
| `scraper/config.py` | 67 | Konfiguratsiya va sozlamalar |
| `scraper/duplicate_checker.py` | 668 | Scraper va kontent yig'ish moduli |
| `scraper/fast_telethon.py` | 431 | Scraper va kontent yig'ish moduli |
| `scraper/fix_missing_sources_and_confirmations.py` | 196 | Scraper va kontent yig'ish moduli |
| `scraper/ingest_pusu.py` | 394 | Scraper va kontent yig'ish moduli |
| `scraper/moderator_pipeline.py` | 671 | Scraper va kontent yig'ish moduli |
| `scraper/process_manager.py` | 420 | Scraper va kontent yig'ish moduli |
| `scraper/queue_manager.py` | 451 | Scraper va kontent yig'ish moduli |
| `scraper/run_scraper.py` | 708 | Scraper va kontent yig'ish moduli |
| `scraper/seed_config.py` | 35 | Konfiguratsiya va sozlamalar |
| `scraper/site_parser.py` | 301 | Scraper va kontent yig'ish moduli |
| `scraper/site_search.py` | 147 | Scraper va kontent yig'ish moduli |
| `scraper/smart_enricher.py` | 965 | Scraper va kontent yig'ish moduli |
| `scraper/state_manager.py` | 111 | Scraper va kontent yig'ish moduli |
| `scraper/telegram_grabber.py` | 283 | Scraper va kontent yig'ish moduli |
| `scraper/telethon_moderator_pipeline.py` | 3966 | Scraper va kontent yig'ish moduli |
| `scraper/test_autopilot_v2.py` | 165 | Test moduli |
| `scraper/title_cleaner.py` | 182 | Scraper va kontent yig'ish moduli |
| `scraper/tmdb_top_ingestor.py` | 670 | Scraper va kontent yig'ish moduli |

#### Papka: `scripts` (9 ta fayl)
| Fayl yo'li | Qatorlar soni | Maqsadi |
| :--- | :--- | :--- |
| `scripts/build_anitoob_catalog.py` | 383 | Yordamchi/operatsion skript |
| `scripts/check_categories.py` | 25 | Yordamchi/operatsion skript |
| `scripts/clean_dirty_db_records.py` | 82 | Yordamchi/operatsion skript |
| `scripts/collect_user_franchises.py` | 99 | Yordamchi/operatsion skript |
| `scripts/fix_anime_everything_db.py` | 361 | Yordamchi/operatsion skript |
| `scripts/fix_anime_posters_db.py` | 93 | Yordamchi/operatsion skript |
| `scripts/migrate_18plus_and_reports.py` | 68 | Yordamchi/operatsion skript |
| `scripts/populate_franchise_queue.py` | 282 | Yordamchi/operatsion skript |
| `scripts/reset_media.py` | 274 | Yordamchi/operatsion skript |

#### Papka: `stitch_kinochi_premium_cinema` (14 ta fayl)
| Fayl yo'li | Qatorlar soni | Maqsadi |
| :--- | :--- | :--- |
| `stitch_kinochi_premium_cinema/design.md` | 64 | Hujjatlashtirish fayli |
| `stitch_kinochi_premium_cinema/kinochi_admin_dashboard/code.html` | 348 | Loyiha resurs fayli |
| `stitch_kinochi_premium_cinema/kinochi_admin_dashboard/screen.png` | 0 | Statik rasm/grafika fayli |
| `stitch_kinochi_premium_cinema/kinochi_barcha_filmlar/code.html` | 289 | Loyiha resurs fayli |
| `stitch_kinochi_premium_cinema/kinochi_barcha_filmlar/screen.png` | 0 | Statik rasm/grafika fayli |
| `stitch_kinochi_premium_cinema/kinochi_barcha_seriallar/code.html` | 384 | Loyiha resurs fayli |
| `stitch_kinochi_premium_cinema/kinochi_barcha_seriallar/screen.png` | 0 | Statik rasm/grafika fayli |
| `stitch_kinochi_premium_cinema/kinochi_home/code.html` | 330 | Loyiha resurs fayli |
| `stitch_kinochi_premium_cinema/kinochi_home/screen.png` | 0 | Statik rasm/grafika fayli |
| `stitch_kinochi_premium_cinema/kinochi_premium/DESIGN.md` | 175 | Hujjatlashtirish fayli |
| `stitch_kinochi_premium_cinema/movie_detail_dune_part_two/code.html` | 370 | Loyiha resurs fayli |
| `stitch_kinochi_premium_cinema/movie_detail_dune_part_two/screen.png` | 0 | Statik rasm/grafika fayli |
| `stitch_kinochi_premium_cinema/series_detail_house_of_the_dragon/code.html` | 378 | Loyiha resurs fayli |
| `stitch_kinochi_premium_cinema/series_detail_house_of_the_dragon/screen.png` | 0 | Statik rasm/grafika fayli |

#### Papka: `website` (69 ta fayl)
| Fayl yo'li | Qatorlar soni | Maqsadi |
| :--- | :--- | :--- |
| `website/.eslintrc.json` | 16 | Konfiguratsiya yoki metadata fayli |
| `website/app/achievements/page.tsx` | 378 | Next.js sahifa komponenti (UI route) |
| `website/app/catalog/page.tsx` | 5 | Next.js sahifa komponenti (UI route) |
| `website/app/category/[id]/page.tsx` | 116 | Next.js sahifa komponenti (UI route) |
| `website/app/collections/[slug]/page.tsx` | 120 | Next.js sahifa komponenti (UI route) |
| `website/app/collections/page.tsx` | 132 | Next.js sahifa komponenti (UI route) |
| `website/app/error.tsx` | 45 | TypeScript/React frontend kodi |
| `website/app/globals.css` | 56 | Loyiha resurs fayli |
| `website/app/history/page.tsx` | 128 | Next.js sahifa komponenti (UI route) |
| `website/app/icon.svg` | 4 | Statik rasm/grafika fayli |
| `website/app/layout.tsx` | 75 | Next.js umumiy layout komponenti |
| `website/app/movie/[code]/page.tsx` | 285 | Next.js sahifa komponenti (UI route) |
| `website/app/movies/page.tsx` | 85 | Next.js sahifa komponenti (UI route) |
| `website/app/notifications/page.tsx` | 334 | Next.js sahifa komponenti (UI route) |
| `website/app/p/[slug]/page.tsx` | 114 | Next.js sahifa komponenti (UI route) |
| `website/app/page.tsx` | 324 | Next.js sahifa komponenti (UI route) |
| `website/app/robots.ts` | 14 | TypeScript/React frontend kodi |
| `website/app/search/page.tsx` | 289 | Next.js sahifa komponenti (UI route) |
| `website/app/series/[id]/page.tsx` | 387 | Next.js sahifa komponenti (UI route) |
| `website/app/series/page.tsx` | 81 | Next.js sahifa komponenti (UI route) |
| `website/app/sitemap.ts` | 63 | TypeScript/React frontend kodi |
| `website/app/test-auth/page.tsx` | 16 | Next.js sahifa komponenti (UI route) |
| `website/components/AdultHeroBackground.tsx` | 38 | React vizual UI komponenti |
| `website/components/AdultPoster.tsx` | 99 | React vizual UI komponenti |
| `website/components/AgeVerificationModal.tsx` | 116 | React vizual UI komponenti |
| `website/components/BackButton.tsx` | 83 | React vizual UI komponenti |
| `website/components/BottomNav.tsx` | 97 | React vizual UI komponenti |
| `website/components/CategoryFilter.tsx` | 223 | React vizual UI komponenti |
| `website/components/CollectionTimelineView.tsx` | 227 | React vizual UI komponenti |
| `website/components/FranchiseTimelineBar.tsx` | 234 | React vizual UI komponenti |
| `website/components/LiveSearch.tsx` | 318 | React vizual UI komponenti |
| `website/components/Navbar.tsx` | 546 | React vizual UI komponenti |
| `website/components/ReportIssueButton.tsx` | 83 | React vizual UI komponenti |
| `website/components/ReportIssueModal.tsx` | 395 | React vizual UI komponenti |
| `website/components/ShareButton.tsx` | 140 | React vizual UI komponenti |
| `website/components/TelegramInit.tsx` | 67 | React vizual UI komponenti |
| `website/components/TelegramWatchButton.tsx` | 279 | React vizual UI komponenti |
| `website/components/TrailerModal.tsx` | 146 | React vizual UI komponenti |
| `website/components/auth/TelegramLoginWidget.tsx` | 52 | React vizual UI komponenti |
| `website/components/catalog/CatalogGrid.tsx` | 132 | React vizual UI komponenti |
| `website/components/catalog/CatalogTypeNav.tsx` | 82 | React vizual UI komponenti |
| `website/components/catalog/CategoryTabs.tsx` | 40 | React vizual UI komponenti |
| `website/components/catalog/MovieCard.tsx` | 90 | React vizual UI komponenti |
| `website/components/history/ContinueWatchingBanner.tsx` | 72 | React vizual UI komponenti |
| `website/components/history/HistoryGrid.tsx` | 96 | React vizual UI komponenti |
| `website/components/history/HistoryTabs.tsx` | 38 | React vizual UI komponenti |
| `website/components/recommendations/RandomRecommendationWidget.tsx` | 310 | React vizual UI komponenti |
| `website/components/recommendations/RecommendationsSection.tsx` | 84 | React vizual UI komponenti |
| `website/components/reviews/KinochiRatingBadge.tsx` | 54 | React vizual UI komponenti |
| `website/components/reviews/ReviewsSection.tsx` | 427 | React vizual UI komponenti |
| `website/hooks/useAgeVerification.ts` | 69 | TypeScript/React frontend kodi |
| `website/lib/adult.ts` | 44 | Frontend yordamchi funksiyalari |
| `website/lib/api.ts` | 44 | Frontend yordamchi funksiyalari |
| `website/lib/api/catalog.ts` | 90 | Frontend yordamchi funksiyalari |
| `website/lib/api/history.ts` | 59 | Frontend yordamchi funksiyalari |
| `website/lib/api/reviews.ts` | 76 | Frontend yordamchi funksiyalari |
| `website/lib/auth/AuthProvider.tsx` | 147 | Frontend yordamchi funksiyalari |
| `website/lib/auth/environment.js` | 17 | Loyiha resurs fayli |
| `website/lib/auth/environment.ts` | 31 | Frontend yordamchi funksiyalari |
| `website/lib/auth/tokenStorage.js` | 24 | Loyiha resurs fayli |
| `website/lib/auth/tokenStorage.ts` | 22 | Frontend yordamchi funksiyalari |
| `website/lib/telegram.ts` | 113 | Frontend yordamchi funksiyalari |
| `website/next-env.d.ts` | 5 | TypeScript/React frontend kodi |
| `website/next.config.mjs` | 18 | Loyiha resurs fayli |
| `website/package-lock.json` | 6383 | Konfiguratsiya yoki metadata fayli |
| `website/package.json` | 31 | Node.js paket va skriptlar tavsifi |
| `website/postcss.config.js` | 6 | Loyiha resurs fayli |
| `website/tailwind.config.ts` | 119 | TypeScript/React frontend kodi |
| `website/tsconfig.json` | 27 | Konfiguratsiya yoki metadata fayli |
