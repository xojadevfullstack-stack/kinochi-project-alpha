# Sud-Texnik Ekspertizasi: 08_CODES_AND_LINKS.md
## Part 8: Identifikatorlar, Kodlar va Havolalar (Codes and Deep Links) Tahlili

### 1. Kodlar Qanday Yaratiladi? (Code Generation Algorithms)
#### A. `movies.code` (Film Kori)
- **Fayl va Qator**: `backend/app/application/movies/service.py:15-24`
- **Algoritm**:
  ```python
  alphabet = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
  while True:
      code = shortuuid.ShortUUID(alphabet=alphabet).random(length=6)
      existing = await self.movie_repo.get_by_code(code)
      if not existing:
          return code
  ```
- **Xususiyatlari**: 6 ta belgi, noaniq harflarsiz (0, 1, I, O chiqarib tashlangan). Masalan: `5DSM32`, `47KF9F`.
- **Cheklov**: `movies.code` jadval darajasida `UNIQUE` qilib belgilangan.
- **To'qnashuv Xavfi (Collision)**: Unikallik faqat `movies` jadvalida tekshiriladi! `episodes.code` bilan to'qnashuv tekshirilmaydi.

#### B. `episodes.code` va `display_code` (Qism Kodlari)
- **Fayl va Qator**: `backend/app/infrastructure/db/repositories/series_repository.py:500-501`
- **Algoritm**:
  - `episodes.code`: `uuid.uuid4().hex[:8]` (8 ta o'n oltilik belgi).
  - `episodes.display_code`: `f"S{season.season_number}-CH{ep_num}"` (Masalan: `S1-CH1`, `S1-CH12`).
- **Xususiyatlari**: `display_code` foydalanuvchiga Telegramda va saytda ko'rsatiladi (`CH` = Chast / Qism).

#### C. `series.code` (Virtual Serial Kodi)
- **Fayl va Qator**: `backend/app/infrastructure/db/models/series.py:18`
- **KRITIK MA'LUMOT (CONFIRMED)**: `series` jadvalida `code` nomli ustun **UMUMAN MAVJUD EMAS**!
- Seriallar uchun kod har doim virtual ravishda `s_{id}` (yoki `s{id}`, `series_{id}`) tarzida hosil qilinadi.
- `bot/services/api_client.py:88-99` va `bot/utils/code_resolver.py:85-87` da `s_(\d+)` regexi orqali to'g'ridan-to'g'ri `series.id` (Primary Key) ajratib olinadi.

### 2. Havolalar va Deep-Linklar Qayerda va Qanday Yaratiladi?
| Joylashuvi | Yaratilayotgan Havola Formati | Ishlatiladigan ID | Qanday Qidiriladi (Resolver Mantiqi)? | Xatolik Xavfi |
| :--- | :--- | :--- | :--- | :--- |
| **Website Movie Page** (`website/app/movie/[code]/page.tsx:210`) | `https://t.me/{bot}?start={code}` | `movie.code` (masalan: `PT3BQB`) | Botda `resolve_and_send_content`: avval `movie_by_code`, so'ng `series_by_code` | Agar kino `published` bo'lmasa 404 beradi |
| **Website Series Page** (`website/app/series/[id]/page.tsx:320`) | `https://t.me/{bot}?start=s_{id}` | `series.id` (masalan: `s_30`) | Botda `resolve_and_send_content`: `s_(\d+)` regex orqali `series_by_id` | Agar serial `published` bo'lmasa 404 beradi |
| **Website Episode Link** (`website/app/series/[id]/page.tsx:340`) | `https://t.me/{bot}?start={ep.code}` | `episode.code` (uuid hex) | Botda `resolve_and_send_content`: `episode_by_code` | Serial `published` bo'lmasa 404 |
| **Bot Inline Search (Movie)** (`bot/handlers/search.py:272-273`) | Bot: `?start={code}`, Sayt: `/movie/{code}` | `movie.code` | Saytda Next.js `/movie/[code]` -> `/movies/code/{code}` | Agar serial kinolar jadvaliga tushib qolgan bo'lsa, sayt uni film deb ochadi |
| **Bot Inline Search (Series)** (`bot/handlers/search.py:254-255`) | Bot: `?start=s_{id}`, Sayt: `/series/{id}` | `series.id` | Saytda Next.js `/series/[id]` -> `/series/{id}` | Agar film seriallar jadvaliga tushib qolgan bo'lsa, 1-qism serial deb ochadi |
| **Magic Login Havolasi** (`bot/handlers/start.py:79`) | `{WEBSITE_URL}/?auth_token={token}` | Bir martalik JWT token | Sayt frontendida token qabul qilinib, sessiya ochiladi | Domenda localhost bo'lsa Telegram xato beradi |

### 3. Resolver To'qnashuvlari va Noto'g'ri Entiti Qaytarish Mexanizmi
`bot/utils/code_resolver.py:124-172` da turi aniq ko'rsatilmagan (prefiksiz) so'rovlar quyidagi tartibda tekshiriladi:
```python
# 1. Serial prefiksi tekshiriladi:
s_match = re.match(r'^s_?(\d+)$', cleaned_code, re.IGNORECASE)
if s_match: return await send_series_info(...)

# 2. Avval Kino kodi bo'yicha qidiriladi:
movie = await api_client.get_movie_by_code(cleaned_code)
if movie: return await send_movie_info(...)

# 3. Agar faqat raqam bo'lsa (masalan: '17'):
if cleaned_code.isdigit():
    # AVVAL KINO ID tekshiriladi:
    movie = await api_client.get_movie_by_id(int(cleaned_code))
    if movie: return await send_movie_info(...)
    # KEYIN SERIAL ID tekshiriladi:
    series = await api_client.get_series_by_id(int(cleaned_code))
    if series: return await send_series_info(...)
```

**Kritik Xavf (CONFIRMED)**:
- Agar foydalanuvchi yoki havola raqamli ID (masalan `15`) yuborsa va bazada `id=15` bo'lgan kino ham, `id=15` bo'lgan serial ham mavjud bo'lsa:
  - Resolver **HAR DOIM KINONI QAYTARADI**!
  - Serial hech qachon ochilmaydi.
- Agar media `publish_status != 'published'` bo'lsa, backend 404 qaytaradi va resolver `False` qaytarib, bot `Hech narsa topilmadi` deydi.
