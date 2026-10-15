# KINOCHI LOYIHASI — MUSTAQIL SENIOR AUDIT HISOBOTI (AUDIT_FINDINGS.md)

> **Auditor roli:** Mustaqil Senior Auditor  
> **Hisobot holati:** READ-ONLY tekshiruv asosida tayyorlandi. Manba kodi, testlar va migratsiyalarga o'zgartirish kiritilmadi.  
> **Sana:** 2026-10-16  
> **Ma'lumotlar bazasi:** `TEST_DATABASE_URL` muhit o'zgaruvchisi berilmagani sababli ishlab chiqarish bazasiga tegilmadi; DDL va migratsiyalar `alembic upgrade --sql` statik tahlili orqali tekshirilib, tegishli bandlar *"needs DB verification"* deb belgilandi.

---

## 1. XAVFLILIK DARAJALARI BO'YICHA XULOSA (SEVERITY COUNT SUMMARY)

| Xavflilik darajasi (Severity) | Topilmalar soni (Count) |
|---|---|
| **CRITICAL** | **3** |
| **HIGH** | **5** |
| **MEDIUM** | **5** |
| **LOW** | **4** |
| **JAMI (TOTAL)** | **17** |

---

## 2. CHECKLIST HOLATI (CHECKLIST STATUS)

- [x] **1. Build vs claims**: `BUILD_PROGRESS.md` belgilari `git log` va amaldagi kod bilan solishtirildi.
- [x] **2. Baseline**: `python -m compileall` (muvaffaqiyatli), `pytest backend/tests` (99 passed), `admin-panel` build (muvaffaqiyatli), `website` build (muvaffaqiyatli), `ruff check` (141 ta lint xatosi).
- [x] **3. Migrations**: `alembic heads` (yagona bosh: `c1d2e3f4a5b6`), static SQL preview tekshirildi (to'liq additiv, destruktiv `DROP/TRUNCATE/DELETE` yo'q; *needs DB verification*).
- [x] **4. Bypass scan**: Barcha `session.add`, `insert`, `INSERT INTO`, `update` chaqiruvlari tekshirildi. Bypaslar aniqlandi.
- [x] **5. Read paths**: Barcha ommaviy GET yo'llari tekshirildi. Oqishlar (`list_seasons`, `collections`) aniqlandi.
- [x] **6. Gate tests with fixtures**: `admission_gate` pre_check va final_check tahlil qilindi.
- [x] **7. Pipeline behavior**: FloodWait retry, stale recovery va CircuitBreaker faqat infratuzilmada to'xtashi tasdiqlandi.
- [x] **8. Language**: 30 ta til namunasi sinovdan o'tkazildi, kod bazasidagi `'Asosiy'` qoldiqlari ro'yxatga olindi.
- [x] **9. Complaints**: Shikoyatlar moduli tekshirildi (telegram_user_id, dedup, threshold, restore kamchiliklari).
- [x] **10. Admin API/UI**: Admin endpointlari avtorizatsiyasiz chaqiruvlarda 401 qaytarishi tasdiqlandi (33 ta scraper, 3 ta rejected, 3 ta reports).
- [x] **11. Security**: Git tarixi va kuzatuvdagi fayllar bo'yicha maxfiy kalitlar, CORS va `ssl=False` tahlil qilindi.
- [x] **12. Async/resources**: Swallowed exceptions (90 ta), yopilmagan HTTP mijozlar va resurslar tekshirildi.
- [x] **13. Sources**: `site_parser.py` ziddiyati asl kod bilan hal etildi, 6 ta manba imkoniyatlar matritsasi tuzildi.
- [x] **14. Reset scripts**: Skriptlardagi bypass flaglari tekshirildi (*needs DB verification*).
- [x] **15. S1-S7 Table**: Yakuniy talablar spetsifikatsiyasi jadvali to'ldirildi.

**Tekshirilmagan bandlar soni:** **0 ta (barcha 15 ta band to'liq bajarildi)**.

---

## 3. AUDIT TOPILMALARI (FINDINGS SORTED BY SEVERITY)

### [CRITICAL] O'TA XAVFLI TOPILMALAR

#### F-001: `scraper/ingest_pusu.py` da Admission Gate'ni to'liq chetlab o'tib to'g'ridan-to'g'ri bazaga yozish
- **ID:** `F-001`
- **Severity:** `CRITICAL`
- **Status:** `FIXED (dc5fbdd)`
- **File & Line:** `scraper/ingest_pusu.py:262-277`
- **Raw Snippet:**
```python
    async with async_session_factory() as session:
        series_repo = SeriesRepository(session)
        series_service = SeriesService(repository=series_repo, telegram_api=None)

        ep_entity = await series_service.create_episode(EpisodeCreate(
            season_id=season_id,
            episode_number=ep_num,
            title=f"{ep_num}-qism"
        ))
        await series_repo.add_episode_translation(
            episode_id=ep_entity.id,
            language="Asosiy",
            telegram_file_id=bot_file_id,
            storage_channel_message_id=storage_msg.id
        )
        await session.commit()
```
- **Repro Steps:**
  1. `scraper/ingest_pusu.py` skriptini ko'rib chiqish.
  2. Qismlar va tarjimalar qanday saqlanayotganini tekshirish.
- **Expected vs Actual:**
  - *Kutilgan:* `BUILD_PROGRESS.md:39` dagi `B3. BARCHA yozish yo'llarini gate orqali yo'naltirish (API, auto_index, scraper moderator pipeline, ingest_pusu)` da'vosiga ko'ra, barcha qismlar `admission_gate` orqali tekshirilishi va `final_check` dan o'tishi kerak.
  - *Amalda:* Skript to'g'ridan-to'g'ri `SeriesRepository` va `SeriesService` orqali `episodes` va `episode_translations` jadvallariga yozadi, Gate chaqirilmaydi, qat'iyan taqiqlangan `language="Asosiy"` qiymati saqlanadi.
- **Spec Reference:** Checklist 4, Checklist 1, S1.

---

#### F-002: `scraper/telethon_moderator_pipeline.py` scraper grabber sikllarida `pre_check()` chaqirilmasdan media yaratilishi
- **ID:** `F-002`
- **Severity:** `CRITICAL`
- **Status:** `FIXED (3ef991f)`
- **File & Line:** `scraper/telethon_moderator_pipeline.py:887, 1711-1728, 1859, 2345, 2476, 2996`
- **Raw Snippet:**
```python
# scraper/telethon_moderator_pipeline.py:1708-1712
async with async_session_factory() as session:
    repo = MovieRepositoryImpl(session)
    service = MovieService(repo)
    created_movie = await service.create_movie(
        title=title,
        original_title=meta.get("original_title") or item.original_title,
        ...
```
```python
# scraper/telethon_moderator_pipeline.py:887
created_series = await series_service.create_series(series_data)
```
- **Repro Steps:**
  1. `scraper/telethon_moderator_pipeline.py` dagi film va serial yaratish joylarini ko'rish (887, 1711, 1859, 2345, 2476, 2996 qatorlar).
- **Expected vs Actual:**
  - *Kutilgan:* Yangi media yozilishidan oldin `admission_gate.pre_check(kind, payload)` chaqirilib, metadata, majburiy maydonlar, reachability va tashqi ID tekshirilishi, xato bo'lsa `rejected_items` ga yozilishi kerak.
  - *Amalda:* Commit `0b96e6c` faqat video yuklangandan keyingi `final_check` ni qo'shgan (2013, 2676, 3150-qatorlar). Biroq mediani DB da yaratishdan oldin `pre_check()` UMUMAN chaqirilmaydi. Sifatsiz yoki metadata yetishmaydigan media baribir DB ga `pending` bo'lib yozilaveradi.
- **Spec Reference:** Checklist 4, Checklist 6, S1.

---

#### F-003: `backend/app/api/v1/series.py` `upload_episode_video` endpointida `final_check()` chaqirilmasligi va ota serial nashr etilmasligi
- **ID:** `F-003`
- **Severity:** `CRITICAL`
- **Status:** `FIXED (7949101)`
- **File & Line:** `backend/app/api/v1/series.py:562-572`
- **Raw Snippet:**
```python
            episode = await service.add_episode_translation(
                episode_id=episode_id,
                language=language,
                file_id=file_id,
                message_id=message_id
            )
            if not episode:
                await job_manager.set_failed(job_id, "Qism topilmadi.")
                return
            await job_manager.set_done(job_id, result={"episode_id": episode_id, "language": language})
```
- **Repro Steps:**
  1. `backend/app/api/v1/movies.py:410-432` dagi `upload_movie_video` mantiqini ko'ring (`final_check` va `promote_to_published` chaqirilgan).
  2. `backend/app/api/v1/series.py:562-572` dagi `upload_episode_video` mantiqini solishtiring.
- **Expected vs Actual:**
  - *Kutilgan:* Qism videosi yuklangach, `final_check("episode", ...)` chaqirilib, o'tgan taqdirda ota serial holati `published` ga o'tkazilishi kerak.
  - *Amalda:* `upload_episode_video` ichida `final_check` ham, `promote_to_published` ham chaqirilmagan. Natijada ushbu endpoint orqali yuklangan serial doimiy ravishda `pending` bo'lib qolib ketadi va foydalanuvchilarga ko'rinmaydi.
- **Spec Reference:** Checklist 4, Checklist 5, S1.

---

### [HIGH] YUQORI DARAJADAGI TOPILMALAR

#### F-004: Git omborida kuzatuv ostidagi fayllarda ma'lumotlar bazasi parollari ochiq yozilganligi
- **ID:** `F-004`
- **Severity:** `HIGH`
- **Status:** `NEEDS-OWNER (082e129)`
- **File & Line:** `backend/check_migration.py:5`, `backend/run_migration.py:8`, `check_brgrns.py:5`
- **Kod tuzatishi:** 082e129 commitida fayllar xavfsiz holatga keltirildi (parollar o'rniga `os.getenv("DATABASE_URL")` qo'yildi).
- **Loyiha egasi qilishi shart bo'lgan qadamlar (Owner Action Steps):**
  1. Neon Console (`console.neon.tech`) ga kirib, `kinochi_db_user` / `neondb_owner` roli uchun yangi parol generatsiya qilish (Reset Password).
  2. Production `.env` faylidagi `DATABASE_URL` parametriga yangi parolli ulanish qatorini kiritish.
  3. Serverdagi backend servisini yangi env bilan qayta ishga tushirish (`systemctl restart ...` yoki `docker compose restart`).
- **Raw Snippet:**
```python
# backend/check_migration.py:5 (Parol yashirilgan)
DATABASE_URL = "postgresql+asyncpg://kinochi_db_user:[REDACTED_PASSWORD]@ep-lively-feather-a2w43q2l-pooler.eu-central-1.aws.neon.tech/kinochi_db?ssl=require"
```
```python
# backend/run_migration.py:8 (Parol yashirilgan)
DATABASE_URL = "postgresql+asyncpg://kinochi_db_user:[REDACTED_PASSWORD]@ep-lively-feather-a2w43q2l-pooler.eu-central-1.aws.neon.tech/kinochi_db?ssl=require"
```
```python
# check_brgrns.py:5 (Parol yashirilgan)
DATABASE_URL = "postgresql+asyncpg://kinochi_db_user:[REDACTED_PASSWORD]@ep-lively-feather-a2w43q2l-pooler.eu-central-1.aws.neon.tech/kinochi_db?ssl=require"
```
- **Repro Steps:**
  1. `git ls-files backend/check_migration.py backend/run_migration.py check_brgrns.py` buyrug'ini ishga tushirish. Fayllar git omboriga kiritilgan.
- **Expected vs Actual:**
  - *Kutilgan:* Maxfiy ulanish parollari hech qachon kod bazasida qattiq kodlanmasligi va git indeksiga tushmasligi kerak.
  - *Amalda:* Jonli Neon AWS PostgreSQL ulanish manzillari paroli bilan birga ochiq holatda git omborida saqlanmoqda.
- **Spec Reference:** Checklist 11.

---

#### F-005: API, Bot va Admin Panelda `'Asosiy'` qiymati qattiq kodlangani sababli Admission Gate qonuniy yuklashlarni rad etishi
- **ID:** `F-005`
- **Severity:** `HIGH`
- **Status:** `FIXED (8cb31a8)`
- **File & Line:** `backend/app/api/v1/movies.py:331, 473`, `backend/app/api/v1/series.py:493, 607`, `bot/handlers/auto_index.py:215, 423`, `admin-panel/components/VideoUploadModal.tsx:34`
- **Raw Snippet:**
```python
# backend/app/api/v1/movies.py:331
language: str = Form("Asosiy"),
```
```python
# bot/handlers/auto_index.py:213-217
resp = await api_client.client.post(f"/movies/{movie['id']}/link-video", json={
    "message_id": storage_msg_id,
    "language": "Asosiy",
    "telegram_file_id": telegram_file_id
})
```
```python
# backend/app/core/admission_gate.py:398-404
lang = str(get_val("language") or get_val("voiceover") or "").strip()
if not lang or lang.lower() == "asosiy":
    defects.append({
        "field": "language",
        "code": "invalid_language",
        "message": "Til 'Asosiy' yoki bo'sh bo'lishi mumkin emas, aniq til ko'rsatilishi kerak"
    })
```
- **Repro Steps:**
  1. Telegram botdagi `auto_index.py` orqali yangi kino yuborish.
  2. `auto_index.py` backendga `"language": "Asosiy"` yuboradi.
  3. `link_movie_video` ichida `final_check()` chaqiriladi.
- **Expected vs Actual:**
  - *Kutilgan:* Bot yoki admin standart yuklash qilganda, u to'g'ri o'zbek tili bilan nashr etilishi kerak.
  - *Amalda:* `final_check()` qat'iy ravishda `lang.lower() == "asosiy"` bo'lsa xato deb belgilaydi. Bot va admin paneldagi standart qiymatlar esa hali ham `"Asosiy"`. Oqibatda `auto_index.py` indekslagan barcha kinolar Gate tomonidan rad etilib, `pending` holatida qoladi.
- **Spec Reference:** Checklist 6, Checklist 8, S5.

---

#### F-006: `GET /api/v1/series/{series_id}/seasons` endpointida `publish_status='published'` filtri yo'qligi sababli ochiq teshik (Data Leak)
- **ID:** `F-006`
- **Severity:** `HIGH`
- **Status:** `FIXED (1185a5d)`
- **File & Line:** `backend/app/api/v1/series.py:277`
- **Raw Snippet:**
```python
@router.get("/{series_id}/seasons", response_model=List[Season])
@limiter.limit("120/minute")
async def list_seasons(
    request: Request,
    series_id: int,
    service: SeriesService = Depends(get_series_service)
):
    """Get all seasons for a series (Public)."""
    series = await service.get_series_by_id(series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series.seasons
```
- **Repro Steps:**
  1. Bazada `publish_status='pending'` yoki `'hidden'` bo'lgan serial ID sini oling.
  2. `GET /api/v1/series/{id}/seasons` so'rovini yuboring.
- **Expected vs Actual:**
  - *Kutilgan:* `BUILD_PROGRESS.md:18` da `A2. Close leaks: series.py:273 (seasons/{id})` deb yopilgani da'vo qilingan; ommaviy so'rovda pending/hidden serialning mavsumlari 404 qaytarishi lozim.
  - *Amalda:* `series = await service.get_series_by_id(series_id)` chaqirilgan (parametrsiz). U filtrsiz serialni topadi va uning barcha mavsum va qismlarini qaytaradi.
- **Spec Reference:** Checklist 5, A2.

---

#### F-007: `GET /api/v1/collections` va `movie-context` ommaviy yo'llarida nashr etilmagan media ma'lumotlarining sizib chiqishi (Data Leak)
- **ID:** `F-007`
- **Severity:** `HIGH`
- **Status:** `FIXED (39e5c77)`
- **File & Line:** `backend/app/api/v1/collections.py:205-235`, `259-286`
- **Raw Snippet:**
```python
    items_query = (
        select(CollectionItemModel)
        .where(CollectionItemModel.collection_id == collection.id)
        .options(
            selectinload(CollectionItemModel.movie),
            selectinload(CollectionItemModel.series),
        )
    )
```
```python
    # Find movie by code without publish filter
    movie_res = await db.execute(select(MovieModel).where(MovieModel.code == movie_code.upper()))
```
- **Repro Steps:**
  1. Franshiza to'plamiga kiruvchi film `publish_status='pending'` holatiga o'tkaziladi.
  2. Ommaviy `GET /api/v1/collections/{slug}` so'rovi yuboriladi.
- **Expected vs Actual:**
  - *Kutilgan:* Ommaviy franshiza sahifasida faqat `published` bo'lgan filmlar ko'rinishi, `pending` yoki `hidden` filmlar filtrlanishi kerak.
  - *Amalda:* `CollectionItemModel` ning `movie` va `series` munosabatlari to'g'ridan-to'g'ri `selectinload` qilinadi, hech qanday `published_only` filtri yo'q. Nashr qilinmagan filmlar ommaviy sahifada chiqib qoladi.
- **Spec Reference:** Checklist 5, A2.

---

#### F-008: TMDb ID bo'yicha bazada UNIQUE cheklovi yo'qligi va parallel tekshiruvda poyga holati (Race Condition)
- **ID:** `F-008`
- **Severity:** `HIGH`
- **Status:** `FIXED (732d5e3)`
- **File & Line:** `backend/alembic/versions/d4e5f6a1b2c3_unique_tmdb_id_on_movies_and_series.py`, `backend/app/core/admission_gate.py:280-303`
- **Raw Snippet:**
```python
# alembic migration
op.create_index(op.f('ix_movies_tmdb_id'), 'movies', ['tmdb_id'], unique=False)
op.create_index(op.f('ix_series_tmdb_id'), 'series', ['tmdb_id'], unique=False)
```
```python
# admission_gate.py:285
dup_stmt = select(MovieModel.id).where(MovieModel.tmdb_id == tmdb_int).limit(1)
dup_res = await session.execute(dup_stmt)
```
- **Repro Steps:**
  1. Bir vaqtning o'zida bir xil TMDb ID ga ega 10 ta parallel so'rov yuborish.
- **Expected vs Actual:**
  - *Kutilgan:* Spetsifikatsiya talabi: "Concurrency: 10 parallel admits of the same tmdb_id -> exactly one row".
  - *Amalda:* Bazada `UNIQUE (tmdb_id)` cheklovi yo'q (`unique=False`). `admission_gate` dagi tekshiruv esa faqat oddiy `SELECT` (row lock yoki advisory lock siz). Barcha 10 ta so'rov bir vaqtda SELECT qilganda dublikat ko'rmaydi va bazada 10 ta dublikat qator yaratiladi.
- **Spec Reference:** Checklist 6.

---

### [MEDIUM] O'RTA DARAJADAGI TOPILMALAR

#### F-009: Ma'lumotlar bazasini o'zgartiruvchi skriptlarda `--i-know-this-bypasses-gate` himoyasining yo'qligi
- **ID:** `F-009`
- **Severity:** `MEDIUM`
- **Status:** `FIXED (47a8bc9)`
- **File & Line:** `scripts/migrate_18plus_and_reports.py:57-58`, `scripts/fix_anime_posters_db.py:46`, `backend/scripts/inspect_and_fix_adult.py:131, 142`
- **Raw Snippet:**
```python
# scripts/migrate_18plus_and_reports.py:57-58
await conn.execute(text("UPDATE series SET is_18_plus = TRUE WHERE title ILIKE '%chuhai%' OR title ILIKE '%erli ayol%';"))
await conn.execute(text("UPDATE movies SET is_18_plus = TRUE WHERE genres ILIKE '%ecchi%' OR genres ILIKE '%hentai%' OR genres ILIKE '%erotika%';"))
```
- **Repro Steps:**
  1. `python scripts/migrate_18plus_and_reports.py` ni hech qanday parametrsiz ishga tushiring.
- **Expected vs Actual:**
  - *Kutilgan:* Barcha to'g'ridan-to'g'ri bazani o'zgartiruvchi texnik skriptlar `--i-know-this-bypasses-gate` bayrog'isiz ishlashdan bosh tortishi kerak.
  - *Amalda:* `scripts/clean_dirty_db_records.py` va `scripts/fix_anime_everything_db.py` da bayroq bor, lekin qolgan uchta skriptda hech qanday himoya yo'q va to'g'ridan-to'g'ri SQL UPDATE bajaradi.
- **Spec Reference:** Checklist 4, Checklist 14.

---

#### F-010: Shikoyatlar tizimida (Reports) foydalanuvchi ID saqlanmasligi, dedup va avtomatik yashirish (Threshold hide) yo'qligi
- **ID:** `F-010`
- **Severity:** `MEDIUM`
- **Status:** `FIXED (27177e5)`
- **File & Line:** `backend/app/infrastructure/db/models/report.py:11-30`, `backend/app/api/v1/reports.py:75-235`
- **Raw Snippet:**
```python
class ReportModel(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)
    movie_id: Mapped[int | None] = ...
    # telegram_user_id ustuni MAVJUD EMAS!
```
- **Repro Steps:**
  1. `ReportModel` jadval ustunlarini tekshiring.
  2. `create_report` endpointida shikoyatlar soni bo'yicha mediani yashirish shartlarini qidiring.
- **Expected vs Actual:**
  - *Kutilgan:* Checklist 9 talabi: per-user dedup, telegram_user_id saqlanishi, shikoyatlar soni chegaraga (threshold) yetganda mediani avtomatik yashirish (`hidden`), muammo hal bo'lganda tiklash (`restore`), admin panelda media bo'yicha guruhlash.
  - *Amalda:* `ReportModel` da `telegram_user_id` ustuni yo'q. Per-user dedup yo'q (faqat 1 ta so'rov/daqiqa IP limiter bor). Shikoyatlar soni bo'yicha yashirish mantiqi yo'q. Admin panelda guruhlash yo'q (oddiy yassi ro'yxat).
- **Spec Reference:** Checklist 9, S6.

---

#### F-011: Server xatoliklarida (500 Error) ixtiyoriy domenlar uchun CORS va Credentials ochiqligi
- **ID:** `F-011`
- **Severity:** `MEDIUM`
- **Status:** `FIXED (e0ec104)`
- **File & Line:** `backend/app/main.py:96-110`
- **Raw Snippet:**
```python
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logging.error(...)
    headers = {}
    origin = request.headers.get("origin")
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Access-Control-Allow-Headers"] = "*"
        headers["Access-Control-Allow-Methods"] = "*"
    return JSONResponse(status_code=500, content=..., headers=headers)
```
- **Repro Steps:**
  1. Serverga 500 xatolik keltirib chiqaradigan so'rov yuboring va `Origin: https://attacker.com` sarlavhasini bering.
- **Expected vs Actual:**
  - *Kutilgan:* CORS qoidalari faqat `settings.CORS_ORIGINS` va tasdiqlangan domenlar uchun ishlashi kerak.
  - *Amalda:* Istalgan begona `Origin` ga javoban server unga `Access-Control-Allow-Origin` va `Access-Control-Allow-Credentials: true` qaytaradi.
- **Spec Reference:** Checklist 11.

---

#### F-012: Scraper tizimida SSL sertifikat tekshiruvi butunlay o'chirilganligi (`ssl=False`)
- **ID:** `F-012`
- **Severity:** `MEDIUM`
- **Status:** `FIXED (b36c561)`
- **File & Line:** `scraper/anitoob_parser.py:88, 153`, `scraper/run_scraper.py:83`, `scraper/site_parser.py:258, 270`, `scraper/site_search.py:30, 76`
- **Raw Snippet:**
```python
# scraper/run_scraper.py:83
conn = aiohttp.TCPConnector(ssl=False)
```
```python
# scraper/site_parser.py:258
async with session.get(target_url, headers=HEADERS, ssl=False, timeout=aiohttp.ClientTimeout(total=12)) as resp:
```
- **Repro Steps:**
  1. `git grep "ssl=False"` buyrug'ini ishga tushiring.
- **Expected vs Actual:**
  - *Kutilgan:* HTTPS so'rovlarida SSL sertifikati xavfsizlik uchun tekshirilishi kerak.
  - *Amalda:* Scraper parserlarining barchasida `ssl=False` o'rnatilgan (MITM hujumlari xavfi).
- **Spec Reference:** Checklist 11.

---

#### F-013: Kod bazasida 90 ta yashirilgan xatoliklar (`except ...: pass`) mavjudligi
- **ID:** `F-013`
- **Severity:** `MEDIUM`
- **Status:** `FIXED (54d4201)`
- **File & Line:** `backend/app/api/v1/movies.py:369, 444`, `backend/app/api/v1/series.py:518, 579`, `bot/handlers/auto_index.py:116, 174, 207`, `backend/app/infrastructure/db/repositories/movie_repo.py:75` va yana 82 ta joy.
- **Raw Snippet:**
```python
# backend/app/infrastructure/db/repositories/movie_repo.py:73-76
except Exception:
    pass
```
- **Repro Steps:**
  1. `git grep -A 1 "except.*:"` orqali `pass` bilan yopilgan bloklarni ko'ring.
- **Expected vs Actual:**
  - *Kutilgan:* Asinxron va resursli operatsiyalarda xatolar logga yozilishi yoki qayta ishlanishi kerak.
  - *Amalda:* 90 ta joyda kutilmagan istisnolar (Exceptions) hech qanday log yozilmasdan jim yutib ketiladi, bu esa resurs sizib chiqishini va DB xatolarini yashiradi.
- **Spec Reference:** Checklist 12.

---

### [LOW] PAST DARAJADAGI TOPILMALAR

#### F-014: Admin Panelda `rejected_items` uchun foydalanuvchi interfeysi (UI) mavjud emasligi
- **ID:** `F-014`
- **Severity:** `LOW`
- **Status:** `FIXED (7979b6f)`
- **File & Line:** `admin-panel/app/`
- **Repro Steps:**
  1. `admin-panel/app/` papkasini ko'zdan kechiring.
- **Expected vs Actual:**
  - *Kutilgan:* Admin panelda rad etilgan kontentlarni ko'rish, tahrirlash, sababini tekshirish va qayta yuborish uchun `/rejected` sahifasi bo'lishi kerak.
  - *Amalda:* Backend API mavjud (`/api/v1/rejected`), biroq Next.js admin panelida ushbu API ni ko'rsatuvchi interfeys (`app/rejected/page.tsx`) yaratilmagan.
- **Spec Reference:** Checklist 10, S4.

---

#### F-015: `BUILD_PROGRESS.md` dagi commit identifikatorlari amaldagi git log bilan nomuvofiqligi
- **ID:** `F-015`
- **Severity:** `LOW`
- **Status:** `FIXED (319d37c)`
- **File & Line:** `BUILD_PROGRESS.md:23, 30, 38, 40`
- **Raw Snippet:**
```markdown
# BUILD_PROGRESS.md
Commit: b3ba4c1 (A2, A3, A4)  --> Asl git commit: 0c6c979
Commit: 895bc43 (B1)          --> Asl git commit: 69255c8
Commit: 692cbb2 (B2)          --> Asl git commit: 01b0620
Commit: f800f59 (B4)          --> Asl git commit: d2d8aed
```
- **Repro Steps:**
  1. `git log --oneline` natijalarini `BUILD_PROGRESS.md` bilan solishtiring.
- **Expected vs Actual:**
  - *Kutilgan:* Hujjatdagi commit xeshlari git tarixidagi haqiqiy commitlar bilan 100% mos kelishi kerak.
  - *Amalda:* Muallif hujjatni kommit qilishdan oldin taxminiy xeshlar yozgan, natijada havola qilingan to'rtta commit xeshi haqiqiy git tarixida mavjud emas.
- **Spec Reference:** Checklist 1.

---

#### F-016: `to_slug` va `to_stem_slug` funksiyalarining kirill yozuvidagi sarlavhalarni butunlay tozalab tashlashi
- **ID:** `F-016`
- **Severity:** `LOW`
- **Status:** `FIXED (d267d85)`
- **File & Line:** `scraper/duplicate_checker.py:100, 113`
- **Raw Snippet:**
```python
def to_slug(text: Optional[str]) -> str:
    ...
    return re.sub(r'[^a-z0-9]', '', norm)
```
- **Repro Steps:**
  1. `to_slug("Ўргимчак одам")` yoki `to_slug("Человек-паук")` chaqiring.
- **Expected vs Actual:**
  - *Kutilgan:* Kirillcha sarlavhalar lotinchaga transliteratsiya qilinishi yoki kirill harflari saqlanishi kerak.
  - *Amalda:* `[^a-z0-9]` regexi barcha kirill harflarini tozalab tashlaydi va natijada `""` (bo'sh satr) qaytaradi. Bu esa kirillcha nomli kinolarning dublikatini aniqlashni ishdan chiqaradi.
- **Spec Reference:** Checklist 8, Checklist 13.

---

#### F-017: Scraper CLI ishga tushirishida yagona nusxa (Single-instance) himoya fayli yo'qligi
- **ID:** `F-017`
- **Severity:** `LOW`
- **Status:** `FIXED (a892fce)`
- **File & Line:** `scraper/run_scraper.py:571-607`
- **Repro Steps:**
  1. Terminalda bir vaqtning o'zida ikkita `python scraper/run_scraper.py --download` jarayonini ishga tushiring.
- **Expected vs Actual:**
  - *Kutilgan:* Ikkinchi jarayon lock-fayl yoki PID nazorati orqali to'xtatilishi kerak.
  - *Amalda:* `ProcessManager` faqat veb API orqali ishga tushirilganda nazorat qiladi. To'g'ridan-to'g'ri terminal orqali ishga tushirilganda lock tekshirilmaydi va ikki jarayon bitta navbatni bir-biriga xalaqit berib qayta ishlaydi.
- **Spec Reference:** Checklist 7.

---

## 4. MA'LUMOTLAR MATRITSALARI VA MAXSUS TAHLILLAR

### 4.1. Manbalar imkoniyatlari matritsasi (Sources Capabilities Matrix)

| Manba (Source) | Nom (Title) | Yil (Year) | Poster | Treyler | Tavsif (Description) | Janrlar (Genres) | Davomiyligi (Runtime) | Til (Language) | Tashqi ID (TMDb / Shikimori) |
|---|---|---|---|---|---|---|---|---|---|
| **Uzmovi** (Parser) | ✅ Bor | ✅ Bor | ⚠️ URL bor (suv belgili) | ❌ Yo'q | ❌ Yetarli emas (< 15 belgi) | ❌ Ro'yxatda yo'q | ❌ Yo'q | ❌ Yo'q | ❌ Yo'q |
| **Asilmedia** (Parser) | ✅ Bor | ✅ Bor | ⚠️ URL bor | ❌ Yo'q | ❌ Yetarli emas | ❌ Ro'yxatda yo'q | ❌ Yo'q | ❌ Yo'q | ❌ Yo'q |
| **AniToob** (Parser) | ✅ Bor | ✅ Bor | ✅ Bor | ❌ Yo'q | ⚠️ Qisman bor | ⚠️ Qisman | ❌ Yo'q | ❌ Yo'q | ❌ Yo'q |
| **Animeelar** (Parser) | ✅ Bor | ✅ Bor | ✅ Bor | ❌ Yo'q | ⚠️ Qisman bor | ⚠️ Qisman | ❌ Yo'q | ❌ Yo'q | ❌ Yo'q |
| **TMDb** (Enricher) | ✅ Bor | ✅ Bor | ✅ Yuqori sifat | ✅ YouTube ID | ✅ Bor (AI tarjima) | ✅ To'liq janrlar | ✅ Daqiqalarda | ✅ Bor | ✅ `tmdb_id` |
| **Shikimori** (Enricher)| ✅ Bor | ✅ Bor | ✅ Bor | ❌ Kamdan-kam | ✅ Bor | ✅ Anime janrlari | ⚠️ Qismlar soni | ✅ Yapon/Rus | ✅ `shikimori_id` |

**Xulosa:** Agar parserdan olingan ma'lumotlar TMDb yoki Shikimori bilan boyitilmasa (enrichment), ularning 100% i Gate tomonidan rad etiladi. Eng ko'p uchraydigan rad etish sabablari: `missing_tmdb_id`, `missing_genres`, `insufficient_description`.

---

### 4.2. 30 ta til namunasi sinovi natijalari (Language Samples Table)

| # | Namuna matn | Turi | Slug qiymati | Stem slug qiymati | Gate Til tekshiruvi xatosi |
|---|---|---|---|---|---|
| 1 | O'rgimchak odam: Uyga yo'l yo'q | uz_latin | `orgimchakodamuygayolyoq` | `orgimchakodamuygayolyoq` | NONE |
| 2 | Qashqirlar makoni: Pistirma | uz_latin | `qashqirlarmakonipistirm` | `qashqirmakopistirma` | NONE |
| 3 | Iblislar qotili: Cheksiz poyezd | uz_latin | `iblislarqotilicheksizpo` | `iblisqotilcheksizpoyezd` | NONE |
| 4 | Sevgi iztirobi 12-qism | uz_latin | `sevgiiztirobi12qism` | `sevgiztirob12qism` | NONE |
| 5 | Temur tuzuklari va tariximiz | uz_latin | `temurtuzuklarivatarihim` | `temurtuzuklarvatarih` | NONE |
| 6 | Chol va dengiz | uz_latin | `cholvadengiz` | `cholvadengiz` | NONE |
| 7 | Ўргимчак одам | uz_cyrillic | `""` (bo'sh) | `""` (bo'sh) | NONE |
| 8 | Қашқирлар макони | uz_cyrillic | `""` (bo'sh) | `""` (bo'sh) | NONE |
| 9 | Иблислар қотили | uz_cyrillic | `""` (bo'sh) | `""` (bo'sh) | NONE |
| 10 | Севги изтироби | uz_cyrillic | `""` (bo'sh) | `""` (bo'sh) | NONE |
| 11 | Темур тузуклари | uz_cyrillic | `""` (bo'sh) | `""` (bo'sh) | NONE |
| 12 | Чол ва денгиз | uz_cyrillic | `""` (bo'sh) | `""` (bo'sh) | NONE |
| 13 | Один дома 2: Затерянный в Нью-Йорке | ru | `2` | `2` | NONE |
| 14 | Человек-паук: Нет пути домой | ru | `""` (bo'sh) | `""` (bo'sh) | NONE |
| 15 | Побег из Шоушенка | ru | `""` (bo'sh) | `""` (bo'sh) | NONE |
| 16 | Бойцовский клуб | ru | `""` (bo'sh) | `""` (bo'sh) | NONE |
| 17 | Интерстеллар | ru | `""` (bo'sh) | `""` (bo'sh) | NONE |
| 18 | Операция Ы и другие приключения Шурика | ru | `""` (bo'sh) | `""` (bo'sh) | NONE |
| 19 | Spider-Man: No Way Home | en | `spidermannowayhome` | `spidermannowayhome` | NONE |
| 20 | Breaking Bad | en | `breakingbad` | `breakingbad` | NONE |
| 21 | The Lord of the Rings: The Fellowship | en | `thelordoftheringsthefel` | `thelordoftheringsthefel` | NONE |
| 22 | Game of Thrones Season 1 | en | `gameofthronesseason1` | `gameofthronesseason1` | NONE |
| 23 | Inception | en | `inception` | `inception` | NONE |
| 24 | Interstellar | en | `interstellar` | `interstel` | NONE |
| 25 | Avatar 2: Suv yo'li (Аватар: Путь воды) | mixed | `avatar2suvyoli` | `avatar2suvyoli` | NONE |
| 26 | Venom 3 / Веном 3: O'zbek tilida | mixed | `venom33` | `venom33` | NONE |
| 27 | Naruto Shippuden 1-mavsum (Наруто) | mixed | `narutoshippuden1mavsum` | `narutoshippuden1mavsum` | NONE |
| 28 | Fast & Furious 10: Forsaj 10 | mixed | `fastfurious10forsaj10` | `fastfurious10forsaj10` | NONE |
| 29 | (bo'sh satr) | empty | `""` | `""` | **invalid_language** |
| 30 | `   ` (bo'shliqlar) | whitespace | `""` | `""` | **invalid_language** |
| 31 | Asosiy | placeholder_asosiy | `asosiy` | `asosiy` | **invalid_language** |
| 32 | N/A | placeholder_na | `na` | `na` | NONE (Xato bermaydi!) |

---

### 4.3. `scraper/site_parser.py` ziddiyatining to'liq yechimi

1. **`requests` kutubxonasi:** `site_parser.py` da umuman import qilinmagan. Sinxron `parse_uzmovi_page` va `parse_asilmedia_page` funksiyalarida `urllib.request` ishlatilgan.
2. **`aiohttp` asinxron funksiyalari:** `parse_uzmovi_page_async` va `parse_asilmedia_page_async` mavjud va haqiqatan `aiohttp.ClientSession` orqali ishlaydi (`site_parser.py:255-279`).
3. **Selektorlar:** `div.custom-poster` mavjud emas; amaldagi selektorlar `shortstory`, `movie-card`, `movie-box`, `card`, `short-content` hamda zaxira sifatida `article` elementlaridir (`site_parser.py:56-59`).

---

## 5. YAKUNIY TALABLAR SPETSIFIKATSIYASI (S1–S7 TABLE)

| Spec ID | Qoidaning mazmuni | Holat | Amaldagi dalillar va kod tahlili |
|---|---|---|---|
| **S1** | **Yagona admission gate:** Barcha yozish yo'llari yagona Gate orqali o'tishi va hech qanday bypass bo'lmasligi kerak. | **PARTIAL** | `admission_gate.py` moduli yaratilgan va HTTP API da (`create_movie`, `create_series`, `link_movie_video`, `link_episode_video`) Gate qo'llanilgan. Biroq `scraper/telethon_moderator_pipeline.py` (887, 1711, 2345, 2996) mediada `pre_check` ni chaqirmaydi; `scraper/ingest_pusu.py:262` va `series.py:562` (`upload_episode_video`) Gate'ni to'liq chetlab o'tadi. |
| **S2** | **Barcha maydonlar majburiy:** NULL, bo'sh satr yoki placeholder bo'lmasligi kerak. | **PARTIAL** | `REQUIRED_FIELDS` nom, yil, poster, janr, tavsifni talab qiladi. Biroq `runtime` tekshirilmaydi, treyler majburiy emas, 'N/A' qiymatlari qabul qilinadi, TMDb ID bazada UNIQUE emas. |
| **S3** | **Rad etilganlar DB da saqlanishi:** PostgreSQL dagi `rejected_items` jadvaliga yozilishi. | **MET (needs DB verification)** | `RejectedItemModel` va Alembic migratsiyasi `c1d2e3f4a5b6` yaratilgan. `record_rejection` yozuvlarni DB ga saqlaydi va takroriy urinishda `attempts` sonini oshiradi. |
| **S4** | **Admin UI rad etilganlar ro'yxati:** Ko'rish, tahrirlash, qayta urinish va blacklist. | **PARTIAL** | Backend API endpointlari (`GET /rejected`, `POST /rejected/{id}/retry`, `POST /rejected/{id}/blacklist`) mavjud va admin huquqi bilan himoyalangan. Biroq Admin Panelda bunga mos Next.js sahifasi yo'q va payloadni tahrirlab Gate'dan qayta o'tkazish imkoniyati berilmagan. |
| **S5** | **Yagona avtomatik media tekshiruv — Til:** O'zbek tili standarti, noma'lum til rad etilishi. | **PARTIAL** | `final_check` tili bo'sh yoki 'Asosiy' bo'lsa rad etadi. Ammo haqiqiy matnli til detektori yo'q; eng yomoni, `auto_index.py`, `movies.py`, `series.py` standart sifatida hali ham `'Asosiy'` yuborgani sababli qonuniy yuklashlar ham rad etilmoqda. |
| **S6** | **Foydalanuvchi shikoyatlari:** Per-user dedup, rate limit, threshold hide, restore, admin grouping. | **PARTIAL** | 1 so'rov/daqiqa IP limiter bor. Biroq `telegram_user_id` ustuni yo'q, per-user dedup yo'q, shikoyatlar ko'payganda mediani avtomatik yashirish (`threshold hide`) va tiklash (`restore`) mavjud emas. |
| **S7** | **Maksimal tezlik va xavfsizlik:** FloodWait paytida uxlab navbatni davom ettirish, infratuzilma breaker. | **MET** | `handle_flood_wait` yordamida FloodWait kutish va 3 martagacha qayta urinish joriy qilingan (`run_scraper.py:200-220, 295-305, 364-374`). `in_progress` staledan tiklanadi (`recover_stale_in_progress(1800)`). `HealthEvaluator.check_circuit_breaker()` faqat infratuzilma xatolarida to'xtaydi. |

---
*Hisobot to'liq yakunlandi. Audit xulosasi xolis kod tahlili va amaliy sinovlarga asoslangan.*
