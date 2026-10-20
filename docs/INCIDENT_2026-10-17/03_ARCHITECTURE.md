# Sud-Texnik Ekspertizasi: 03_ARCHITECTURE.md
## Part 3: Runtime Arxitekturasi, Marshrutlash va Aloqa Qatlamlari

### 1. `run.py` Ishga Tushirilganda Nimalar Start Bo'ladi?
`run.py` bitta Python jarayoni va bitta asyncio event loop ichida ikkita yirik asinxron komponentni parallel ishga tushiradi (`asyncio.gather(run_api(), run_bot(), return_exceptions=True)`):

#### A. FastAPI Backend (`run_api()`)
- **Server**: `uvicorn.Server` (1 worker, asyncio loop, default port 8000).
- **Lifespan Startup Hook (`backend/app/main.py:30-84`)**:
  1. `keep_alive` fon vazifasi (Render muhitida uyquga ketmaslik uchun har 14 daqiqada `/health` ping).
  2. `init_redis_bg` fon vazifasi (`job_manager._redis.ping()` chaqiradi; agar xato bersa, tizim to'xtamaydi, in-memory keshga o'tadi).
  3. `engine ping` (`SELECT 1` bilan PostgreSQL bazasiga ulanish tekshiruvi).
- **FastAPI Middleware Qatlamlari**:
  - `SlowAPIMiddleware` (API so'rovlar sonini cheklovchi rate limiter).
  - `CORSMiddleware` (Next.js website va admin panel uchun ruxsat berilgan domenlar: `http://localhost:3000`, `3001` va `https://*.vercel.app`).
  - `generic_exception_handler` (Barcha 500 xatoliklarni ushlab, JSON formatida `Serverda kutilmagan xatolik yuz berdi` qaytaradi).
- **FastAPI Routerlari (20 ta router)**: `movies`, `categories`, `users`, `channels`, `auth`, `broadcasts`, `series`, `pages`, `sources`, `telegram_auth`, `reviews`, `statistics`, `content_lookup`, `scraper`, `collections`, `search`, `reports`, `audit`, `blacklist`, `series_subscriptions`, `rejected`.
- **Statik Fayllar**: `/uploads` -> `uploads/` papkasi.

#### B. Telegram Bot (`run_bot()`)
- **Dvigatel**: `aiogram 3.x` Dispatcher.
- **Polling vs Webhook**: **POLLING** rejimida ishlaydi (`bot.delete_webhook(drop_pending_updates=True)` va `dp.start_polling(bot)`).
  - **Xavf (CONFIRMED)**: Har safar bot qayta ishga tushganda `drop_pending_updates=True` tufayli Telegram serverida navbatda turgan barcha yangilanishlar (shu jumladan foydalanuvchi bosgan tugmalar va kanal xabarlari) o'chiriladi!

### 2. Aiogram Routerlari va Handlerlar Ketma-Ketligi (Handler Order Tahlili)
`bot/main.py` da routerlar quyidagi qat'iy tartibda ro'yxatdan o'tkazilgan:
1. `start_router` (`/start`, `/login`)
2. `check_sub_router` (`check_subscription` callback)
3. `catalog_router` (katalog callback va menyu xabarlari)
4. `reviews_router` (baho va izoh callbacklari va FSM matn xabari)
5. `search_router` (`F.text & ~F.text.startswith('/') & (F.chat.type == 'private')`)
6. `browsing_router` (`watch_m_*`, `watch_e_*`, `show_season_*`, `delete_msg`)
7. `episode_router` (`ep_prev:*`, `ep_next:*`, `series_info:*`, `back_to_series:*`, `main_menu`)
8. `translation_router` (`tr_*`)
9. `auto_index_router` (`F.video | F.document` message va channel_post)
10. `trailer_router` (`trailer_m_*`, `trailer_s_*`)
11. `history_router` (`history_complete_*`, `ignore_history`)
12. `recommendation_router` (`menu_random`, `rec_cat:*`)
13. `profile_router` (`menu_profile`, `/profile`)
14. `reports_router` (`report_m_*`, `report_s_*`, `report_e_*`, `rep_do:*`, `rep_cancel`)

**Handlerlar To'qnashuvi Tahlili (Catch-all check)**:
- `search_router` dagi `handle_search_query` matnli xabarlar uchun catch-all hisoblanadi. U `catalog_router` va `reviews_router` dan keyin ro'yxatdan o'tkazilgan. Agar foydalanuvchi FSM holatida bo'lmasa, har qanday matnli xabarni qidiruv so'rovi deb hisoblaydi.
- Callback_query larda global catch-all handler yo'q. Har bir router o'zining prefiksiga ega (`F.data.startswith(...)`).
- **Lekin diqqat**: `main_menu` callbacki `episode.py:77` da tutiladi, `menu_main` callbacki esa `catalog.py:63` da tutiladi! Callback nomlari bir-biriga o'xshash ammo farqli!

### 3. Middleware Qatlamlari: Bloklash va So'rovlarni Tashlab Yuborish Shartlari
#### A. `SubscriptionMiddleware` (`bot/middlewares/subscription_check.py`)
- Barcha `Message` va `CallbackQuery` hodisalariga tatbiq qilingan.
- Kanallar ro'yxati 60 soniyalik in-memory kesh bilan `api_client.get_active_channels()` dan olinadi.
- **Bloklash sharti**:
  1. Bot Telegram API orqali `bot.get_chat_member(chat_id, user_id)` ni tekshiradi.
  2. Agar foydalanuvchi statusi `left` yoki `kicked` bo'lsa -> BLOKLANADI.
  3. **KRITIK XUSUSIYAT**: Agar `TelegramBadRequest` yuz bersa (masalan, bot kanalga admin qilinmagan bo'lsa, kanal o'chirilgan bo'lsa yoki chat topilmasa), xatolik yutiladi va kanal majburiy obuna ro'yxatiga qo'shiladi! Natijada bot foydalanuvchiga obuna bo'lish tugmasini chiqaradi va uni **UMUMAN BOTDAN FOYDALANISHDAN BLOKLAYDI**!
  4. Foydalanuvchi ko'radigan xabar: `Botdan foydalanish uchun quyidagi kanal(lar)ga obuna bo'ling:` va `✅ Tekshirish` tugmasi.
- **Silent Drop**: Foydalanuvchi `check_subscription` tugmasini bosganda, agar hali ham obuna tasdiqlanmasa: `event.answer('Hali hamma kanallarga obuna bo'lmadingiz!', show_alert=True)` chiqadi va handler chaqirilmaydi.

#### B. `ThrottlingMiddleware` (`bot/middlewares/throttling.py`)
- Faqat `start_router`, `search_router`, `catalog_router`, `browsing_router` ga ulangan.
- Redis orqali har bir foydalanuvchiga cheklov qo'yadi (default: 30 so'rov / daqiqa).
- Cheklov oshganda foydalanuvchiga alert: `⚠️ Iltimos, biroz kuting! Juda ko'p so'rov yubordingiz.` ko'rsatiladi va so'rov tashlab yuboriladi.

### 4. Xizmatlararo Aloqa Arxitekturasi (Who Talks to Whom)
```
+----------------------------------------------------------------+
|                      TELEGRAM USERS                            |
+-------------------------------+--------------------------------+
                                |
                                v
+-------------------------------+--------------------------------+
|                   TELEGRAM BOT (aiogram 3)                     |
|  - listens to polling updates                                  |
|  - calls Backend via HTTP (api_client, X-Bot-Secret)           |
+-------------------------------+--------------------------------+
                                |
        +-----------------------+-----------------------+
        | HTTP (X-Bot-Secret)   | HTTP (Public/JWT)     | HTTP (Public/JWT)
        v                       v                       v
+-------+-----------------------+-----------------------+--------+
|                   FASTAPI BACKEND (Uvicorn)                    |
|  - 137 REST endpoints                                         |
|  - Admission Gate & Franchise Canon                            |
+-------+-----------------------------------------------+--------+
        |                                               |
        v                                               v
+-------+-----------------------+               +-------+--------+
|   PostgreSQL (AsyncPG)        |               | Redis Cache    |
|   - movies, series, episodes  |               | - 300s TTL     |
|   - translations, sources     |               | - in-memory fb |
+-------------------------------+               +----------------+
```

1. **Bot -> Backend**: `http://127.0.0.1:8000/api/v1` orqali `X-Bot-Secret` sarlavhasi bilan bog'lanadi.
2. **Website -> Backend**: Next.js Server Components va Client Components orqali `NEXT_PUBLIC_API_URL` ga public so'rovlar yuboradi.
3. **Admin Panel -> Backend**: Next.js admin frontend orqali JWT Bearer token bilan himoyalangan `/api/v1/auth`, `/api/v1/movies`, `/api/v1/series`, `/api/v1/scraper` ga ulanadi.
4. **Scraper / Autopilot -> Backend / DB**: Scraper ham backend REST API ga (`/api/v1/scraper/upload-batch`), ham to'g'ridan-to'g'ri PostgreSQL bazasiga (`DATABASE_URL`) ulanish imkoniyatiga ega.

### 5. Redis Kesh Arxitekturasi va Stale Data Xavfi
- **Kalit Shablonlari (Key Patterns)**:
  - `cache:movies:*` (filmlar ro'yxati va filtrlari, TTL=300s)
  - `cache:series:*` (seriallar ro'yxati va filtrlari, TTL=300s)
  - `cache:pages:*` (sahifalar va ularning filmlari, TTL=300s)
  - `cache:collections:*` (kolleksiyalar, TTL=300s)
  - `cache:search:*` (qidiruv natijalari, TTL=300s)
  - `tmdb:*` (TMDb kesh ma'lumotlari, TTL=86400s)
  - `tr:*` (Google Translate tarjimalari, TTL=2592000s)
  - `throttling:*` (foydalanuvchi so'rovlar limiti, TTL=60s)
- **In-Memory Fallback Xavfi (CONFIRMED)**:
  - `backend/app/core/cache.py:12` da `_memory_cache: dict` mavjud.
  - Agar admin yoki skript tashqaridan Redis keshini tozalasa (`redis-cli flushall` yoki `redis_flush_cache.py`), FastAPI jarayonining xotirasidagi `_memory_cache` TOZALANMAYDI!
  - Natijada, baza tozalangan yoki media holati `hidden` ga o'zgartirilgan bo'lsa ham, veb-sayt va botga 300 soniya davomida eski (mavjud bo'lmagan) ma'lumotlar uzatilib turishi mumkin.

### 6. Backend REST API Endpointlarining Asosiy Katalogi (137 ta endpointdan saralangan)
| Method | Path | Auth Turi | Fayl:Qator | Kimlar Murojaat Qiladi? |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/search` | Admin (JWT) | `content_lookup.py:23` | Bot, Website, Admin Panel |
| `GET` | `/api/v1/search` | Public | `movies.py:216` | Bot, Website, Admin Panel |
| `GET` | `/api/v1/search` | Public | `series.py:112` | Bot, Website, Admin Panel |