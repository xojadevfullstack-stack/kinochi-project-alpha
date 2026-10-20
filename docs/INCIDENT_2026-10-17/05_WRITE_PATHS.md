# Sud-Texnik Ekspertizasi: 05_WRITE_PATHS.md
## Part 5: Barcha Ma'lumot Yozish Yo'llari (Write Paths) Tahlili

### 1. Yozish Yo'llarining Umumiy Xaritasi
Loyiha kodida ma'lumotlar bazasiga (`movies`, `series`, `seasons`, `episodes`, `translations`, `categories`, `pages`, `reports`, `rejected_items`, `seed_candidates`) yozish amalga oshiriladigan 5 ta asosiy mustaqil mexanizm aniqlandi:

1. **Backend REST API & Admission Gate Qatlami** (`backend/app/api/v1/`, `backend/app/core/admission_gate.py`)
2. **Telegram Auto-Index Qatlami** (`bot/handlers/auto_index.py`)
3. **Scraper & Telethon Moderator Qatlami** (`scraper/`, `scraper/autopilot_v2/`)
4. **TMDb Top Seed Ingestor** (`scraper/tmdb_top_ingestor.py`, `scripts/seed_ingestor.py`)
5. **AI Agent tomonidan yaratilgan Ad-hoc Migratsiya Skriptlari** (`scripts/migrate_*.py`, `scripts/fix_*.py`)

### 2. Yozish Yo'llarining Qiyosiy Tahlil Jadvali
| Yozish Yo'li (Write Path) | Fayl va Qator | Trigger / Sabab | Admission Gate Tekshiruvi | Tur (Type) Qanday Aniqlanadi? | Kod (Code) Qanday Yaratiladi? | `source_*` Maydonlariga Nima Yoziladi? | Boshlang'ich `publish_status` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Movie Repo Create** | `backend/app/infrastructure/db/repositories/movie_repo.py:46` | Admin API, Scraper, yoki Seed orqali | **BOR** (`pre_check` chaqirilsa) | Qat'iy `movie` (`movies` jadvaliga yoziladi) | `generate_unique_code()` (6-8 belgili tasodifiy alfanumerik) | `source_chat_id`, `source_topic_id`, `source_type` | `pending` (gate promote qilsa `published`) |
| **2. Series Repo Create** | `backend/app/infrastructure/db/repositories/series_repository.py:147` | Admin API, Scraper, yoki Seed orqali | **BOR** (`pre_check` chaqirilsa) | Qat'iy `series` (`series` jadvaliga yoziladi) | `s_{id}` yoki alfanumerik | `source_id` (FK -> `series_sources`), `source_type` | `pending` (gate promote qilsa `published`) |
| **3. Episode Repo Create** | `backend/app/infrastructure/db/repositories/series_repository.py:233` | Auto-index yoki Admin API | **QISMAN** (faqat parametrlar tekshiriladi) | Qat'iy `episode` | `code`: `ep_{uuid[:8]}` yoki tasodifiy, `display_code`: `S{season}-CH{ep}` | `source_message_id` | Bog'liq mavsum/serial statusiga bo'ysunadi |
| **4. Movie Translation Add** | `backend/app/infrastructure/db/repositories/movie_repo.py:95` | Auto-index yoki Scraper upload | **QISMAN** (video file_id) | Parent `movie_id` ga bog'lanadi | Mavjud emas | `telegram_file_id`, `storage_channel_message_id` | - |
| **5. Episode Translation Add** | `backend/app/infrastructure/db/repositories/series_repository.py:270` | Auto-index yoki Scraper upload | **QISMAN** (video file_id) | Parent `episode_id` ga bog'lanadi | Mavjud emas | `telegram_file_id`, `storage_channel_message_id` | - |
| **6. Auto-Index Movie Flush** | `bot/handlers/auto_index.py:280` | Telegram kanal/topic ga video tashlanganda | **YO'Q (BYPASSED!)** | `/movies/by-source` javobiga tayanadi | Mavjud kod saqlanadi | `source_chat_id`, `source_topic_id` | O'zgartirilmaydi |
| **7. Auto-Index Series Flush** | `bot/handlers/auto_index.py:420` | Telegram kanal/topic ga video tashlanganda | **YO'Q (BYPASSED!)** | `/series/by-source` javobiga tayanadi | `display_code`: `S{s}-CH{e}` | `source_message_id` | O'zgartirilmaydi |
| **8. Scraper Upload-Batch** | `backend/app/api/v1/scraper.py:280` | Autopilot yoki Scraper pipeline | **TO'LIQ BOR** (`pre_check` + `final_check`) | Scraper payload'idagi `media_type` ga qarab | `generate_unique_code()` | `source_chat_id`, `source_type` | `pending` -> `published` |
| **9. Ad-hoc Script: Migrate Movies** | `scripts/migrate_all_movies_individual_topics.py` | AI Agent qo'lda ishga tushirgan | **MUTLAQO YO'Q (GATE BYPASSED)** | Skript ichidagi ro'yxat / regex orqali | Yangi kod yoki eski kod | Yangi yaratilgan superguruh topic ID | To'g'ridan-to'g'ri `published` |
| **10. Ad-hoc Script: Migrate Series** | `scripts/migrate_all_major_series.py` | AI Agent qo'lda ishga tushirgan | **MUTLAQO YO'Q (GATE BYPASSED)** | Skript ichidagi ro'yxat / hardcoded | Hardcoded yoki ketma-ket | Supergroup topic ID | To'g'ridan-to'g'ri `published` |
| **11. Reset Media Script** | `ops/reset_media.py` | Operator / Agent tomonidan bazani tozalash | N/A | Barcha jadvallarni tozalaydi | N/A | N/A | Barcha qatorlar o'chiriladi |

### 3. Kod Snippetlari va Yozish Joylari Dalillari (Evidence)
#### A. Auto-Index Admission Gate'ni Chetlab O'tishi (CONFIRMED)
`bot/handlers/auto_index.py` da xabarlar kelganda to'g'ridan-to'g'ri backend API ga POST yuboriladi va unda `pre_check` yoki `final_check` chaqirilmaydi:
```python
# bot/handlers/auto_index.py:315-325
# Video nusxalangandan so'ng to'g'ridan-to'g'ri tarjima biriktiriladi:
resp = await api_client.client.post(
    f"/movies/{movie['id']}/translations",
    json={
        "language": language,
        "telegram_file_id": file_id,
        "storage_channel_message_id": copied_msg.message_id,
    }
)
```

#### B. Tartibsiz Kanaldan Kelgan Videolarni Serial Qilib Qabul Qilinishi (CONFIRMED)
`bot/handlers/auto_index.py` da dastlab `/series/by-source` tekshiriladi:
```python
# bot/handlers/auto_index.py:520-530
url = f"/series/by-source?chat_id={chat_id}"
if topic_id:
    url += f"&topic_id={topic_id}"
resp = await api_client.client.get(url)

if resp.status_code == 404:
    # Faqat 404 bo'lsagina Movie qidiriladi!
    movie_url = f"/movies/by-source?chat_id={chat_id}"
```
`backend/app/infrastructure/db/repositories/series_repository.py:119-132` da esa agar `topic_id is None` bo'lsa:
```python
stmt = select(SeriesModel)...join(SourceModel, SeriesModel.source_id == SourceModel.id).where(SourceModel.chat_id == chat_id)
if topic_id is not None:
    stmt = stmt.where(SourceModel.topic_id == topic_id)
result = await self.session.execute(stmt)
return result.scalars().first()
```
**Xulosa**: Tartibsiz kanaldan (`topic_id` yo'q bo'lgan) har qanday video tashlanganda, agar ushbu `chat_id` bitta bo'lsa ham serialga ulangan bo'lsa, backend ushbu serialni qaytaradi va barcha kinolar ushbu tasodifiy serialning qismlari sifatida bazaga yoziladi!

#### C. Ad-hoc Migratsiya Skriptlari Tomonidan To'g'ridan-To'g'ri Bazaga Yozish (CONFIRMED)
`scripts/migrate_all_movies_individual_topics.py` da Telegramdan olingan xabarlar hech qanday tekshiruvsiz topiclarga copy qilingan:
```python
# scripts/migrate_all_movies_individual_topics.py:180-210
# AI agent tomonidan yozilgan skript Telegram orqali xabarlarni supergroup topiclariga
# ommaviy nusxalagan va auto-index bularni real vaqt rejimida qayta ishlab bazani ifloslantirgan.
```
