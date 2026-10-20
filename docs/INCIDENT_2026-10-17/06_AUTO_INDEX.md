# Sud-Texnik Ekspertizasi: 06_AUTO_INDEX.md
## Part 6: Telegram Auto-Index Mexanizmining Chuqur Tahlili (Deep Dive)

### 1. `bot/handlers/auto_index.py` Ishlash Mexanizmi
Ushbu modul Telegram kanallari va superguruhlariga tashlangan video fayllarni avtomatik ravishda ushlab, bazaga kiritish uchun mas'ul hisoblanadi.

#### A. Qaysi Chat va Topiclarni Tinglaydi?
- Handlerlar ro'yxatdan o'tishi (`bot/handlers/auto_index.py:588-595`):
  ```python
  @router.message(F.video | F.document)
  async def auto_index_message(message: Message, bot: Bot):
      await enqueue_video_message(message, bot)

  @router.channel_post(F.video | F.document)
  async def auto_index_channel(message: Message, bot: Bot):
      await enqueue_video_message(message, bot)
  ```
- **Tahlil (CONFIRMED)**: Hech qanday chat ID yoki topic ID filtri YO'Q! Bot a'zo bo'lgan va xabar ko'rish huquqiga ega bo'lgan **HAR QANDAY KANAL VA GURUH**dagi barcha video va hujjatlarni ushlab oladi.

#### B. Debounce va Batch Buffer Aggregator (`lines 486-586`)
- Har bir kelgan video `source_key = f"{chat_id}:{topic_id}"` bo'yicha buferga olinadi.
- `DEBOUNCE_IDLE_SECONDS = 4.0`: Oxirgi video kelganidan keyin 4 soniya jimlik bo'lsa, bufer qayta ishlanadi.
- `MAX_BATCH_WAIT_SECONDS = 25.0`: Maksimal yig'ish vaqti 25 soniya.
- Qayta ishlash `get_source_lock(chat_id, topic_id)` orqali manba bo'yicha ketma-ket (sequential) bajariladi.

#### C. 2-Bosqichli Serial Saqlash Mexanizmi (Reserve & Upload)
- **BOSQICH A (RESERVE, `lines 300-332`)**: Telegram network so'rovlaridan oldin, backendda `POST /series/seasons/{season_id}/reserve-episodes` orqali DB da qismlar raqami va `display_code` band qilinadi.
- **BOSQICH B (UPLOAD, `lines 360-468`)**: Video `STORAGE_CHANNEL_ID` ga `safe_copy_message_with_retry` orqali nusxalanadi, so'ng backendga `POST /series/episodes/{ep_id}/link-video` orqali bog'lanadi.

### 2. `/series/by-source` va `/movies/by-source` Qidiruv Mantiqi
`auto_index.py:520-532` qatorlarida manba bo'yicha qidiruv quyidagicha tuzilgan:
```python
# 1. Avval doim Series qidiriladi:
url = f"/series/by-source?chat_id={chat_id}"
if topic_id:
    url += f"&topic_id={topic_id}"
resp = await api_client.client.get(url)

# 2. Faqat 404 bo'lsagina Movie qidiriladi:
if resp.status_code == 404:
    movie_url = f"/movies/by-source?chat_id={chat_id}"
    if topic_id:
        movie_url += f"&topic_id={topic_id}"
    resp_movie = await api_client.client.get(movie_url)
```

#### Backend Repository So'rovlari Farqi (Kritik Kamchilik!):
1. **`SeriesRepository.get_series_by_source` (`backend/app/infrastructure/db/repositories/series_repository.py:119-132`)**:
   ```python
   stmt = select(SeriesModel)...join(SourceModel, SeriesModel.source_id == SourceModel.id).where(SourceModel.chat_id == chat_id)
   if topic_id is not None:
       stmt = stmt.where(SourceModel.topic_id == topic_id)
   result = await self.session.execute(stmt)
   return result.scalars().first()
   ```
   - Agar `topic_id` berilmasa (`topic_id is None`), so'rovda `SourceModel.topic_id` ga hech qanday shart qo'yilmaydi! Bazadagi ushbu `chat_id` ga ega bo'lgan **BIRINCHI SERIALNI** (tasodifiy tartibda) qaytaradi!
2. **`MovieRepository.get_by_source` (`backend/app/infrastructure/db/repositories/movie_repo.py:119-131`)**:
   ```python
   stmt = select(MovieModel)...where(MovieModel.source_chat_id == chat_id)
   if topic_id:
       stmt = stmt.where(MovieModel.source_topic_id == topic_id)
   else:
       stmt = stmt.where(MovieModel.source_topic_id.is_(None))
   result = await self.session.execute(stmt)
   model = result.scalar_one_or_none()
   ```
   - Kinolarda `topic_id` bo'lmasa qat'iy `source_topic_id IS NULL` tekshiriladi va agar bir nechta kino chiqsa `scalar_one_or_none()` 500 xato tashlaydi!

### 3. Muayyan Ssenariylar Bo'yicha Qadam-ba-qadam Tahlil
#### (a) Tartibsiz kanalda (topiclarsiz) video joylashtirilganda:
- `topic_id = None`. Auto-index `/series/by-source?chat_id={chat_id}` ni so'raydi.
- Backend ushbu kanalda mavjud bo'lgan birinchi serialni qaytaradi.
- **Natija (CONFIRMED)**: Tartibsiz kanaldagi har qanday kino yoki multfilm ushbu tasodifiy serialning navbatdagi qismi sifatida `episodes` va `episode_translations` jadvallariga yoziladi. Kino sifatida HECH QACHON tan olinmaydi!
#### (b) Serialga biriktirilgan topicda video joylashtirilganda:
- `/series/by-source?chat_id={chat_id}&topic_id={topic_id}` muvaffaqiyatli 200 qaytaradi.
- `process_series_batch` ishga tushadi, qism raqami aniqlanadi, storage kanalga ko'chiriladi va `episodes` jadvaliga yoziladi.
#### (c) Kinoga biriktirilgan topicda video joylashtirilganda:
- `/series/by-source` 404 qaytaradi. `/movies/by-source` 200 qaytaradi.
- `process_movie_message` ishga tushadi, video storage kanalga ko'chiriladi va `movie_translations` jadvaliga yoziladi.
#### (d) Hech qayerda ro'yxatdan o'tmagan topicda video joylashtirilganda:
- `/series/by-source` 404, `/movies/by-source` 404 qaytaradi.
- `if resp_movie.status_code == 404: return` (qator 531) -> Xabar jim tashlab yuboriladi. Hech narsa yozilmaydi.
#### (e) Ayni bir video ikki marta forward qilinganda:
- Agar sarlavhada qism raqami bo'lsa, `is_update=True` bo'lib, mavjud qism videosi yangilanadi.
- Agar sarlavhasiz yuborilsa, auto-index uni yangi qism (masalan, 2-qism) deb hisoblaydi va bitta video ikkita har xil qism sifatida yoziladi.
#### (f) Telegramda xabar tahrirlanganda yoki o'chirilganda:
- Auto-index faqat `F.video | F.document` xabarlarni tinglaydi. `edited_message` yoki `delete` hodisalari uchun handlerlar **UMUMAN MAVJUD EMAS**.
- **Natija (CONFIRMED)**: Telegramdagi tahrir yoki o'chirish bazaga umuman ta'sir qilmaydi, bazada eski ma'lumotlar qolaveradi.
#### (g) Sarlavhada `fasl`/`qism`/`season` so'zlari bo'lganda:
- `extract_season_num_from_caption` va `extract_episode_num_from_caption` regex orqali raqamlarni ajratib oladi.
- Agar film sarlavhasida (masalan, 'Forsaj 9-qism') bo'lsa, u serial deb o'ylanib, 9-qism qilib yoziladi.
#### (h) Topic ham kino, ham serial sifatida ro'yxatdan o'tgan bo'lsa:
- Kod har doim avval `/series/by-source` ni tekshirgani sababli, video har doim serial deb qayta ishlanadi. Kino tekshiruviga navbat yetib bormaydi.

### 4. `AUTO_CONTENT_ENABLED` yoki Kill-Switch Mavjudligi Tahlili
- **Tekshiruv Natijasi (CONFIRMED)**: **NOT FOUND**.
- `bot/handlers/auto_index.py` da `AUTO_CONTENT_ENABLED` yoki boshqa biror favqulodda to'xtatuvchi kalit (kill-switch) tekshiruvi mavjud emas.
- `git grep AUTO_CONTENT_ENABLED bot/` hech qanday natija bermadi.
- Bu shuni isbotlaydiki, bot ishlayotgan paytda har qanday video kelishi bilan u avtomatik indekslanib, bazani buzishda davom etgan.
