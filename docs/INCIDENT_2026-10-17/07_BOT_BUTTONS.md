# Sud-Texnik Ekspertizasi: 07_BOT_BUTTONS.md
## Part 7: Telegram Bot Barcha Tugmalari, Callbacklar va Aloqalar Tahlili

### 1. Telegram Bot Barcha Tugmalari (Buttons & Callbacks) Jadvali
| Tugma Matni (Text) | Callback Data yoki URL | Handler (Fayl:Qator) | Backend API Chaqiruvlari | Nima Qaytaradi? | 404 / 500 / Bo'sh bo'lganda nima yuz beradi? | Foydalanuvchi Nimani Ko'radi? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `▶ Ko'rish` | `watch_m_{code}` | `bot/handlers/browsing.py:14` | `GET /movies/code/{code}` | Kino video xabari | 404 bo'lsa xabar chiqadi | `⚠️ Bu kino topilmadi.` |
| `▶ Ko'rish (Qism)` | `watch_e_{code}` | `bot/handlers/browsing.py:28` | `GET /series/episodes/code/{code}` | Qism video xabari | 404 bo'lsa xabar chiqadi | `⚠️ Bu qism topilmadi.` |
| `{s_num}-Mavsum` | `show_season_{s_id}_{season_id}` | `bot/handlers/browsing.py:42` | `GET /series/{id}` | Fasl kartochkasi va qismlar | 404 bo'lsa `Bu fasl topilmadi` | Xatolik xabari |
| `🎬 Treyler` | `trailer_m_{code}` | `bot/handlers/trailer.py:81` | `GET /movies/code/{code}` | Treyler video/xabari | **CRASH (BUG!)**: `show_alert=True` in `Message.answer` | **Xatolik / Tugma javobsiz qotadi!** |
| `🎬 Treyler (Serial)` | `trailer_s_{id}` | `bot/handlers/trailer.py:93` | `GET /series/{id}` | Treyler video/xabari | **CRASH (BUG!)**: `show_alert=True` in `Message.answer` | **Xatolik / Tugma javobsiz qotadi!** |
| `⭐ Baholash` | `rate_m_{code}`, `rate_s_{id}` | `bot/handlers/reviews.py:32,42` | `GET /movies/code/{code}`, `GET /series/{id}` | 1-10 reyting tugmalari | 404 bo'lsa 'Kino topilmadi' | Alert xabari |
| `💬 Fikrlar` | `reviews_m_{code}`, `reviews_s_{id}` | `bot/handlers/reviews.py:62,105` | `GET /reviews/movie/{id}` | Sharhlar ro'yxati | Sharh bo'lmasa 'Hali fikrlar yo'q' | Matnli xabar |
| `⚠️ Xatolikni bildirish` | `report_m_{code}`, `report_s_{id}` | `bot/handlers/reports.py:22,40` | `GET /movies/code/{code}` | Shikoyat sabablari menyusi | 404 bo'lsa alert | Shikoyat inline menyusi |
| `📂 Katalog` | `menu_catalog` | `bot/handlers/catalog.py:54` | `GET /pages` | Bo'limlar ro'yxati (Kinolar, Seriallar, Anime...) | Sahifalar bo'sh bo'lsa standart menyu | Inline katalog |
| `🎬 Kinolar` | `catalog_all_movies` | `bot/handlers/catalog.py:109` | `GET /movies?publish_status=published` | Filmlar 1-sahifasi | Bo'sh bo'lsa 'Kinolar topilmadi' | 10 talik kinolar ro'yxati |
| `📺 Seriallar` | `catalog_all_series` | `bot/handlers/catalog.py:159` | `GET /series?publish_status=published` | Seriallar 1-sahifasi | Bo'sh bo'lsa 'Seriallar topilmadi' | 10 talik seriallar ro'yxati |
| `🎌/📂 {Page}` | `menu_page_{page_id}` | `bot/handlers/catalog.py:209` | `GET /pages/{id}/movies`, `/series` | Dinamik sahifa elementlari | Bo'sh bo'lsa 'Kontent topilmadi' | Sahifa elementlari |
| `🎲 Tavsiya` | `menu_random` | `bot/handlers/recommendation.py:13`| `GET /categories` | Janr tanlash menyusi | Kategoriya bo'lmasa xato | Janrlar inline tugmalari |
| `👤 Profil` | `menu_profile` | `bot/handlers/profile.py:111` | `GET /users/by-telegram/{id}/summary` | Foydalanuvchi ko'rish tarixi va stat | 404 bo'lsa default profil | Profil kartochkasi |
| `🔔 Obuna bo'lish` | `sub_series_{series_id}` | `bot/handlers/search.py:109` | `POST /series/{id}/subscribe` | Obuna holatini o'zgartiradi | 404/500 bo'lsa alert | Alert xabari |
| `❌ Yopish` | `delete_msg` | `bot/handlers/browsing.py:70` | Yo'q (Telegram API) | Xabarni o'chiradi | Xabar o'chmagan bo'lsa yutiladi | Xabar yo'qoladi |
| `✅ Tekshirish` | `check_subscription` | `bot/handlers/check_sub.py:7` | `GET /channels/active`, `bot.get_chat_member` | Obunani qayta tekshirish | To'liq obuna bo'lmasa alert | `Hali hamma kanallarga obuna bo'lmadingiz!` |

### 2. `publish_status` Filtrlari Kiritilgandan So'ng Javoblar O'zgarishi (Root Cause Signal!)
1. **2026-10-15 sanasidagi o'zgarish (CONFIRMED)**:
   - Backendda barcha public endpointlar (`/movies`, `/movies/{id}`, `/movies/code/{code}`, `/series`, `/series/{id}`, `/series/episodes/code/{code}`) faqat `publish_status = 'published'` bo'lgan qatorlarni qaytaradigan qilindi.
   - Agar media `pending`, `draft`, `hidden` yoki `rejected` holatida bo'lsa:
     - ID yoki Code bo'yicha so'rovlar: **HTTP 404 Not Found** qaytaradi.
     - Ro'yxat va Qidiruv so'rovlari: **Bo'sh ro'yxat (`items: []`, `total: 0`)** qaytaradi.
2. **Bot Handlerlarining 404 ga Munosabati**:
   - `bot/handlers/browsing.py:18-21`: `api_client.get_movie_by_code(code)` 404 olganda `None` qaytaradi. Handler foydalanuvchiga: `⚠️ Bu kino topilmadi.` deb javob beradi.
   - `bot/handlers/start.py:32-35`: `/start <code>` kelganda `resolve_and_send_content` 404 olganda `False` qaytaradi. Handler foydalanuvchiga: `❌ Hech narsa topilmadi!` deb javob beradi.
   - **Natija (CONFIRMED)**: Baza bo'shatilib, qayta import qilinganda admission gate dan o'tmagan yoki `publish_status='pending'` bo'lib qolgan barcha 1600 ta media uchun foydalanuvchi tugmani bosganda 'Topilmadi' xatoligi chiqadi va tugmalar javob bermayotgandek tuyuladi!

### 3. Aniqlangan Kritik Kod Xatolari (Confirmed Bugs in Bot)
1. **`bot/handlers/trailer.py:87, 101, 106` da `TypeError` (CONFIRMED BUG)**:
   ```python
   # bot/handlers/trailer.py:87
   await callback.message.answer("⚠️ Treyler topilmadi.", show_alert=True)
   ```
   - `Message.answer()` metodi `show_alert` parametrini qabul qilmaydi (`show_alert` faqat `CallbackQuery.answer()` ga tegishli).
   - Oqibat: Treyleri bo'lmagan har qanday kino yoki serialda '🎬 Treyler' tugmasi bosilganda Python `TypeError` tashlaydi, Telegram 'soat' aylanib qotadi va foydalanuvchiga hech narsa ko'rinmaydi.
2. **Callback Nomlaridagi Noaniqlik**:
   - `catalog.py:63` da `F.data == 'menu_main'` kutiladi.
   - `episode.py:77` da `F.data == 'main_menu'` kutiladi.
   - `info_sender.py` va `inline.py` turli joylarda `menu_catalog` va `back_to_catalog` dan foydalanadi.
3. **Yutilgan Xatoliklar (Silently Swallowed Exceptions)**:
   - `bot/services/api_client.py:45-49`: `get_movie_by_code` da har qanday tarmoq xatosi logga yoziladi, lekin funksiya `None` qaytaradi, bot esa 'Kino topilmadi' deydi (aslida backend 500 yoki connection error bergan bo'lishi mumkin).
