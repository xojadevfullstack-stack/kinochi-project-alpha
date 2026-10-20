# Sud-Texnik Ekspertizasi: 10_SCRAPER_AND_OPS.md
## Part 10: Scraper, Autopilot, Seed Ingestor va Operatsion Skriptlar Tahlili

### 1. Scraper va Autopilot Modullari Arxitekturasi
Loyiha doirasida tashqi O'zbek media kanallari va botlaridan (`uzmovi`, `asilmedia`, `animeelar`, `anitoob`) kontent yig'uvchi quyidagi tizimlar mavjud:

1. **`scraper/run_scraper.py` (Asosiy Scraper Manager)**:
   - Veb-saytlar HTML sahifalarini (`site_parser.py`) va Telegram botlarini (`telegram_grabber.py`) so'rov qiladi.
   - Yig'ilgan filmlar va seriallarni navbat fayliga (`scraper/scraper_queue.json`) yozadi.
   - Holatni (`uzmovi_current_page`, `asilmedia_current_page`, va h.k.) `scraper/scraper_state.json` da saqlaydi.
2. **`scraper/telethon_moderator_pipeline.py` (MTProto Userbot Pipeline)**:
   - Telethon orqali Telegram API ga ulanadi (`TELEGRAM_STRING_SESSION`).
   - `CreateForumTopicRequest` orqali superguruhda mavzular ochadi.
   - Videolarni yuklab, storage kanalga `client.send_file` orqali yuboradi.
   - Backendga `POST /scraper/upload-batch` orqali ma'lumotlarni uzatadi.
3. **`scraper/tmdb_top_ingestor.py` / `scripts/seed_ingestor.py` (TMDb Top Seed Ingestor)**:
   - TMDb API orqali eng yuqori reytingli 1000 ta film va 500 ta serial nomzodlarini oladi.
   - `seed_candidates` jadvaliga `status='discovered'` holatida yozadi.
   - `--search`: Mahalliy O'zbek manbalaridan (UzMovi, AsilMedia, AniToob) qidiradi va topilganlarni `matched` ga o'tkazadi.
   - `--enqueue --execute`: Nomzodlarni scraper navbatiga qo'shadi.

### 2. Telegram Xabarlarini Boshqaruvchi Barcha Chaqiruvlar (MTProto / Bot API)
`scraper/`, `scripts/` va `ops/` papkalarida Telegram bilan to'g'ridan-to'g'ri ishlovchi **193 ta chaqiruv** aniqlandi. Quyida ularning eng asosiylari keltirilgan:

| Skript / Modul | Fayl:Qator | Telegram Metodi | Maqsadli Kanal / Guruh | Vazifasi va Oqibati |
| :--- | :--- | :--- | :--- | :--- |
| `telethon_moderator_pipeline.py` | `scraper/telethon_moderator_pipeline.py:180` | `client(CreateForumTopicRequest(...))` | Superguruh (`AUTO_TOPIC_CHAT_ID`) | Serial yoki kino uchun yangi forum topic ochadi |
| `telethon_moderator_pipeline.py` | `scraper/telethon_moderator_pipeline.py:245` | `client.send_file(...)` | Storage Kanal (`STORAGE_CHANNEL_ID`) | Videoni storage kanalga yuklaydi |
| `migrate_all_movies_individual_topics.py` | `scripts/migrate_all_movies_individual_topics.py:120` | `client(CreateForumTopicRequest(...))` | Superguruh (`AUTO_TOPIC_CHAT_ID`) | Har bir kino uchun alohida forum topic yaratadi |
| `migrate_all_movies_individual_topics.py` | `scripts/migrate_all_movies_individual_topics.py:165` | `client.send_file(...)` | Superguruh yangi topiclari | Eski kanaldan videolarni yangi topiclarga nusxalaydi |
| `migrate_all_major_series.py` | `scripts/migrate_all_major_series.py:115` | `client(CreateForumTopicRequest(...))` | Superguruh (`AUTO_TOPIC_CHAT_ID`) | Katta seriallar uchun topic ochadi |
| `migrate_all_major_series.py` | `scripts/migrate_all_major_series.py:180` | `client.send_file(...)` | Superguruh serial topiclari | Serial qismlarini ketma-ket yuklaydi |
| `migrate_bleach.py` | `scripts/migrate_bleach.py:90` | `client.send_file(...)` | Superguruh Bleach topic | Bleach serial qismlarini yuklaydi |
| `migrate_kurtlar_pusu.py` | `scripts/migrate_kurtlar_pusu.py:85` | `client.send_file(...)` | Superguruh Kurtlar Vadisi topic | Kurtlar Vadisi qismlarini yuklaydi |
| `reset_media.py` | `ops/reset_media.py:60` | SQL TRUNCATE / DELETE | PostgreSQL Ma'lumotlar Bazasi | Barcha media jadvallarini tozalaydi |

### 3. Navbat, Holat va Karantin Fayllari (Runtime State Summary)
| Fayl Yo'li | Turi | Elementlar Soni | Hajmi | Joriy Holati va Mazmuni |
| :--- | :--- | :--- | :--- | :--- |
| `scraper/animeelar_catalog.json` | `dict` | 180 ta | 7316 bayt | Mahalliy diskda mavjud |
| `scraper/anitoob_catalog.json` | `dict` | 307 ta | 102426 bayt | Mahalliy diskda mavjud |
| `scraper/autopilot_v2/quarantine_items.json` | `dict` | 0 ta | 2 bayt | Mahalliy diskda mavjud |
| `scraper/scraper_queue.json` | `list` | 34 ta | 25288 bayt | Mahalliy diskda mavjud |
| `scraper/scraper_state.json` | `dict` | 15 ta | 450 bayt | Mahalliy diskda mavjud |
| `scraper/state.json` | `dict` | 0 ta | 2 bayt | Mahalliy diskda mavjud |

**Muhim Xulosalar (CONFIRMED)**:
1. `scraper/scraper_queue.json` da 34 ta navbatda turgan media elementi mavjud.
2. `scraper/anitoob_catalog.json` (307 ta element) va `scraper/animeelar_catalog.json` (180 ta element) anime kataloglari mavjud bo'lib, ular scraper tomonidan keshlab olingan.
3. AI agent tomonidan yozilgan o'nlab `migrate_*.py` skriptlari Telegram superguruhiga ommaviy video yuklaganda, fonda ishlab turgan `auto_index.py` ushbu xabarlarni parallel qabul qilib, bazani noto'g'ri bog'lanishlar bilan to'ldirib tashlagan.
