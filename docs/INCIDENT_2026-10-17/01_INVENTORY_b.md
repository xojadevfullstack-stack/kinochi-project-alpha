# Sud-Texnik Ekspertizasi: 01_INVENTORY_b.md
## Part 1 (B-qism): Ishga Tushirish Nuqtalari, Muhit O'zgaruvchilari va Feature Flaglar

### 1. Git Status --Porcelain (O'zgartirilgan va Yangi / Untracked Fayllar)
Jami nosinxron / untracked elementlar soni: **173 ta**.

Muhim guruhlar:
- **Modified Tracked Files (21 ta)**: admin-panel, backend (movies, scraper, series routerlari, admission_gate.py, franchise_canon.py, series_repository.py), bot/config.py, scraper modullari, website sahifalari.
- **Untracked Migration va Fix Skriptlari (scripts/)**: 110 dan ortiq bir martalik/ad-hoc skriptlar (masalan: `migrate_all_major_series.py`, `migrate_all_movies_individual_topics.py`, `fix_mismatched_movies.py`, `realign_all_posters.py` va h.k.).
- **Loyiha Ildizidagi Dump va Test Fayllari**: `all_movies_dump.txt`, `movies_names_list.txt`, `nextjs_error.html`, `tmdb_audit_report.txt`.

### 2. Barcha Ishga Tushirish Nuqtalari va CLI Rejimlari
| Kirish Nuqtasi (Entry Point) | Turi | Tavsif va Bajaradigan Buyruqlari |
| :--- | :--- | :--- |
| `run.py` | Asosiy Entry Point | FastAPI va aiogram botni bitta asyncio loopda (`uvicorn.Server` va `dp.start_polling`) parallel yurgizadi. CLI parametrlari: `--host`, `--port`, `--reload`, `--no-bot`. |
| `backend/app/main.py` | FastAPI App | Faqat backend REST API ni ishga tushirish (lifespan: DB connect, Redis ping). |
| `start_all.bat` | Windows Shell | Barcha xizmatlarni (backend, bot, website, admin-panel) alohida oynalarda start qiladi. |
| `start_backend.bat` | Windows Shell | `uvicorn app.main:app --reload --port 8000` buyrug'ini ishga tushiradi. |
| `start_bot.bat` | Windows Shell | `python -m bot.main` yoki `python run.py --no-backend` ni yurgizadi. |
| `start_website.bat` | Windows Shell | `npm run dev` (Next.js website, port 3000) ni ishga tushiradi. |
| `start_scraper.bat` | Windows Shell | Scraper va telethon moderator pipelinelarini ishga tushiradi. |
| `ops/go_live.ps1` | PowerShell Ops | Production deployment script (Alembic check, healthcheck, seed gate check, backup olish). |
| `ops/check_live.ps1` | PowerShell Ops | Live tizim statusi va endpointlarini tekshiruvchi monitoring skripti. |
| `ops/reset_media.py` | Python Ops | BAZANI TOZALASH SKRIPTI: Barcha media jadvallarini (`movies`, `series`, `seasons`, `episodes`, `translations`, `categories`) TRUNCATE/DELETE qiladi. |
| `scraper/run_scraper.py` | CLI Scraper | Tashqi botlardan (`uzmovi`, `asilmedia`, `animeelar`, `anitoob`) media yig'ish jarayoni menejeri. |
| `scraper/telethon_moderator_pipeline.py` | CLI Telethon | Telegram userbot orqali kanallardan xabarlarni yuklab olish va storage ga yo'naltirish. |
| `scraper/tmdb_top_ingestor.py` | CLI Seed Ingestor | TMDb API orqali eng sara filmlarni olib, `seed_candidates` jadvaliga yozish va navbatga qo'yish (`--search`, `--enqueue`). |
| `scripts/seed_ingestor.py` | CLI Ingestor | `tmdb_top_ingestor.py` uchun root wrapper skripti. |

### 3. Muhit O'zgaruvchilari (Environment Variables) Katalogi
| O'zgaruvchi Nomi | Aniqlangan / O'qilgan Manzili | Standart Qiymati (Default) | Maqsadi va Vazifasi |
| :--- | :--- | :--- | :--- |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `backend/app/core/config.py:70` | `30` | JWT access token amal qilish muddati (daqiqa) |
| `APP_ENV` | `backend/tests/conftest.py:11` | `REQUIRED (KeyError)` | Dastur muhiti (development / staging / production) |
| `AUTO_CONTENT_ENABLED` | `backend/app/core/config.py:86` | `True` | Avtomatik kontent indekslash global bayrog'i (Kill switch) |
| `AUTO_TOPIC_CHAT_ID` | `scraper/config.py:55` | `None` | Avtomatik forum mavzulari (topics) ochiladigan superguruh ID raqami |
| `BACKEND_API_URL` | `run.py:63` | `"http://127.0.0.1:8000/api/v1"` | Bot va tashqi xizmatlar murojaat qiladigan Backend REST API bazaviy URL manzili |
| `BOT_API_SECRET` | `backend/tests/conftest.py:16` | `REQUIRED (KeyError)` | Bot va Scraperdan Backend ichki API ga kirish uchun umumiy maxfiy kalit |
| `BOT_RATE_LIMIT_PER_MINUTE` | `bot/middlewares/throttling.py:29` | `None` | Bot foydalanuvchilariga daqiqalik so'rovlar limiti |
| `BOT_TOKEN` | `backend/tests/conftest.py:14` | `REQUIRED (KeyError)` | Telegram Bot API tokeni (@BotFather dan olingan) |
| `BOT_USERNAME` | `bot/config.py:15` | `"kinochi_mvp_bot"` | Telegram botining foydalanuvchi nomi (link generatorlar uchun) |
| `CORS_ORIGINS` | `backend/app/core/config.py:57` | `[]` | Tizim konfiguratsiyasi yoki lokal o'zgaruvchi |
| `DATABASE_URL` | `AUDIT_FINDINGS.md:146` | `None` | PostgreSQL async ulanish URI (asyncpg drayveri) |
| `DEBUG` | `backend/app/core/config.py:19` | `False` | Nosozliklarni aniqlash (debug) rejimi bayrog'i |
| `GEMINI_API_KEY` | `backend/app/core/config.py:84` | `""` | Google Gemini AI API kaliti (tavsiflar va tahlil uchun) |
| `HOST` | `run.py:27` | `"0.0.0.0"` | Tizim konfiguratsiyasi yoki lokal o'zgaruvchi |
| `JWT_SECRET_KEY` | `admin-panel/middleware.ts:13` | `None (JS undefined)` | Admin panel Next.js middleware JWT tekshiruvi uchun kalit |
| `MOCK_REMOTE_URL` | `backend/tests/test_ops_scripts.py:391` | `$null` | Tizim konfiguratsiyasi yoki lokal o'zgaruvchi |
| `NEXT_PUBLIC_API_URL` | `admin-panel/app/login/page.tsx:6` | `None (JS undefined)` | Next.js frontend tomonidan backend API ga so'rov yuborish URL manzili |
| `NEXT_PUBLIC_BOT_USERNAME` | `website/app/movie/[code]/page.tsx:69` | `None (JS undefined)` | Next.js frontendda bot havolalarini ko'rsatish uchun bot username |
| `NEXT_PUBLIC_SITE_URL` | `website/app/robots.ts:3` | `None (JS undefined)` | Veb-sayt sitemap va SEO uchun tashqi domen manzili |
| `PATH` | `ops/go_live.ps1:137` | `$null` | Tizim konfiguratsiyasi yoki lokal o'zgaruvchi |
| `PORT` | `run.py:26` | `8000` | Tizim konfiguratsiyasi yoki lokal o'zgaruvchi |
| `PROJECT_NAME` | `backend/app/core/config.py:16` | `"MediaPlus"` | Loyiha nomi metama'lumotlari |
| `PYTHONPATH` | `ops/go_live.ps1:155` | `$null` | Tizim konfiguratsiyasi yoki lokal o'zgaruvchi |
| `REDIS_URL` | `backend/scripts/test_redis_graceful.py:6` | `REQUIRED (KeyError)` | Redis kesh va rate limiter ulanish manzili (Upstash/lokal) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `backend/app/core/config.py:71` | `7` | JWT refresh token amal qilish muddati (kun) |
| `RENDER_EXTERNAL_URL` | `backend/app/main.py:41` | `None` | Tizim konfiguratsiyasi yoki lokal o'zgaruvchi |
| `SECRET_KEY` | `backend/tests/conftest.py:13` | `REQUIRED (KeyError)` | JWT tokenlarni imzolash uchun kriptografik kalit |
| `SEED_BATCH_SIZE` | `backend/app/core/config.py:95` | `20` | Seed Ingestor bitta siklda qayta ishlaydigan nomlar soni |
| `SEED_EXCLUDE_ADULT` | `backend/app/core/config.py:94` | `True` | Kattalar uchun kontentni (18+) filtrdan o'tkazish bayrog'i |
| `SEED_INCLUDE_SERIES` | `ops/README.md:129` | `$null` | Seed Ingestorga seriallarni qo'shish yoki qo'shmaslik bayrog'i |
| `SEED_MIN_RATING` | `backend/app/core/config.py:93` | `7.0` | TMDb da film tanlash uchun minimal reyting |
| `SEED_MIN_VOTE_COUNT` | `backend/app/core/config.py:92` | `1000` | TMDb da film tanlash uchun minimal ovozlar soni |
| `SEED_MOVIE_TARGET` | `backend/app/core/config.py:89` | `1000` | TMDb Seed Ingestor yig'ishi kerak bo'lgan kinolar maqsadi |
| `SEED_NOT_FOUND_RETRY_DAYS` | `backend/app/core/config.py:96` | `30` | Topilmagan nomlarni qayta qidirish oralig'i (kunlarda) |
| `SEED_PRIORITY` | `backend/app/core/config.py:97` | `100` | Seed orqali kelgan media navbatidagi ustuvorlik darajasi |
| `SEED_SEARCH_CONCURRENCY` | `backend/app/core/config.py:99` | `2` | Parallel qidiruv oqimlari soni |
| `SEED_SEARCH_DELAY_SECONDS` | `backend/app/core/config.py:98` | `1.0` | TMDb qidiruvlari orasidagi kechikish vaqti (soniya) |
| `SEED_TV_TARGET` | `backend/app/core/config.py:90` | `500` | TMDb Seed Ingestor yig'ishi kerak bo'lgan seriallar maqsadi |
| `STORAGE_CHANNEL_ID` | `backend/tests/conftest.py:15` | `REQUIRED (KeyError)` | Fayllar (video/audio) saqlanadigan yopiq kanal ID raqami |
| `TELEGRAM_API_HASH` | `ops/new_telegram_session.py:149` | `None` | Telethon MTProto API Hash kaliti |
| `TELEGRAM_API_ID` | `ops/new_telegram_session.py:148` | `None` | Telethon MTProto API ID raqami |
| `TELEGRAM_PHONE` | `ops/new_telegram_session.py:153` | `None` | Tizim konfiguratsiyasi yoki lokal o'zgaruvchi |
| `TELEGRAM_STRING_SESSION` | `scraper/config.py:51` | `None` | Telethon sessiya stringi (avtorizatsiyadan o'tgan userbot) |
| `TELETHON_SESSION` | `scraper/telethon_moderator_pipeline.py:100` | `None` | Tizim konfiguratsiyasi yoki lokal o'zgaruvchi |
| `TEST_DATABASE_URL` | `AUDIT_OPS.md:107` | `$null` | Tizim konfiguratsiyasi yoki lokal o'zgaruvchi |
| `TMDB_API_KEY` | `backend/app/core/config.py:83` | `""` | The Movie Database (TMDb) v3 API kaliti |
| `TMDB_RATE_LIMIT` | `backend/app/infrastructure/external/tmdb_client.py:55` | `"10.0"` | TMDb mijozining soniyalik so'rovlar chegarasi |
| `TMDB_TIMEOUT` | `backend/app/infrastructure/external/tmdb_client.py:57` | `"10.0"` | TMDb HTTP so'rovlarining kutish vaqti (timeout) |
| `USERBOT_SESSION_STRING` | `scraper/telethon_moderator_pipeline.py:99` | `None` | Tizim konfiguratsiyasi yoki lokal o'zgaruvchi |
| `VERSION` | `backend/app/core/config.py:17` | `"0.1.0"` | Loyiha versiyasi |
| `WEBSITE_URL` | `bot/config.py:14` | `"https://kinochi-project-alpha.vercel...` | Next.js veb-saytining domen manzili (deep-linklar uchun) |

### 4. Feature Flaglar va Ularning Kodda Tekshirilishi Tahlili
Loyiha kodida bir qator funksional bayroqlar (Feature Flags) e'lon qilingan. Quyida ularning har biri kodda qayerda va qanday tekshirilishi ko'rsatilgan:

#### 4.1. `AUTO_CONTENT_ENABLED`
- **Ta'rifi**: Avtomatik indekslash va kontent qo'shilishini to'xtatuvchi asosiy 'Kill Switch' deb taxmin qilingan.
- **Holati**: `backend/app/core/config.py:86` da `AUTO_CONTENT_ENABLED: bool = True` deb e'lon qilingan.
- **Tekshiruv Natijasi (CONFIRMED)**: **BUTUN KOD BAZASIDA HECH QAYERDA TEKSHIRILMAYDI!**
  - Na `bot/handlers/auto_index.py` da, na backend routerlarida, na scraperda bu bayroq o'qilmaydi.
  - Qidiruv isboti: `git grep AUTO_CONTENT_ENABLED` faqat konfiguratsiyaning o'zini qaytaradi:
    ```python
    backend/app/core/config.py:86:    AUTO_CONTENT_ENABLED: bool = True
    ```
  - **Xulosa**: Agent yoki administrator `AUTO_CONTENT_ENABLED=False` qilsa ham, auto-index to'xtamaydi, xabarlarni qabul qilib bazaga yozishda davom etadi.

#### 4.2. `SEED_INCLUDE_SERIES`
- **Ta'rifi**: TMDb Seed Ingestor seriallarni ham bazaga kiritishini belgilovchi bayroq.
- **Holati**: `backend/app/core/config.py:91` da `SEED_INCLUDE_SERIES: bool = False` qilib belgilangan.
- **Tekshiruv Natijasi (CONFIRMED)**: `scraper/tmdb_top_ingestor.py:270` da tekshiriladi:
  ```python
  # scraper/tmdb_top_ingestor.py:270
  if not SEED_INCLUDE_SERIES and media_type == 'tv':
      logger.info('SEED_INCLUDE_SERIES=False, TV shoulari chetlatildi.')
      return None
  ```

#### 4.3. `SEED_EXCLUDE_ADULT`
- **Ta'rifi**: 18+ filmlarni chetlatish bayrog'i.
- **Holati**: `backend/app/core/config.py:94` da `SEED_EXCLUDE_ADULT: bool = True`.
- **Tekshiruv Natijasi (CONFIRMED)**: `scraper/tmdb_top_ingestor.py:291` da tekshiriladi:
  ```python
  # scraper/tmdb_top_ingestor.py:291
  if SEED_EXCLUDE_ADULT and item.get('adult'):
      logger.debug(f'Adult content skipped: {title}')
      return None
  ```

#### 4.4. `REPORT_THRESHOLD` (Auto-hide shikoyat chegarasi)
- **Ta'rifi**: Kontent ustidan tushgan shikoyatlar soni bo'yicha uni avtomatik yashirish (`hidden`).
- **Holati**: `backend/app/api/v1/reports.py:209` da `REPORT_THRESHOLD = 5` deb qat'iy yozilgan (hardcoded).
- **Tekshiruv Natijasi (CONFIRMED)**: `backend/app/api/v1/reports.py:217` va `230` qatorlarida tekshiriladi:
  ```python
  # backend/app/api/v1/reports.py:217
  if (cnt_res.scalar() or 0) + 1 >= REPORT_THRESHOLD:
      target_movie.publish_status = 'hidden'
  ```

#### 4.5. `SEED_GATE_MODE` (Deployment Gate bayrog'i)
- **Ta'rifi**: Yangi kontent omma oldida darhol ko'rinmasligi uchun karantin rejimini boshqarish.
- **Holati**: `ops/go_live.ps1:455-474` da deploy jarayonida so'raladi va tekshiriladi.
- **Tekshiruv Natijasi (CONFIRMED)**: Ushbu bayroq deployment scriptida qo'lda tekshiriladi (`ops/go_live.ps1:455`).
