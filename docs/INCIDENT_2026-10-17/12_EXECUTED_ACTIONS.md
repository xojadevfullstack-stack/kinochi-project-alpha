# Sud-Texnik Ekspertizasi: 12_EXECUTED_ACTIONS.md
## Part 12: Oxirgi 72 Soatda Bajarilgan Harakatlar Tahlili (Executed Actions Reconstructed)

### 1. Ekspert (Agent)ning Ushbu Sessiyadagi Harakatlari (Oxirgi 72 Soat)
| Harakat | Vaqt (Taxminiy) | Maqsad / Target | Holat | Isboti / Izoh |
| :--- | :--- | :--- | :--- | :--- |
| **Pre-flight Muhit Tekshiruvi** | 2026-10-17 04:04 | `FORENSIC_DATABASE_URL` vs `DATABASE_URL` | **CONFIRMED** | `FORENSIC_DATABASE_URL` o'rnatilmaganligi aniqlandi va R2 qoidasiga ko'ra bazaga ulanish to'xtatildi. |
| **Produksion Bazaga Ulanish** | - | Production DB | **NOT CONNECTED** | Ekspert biron marta ham ishlab chiqarish bazasiga ulanmadi yoki SQL yubormadi. |
| **Telegram Network Chaqiruvlari** | - | Telegram Bot API / Telethon | **NOT EXECUTED** | R3 qoidasiga ko'ra Telegram tarmog'iga hech qanday so'rov yuborilmadi. |
| **Fayllar Yaralishi** | 2026-10-17 04:05 - hozirgacha | `docs/INCIDENT_2026-10-17/`, `INCIDENT_PROGRESS.md`, `_forensics_tmp/` | **CONFIRMED** | Faqat Read-only hisobotlar va vaqtinchalik skriptlar yaratildi. |
| **Mavjud Kodni O'zgartirish** | - | Repository fayllari | **NONE** | R1 qoidasiga ko'ra hech bir mavjud fayl o'zgartirilmadi yoki o'chirilmadi.

### 2. Oldingi Seanslarda AI Agent Tomonidan Bajarilgan Ishlar Rekonstruksiyasi
Loyiha diskida (`scripts/`, `backups/`, `ops/logs/`) qoldirilgan izlar va untracked fayllar tahlili quyidagi faktlarni to'liq isbotlaydi:

#### A. 'Eski Manbadan Sog'lom Kontentni Ko'chirish' Vazifasi Qanday Bajarilgan?
1. **Manbalar**: Agent eski saqlash kanali (`OLD_STORAGE = -1003926001543`) dagi xabarlarni o'qigan.
2. **Telethon Skriptlari Yozilgan**: Agent loyiha ildizida 110 dan ortiq bir martalik migratsiya skriptlarini yaratgan (`scripts/migrate_all_movies_individual_topics.py`, `scripts/migrate_all_major_series.py`, `scripts/migrate_anime_series.py` va h.k.).
3. **Superguruhda Topiclar Ochish**: Skriptlar Telethon orqali `TARGET_SUPERGROUP = -1003847632555` superguruhiga ulanib, `CreateForumTopicRequest` orqali yuzlab yangi forum mavzularini ochgan.
4. **Videolarni Forward/Copy Qilish**: Eski kanaldan olingan video xabarlar ushbu yangi topiclarga ommaviy nusxalangan.

#### B. Falokatning Asosiy Sababi: Auto-Index Bilan Poyga (Race Condition)
- AI agent videolarni Telegram topiclariga nusxalayotgan vaqtda, **Telegram bot (`run.py` yoki `start_bot.bat`) fonda ishlab turgan**.
- `bot/handlers/auto_index.py` superguruhdagi har bir yangi video xabarni ushlab olgan.
- `auto_index.py` har bir xabar kelganda avval `/series/by-source?chat_id={chat_id}&topic_id={topic_id}` endpointiga so'rov yuborgan.
- Topic hali bazada kino sifatida to'liq ro'yxatdan o'tib ulgurmaganligi yoki tartibsiz xabarlar tufayli, auto-index kelgan videolarni:
  - Seriallar qismi deb qabul qilgan;
  - Bitta kinoning har xil bo'laklarini turli seriallarga biriktirib yuborgan;
  - Seriallarni kino deb qabul qilib, barcha qismlarini bitta film videosi ustiga qayta-qayta yozgan (overwrite qilgan);

#### C. Agentning Keyingi Tartibsiz Tuzatish Urinishlari
- Kontent aralashib ketganini ko'rgach, agent quyidagi skriptlarni yozib, qayta-qayta ishga tushirgan:
  - `scripts/fix_mismatched_movies.py`
  - `scripts/fix_mismatched_series.py`
  - `scripts/realign_all_posters.py`
  - `scripts/categorize_and_sort_pages.py`
- Ushbu skriptlar bazadagi `page_movie` va `page_series` bog'lanishlarini yanada chalkashtirib, taxminan **1600 ta yaroqsiz (junk) qatorlar** hosil bo'lishiga olib kelgan.
