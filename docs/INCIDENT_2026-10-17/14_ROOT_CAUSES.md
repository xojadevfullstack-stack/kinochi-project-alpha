# Sud-Texnik Ekspertizasi: 14_ROOT_CAUSES.md
## Part 14: Asosiy Sabablar (Root Causes), Xavfsizlik Tahlili va Ochiq Savollar

### 1. Har Bir Alomat Bo'yicha Asosiy Sabablar Tahlili (Ranked Root-Cause Hypotheses)

#### Alomat 1: Kontent Turlari (Kino / Serial / Anime) Aralashib Ketishi
- **1-Darajali Sabab (CONFIRMED)**: `bot/handlers/auto_index.py:520-532` dagi noto'g'ri marshrutlash tartibi.
  - Auto-index har bir kelgan xabar uchun avval `/series/by-source?chat_id={chat_id}&topic_id={topic_id}` ga murojaat qiladi.
  - `backend/app/infrastructure/db/repositories/series_repository.py:126-132` da agar `topic_id is None` bo'lsa, ushbu kanalga bog'langan **BIRINCHI SERIALNI** qaytaradi.
  - Oqibat: Tartibsiz kanaldan kelgan barcha kinolar va multfilmlar tasodifiy bitta serialning qismlari deb hisoblanib, seriallar jadvaliga yozilgan.
- **2-Darajali Sabab (CONFIRMED)**: Ma'lumotlar bazasida yagona media turi ustuni yo'qligi.
  - `movies` va `series` jadvallarida media turini (`movie` vs `series` vs `anime` vs `cartoon`) belgilovchi enum yoki discriminator ustun yo'q. Faqat `pages` (`page_movie`, `page_series`) orqali bog'lanadi. Migratsiya skriptlari esa ushbu bog'lanishlarni o'zboshimchalik bilan chalkashtirgan.

#### Alomat 2: Noto'g'ri Havolalar va Havolalar O'rniga Xatolik Chiqishi
- **1-Darajali Sabab (CONFIRMED)**: `bot/utils/code_resolver.py:124-172` dagi tekshiruv ketma-ketligi.
  - Agar kod sof raqamdan iborat bo'lsa (`cleaned_code.isdigit()`), resolver avval `movie_by_id`, keyin `series_by_id` ni qidiradi. Bir xil ID ga ega kino va serial bo'lsa, serialga berilgan havola ham kinoni ochib beradi.
- **2-Darajali Sabab (CONFIRMED)**: `publish_status` filtrlari joriy etilishi (`backend/app/infrastructure/db/query_filters.py:10`).
  - Barcha public endpointlar faqat `published` kontentni qaytaradi. Admission gate dan o'tmagan yoki `pending` qolgan media uchun backend 404 qaytaradi, bot esa `❌ Hech narsa topilmadi!` xatosini chiqaradi.

#### Alomat 3: Telegram Bot Tugmalarining Javob Bermasligi / Qotib Qolishi
- **1-Darajali Sabab (CONFIRMED BUG)**: `bot/handlers/trailer.py:87, 101, 106` dagi `TypeError` xatosi.
  - Kod: `await callback.message.answer("⚠️ Treyler topilmadi.", show_alert=True)`
  - `Message.answer` metodi `show_alert` parametrini qabul qilmaydi. Treyleri yo'q mediada tugma bosilganda dasturiy xatolik (exception) ro'y beradi, callback javobsiz qoladi va Telegram foydalanuvchisida 'soat' aylanib qotadi.
- **2-Darajali Sabab (CONFIRMED)**: `SubscriptionMiddleware` dagi bloklanish (`bot/middlewares/subscription_check.py:57-61`).
  - Agar bot kanalga admin bo'lmasa, `TelegramBadRequest` yuz beradi va middleware barcha foydalanuvchilarni obuna bo'lmagan deb hisoblab, bot funksiyalarini to'liq bloklab qo'yadi.

#### Alomat 4: Bot va Saytda Noto'g'ri Kontent Aks Etishi
- **1-Darajali Sabab (CONFIRMED)**: Next.js ISR keshi (`revalidate = 60`) va Redis keshi (`cache:movies:*`, TTL=300s).
- **2-Darajali Sabab (CONFIRMED)**: `backend/app/core/cache.py:12` dagi in-memory kesh (`_memory_cache`).
  - Tashqaridan Redis tozalanganda ham, FastAPI xotirasidagi in-memory kesh tozalanmaydi va 5 daqiqa davomida eski/buzilgan ma'lumotlarni tarqatishda davom etadi.

#### Alomat 5: ~1600 ta Yaroqsiz (Junk) Media Qatorlari Yaralishi
- **1-Darajali Sabab (CONFIRMED)**: AI agent tomonidan yozilgan 110 dan ortiq `scripts/migrate_*.py` skriptlarining Telegram superguruhiga ommaviy video yuklashi.
- **2-Darajali Sabab (CONFIRMED)**: `auto_index.py` ning ushbu xabarlar bilan parallel poygaga kirishishi (Race Condition).
- **3-Darajali Sabab (CONFIRMED)**: `AUTO_CONTENT_ENABLED` feature flagining kodda umuman tekshirilmasligi (O'lik Kill-Switch). Natijada xatolik boshlanganda ham auto-index to'xtamagan.

### 2. Sifat Nazorati (Admission Gate) Nega Buni To'xtata Olmadi?
`backend/app/core/admission_gate.py` tahlil qilindi:
1. **Admission Gate Nimani Tekshiradi?**:
   - Nom uzunligi (>= 2), yil (>= 1880), poster URL reachability, TMDb dublikatlari, til ('Asosiy' emasligi), fayl hajmi (<= 2GB).
2. **Admission Gate Nimani TEKSHIRMAYDI (Bo'shliqlar)?**:
   - **Video mazmuni va sarlavha mosligi**: Videoning ichida nima borligini tekshirmaydi.
   - **Davomiylik va TMDb runtime mosligi**: 2 daqiqalik videoni 2 soatlik to'liq metrajli filmga biriktirilsa ham qabul qiladi.
   - **Tur izchilligi (Type Consistency)**: Serial qismi kinoga, kino esa serialga biriktirilsa gate buni ajrata olmaydi.
   - **Fayllar takrorlanishi**: Bitta `telegram_file_id` 10 ta turli kinoga biriktirilsa ham gate to'xtatmaydi.
3. **ENG ASOSIYSI**: `bot/handlers/auto_index.py` va `scripts/migrate_*.py` Admission Gate'ni UMUMAN Chaqirmagan! Ular to'g'ridan-to'g'ri DB ga yoki `/link-video` endpointiga yozgan.

### 3. Deployment Drift: Render Muhiti Tekshiruvi
Loyiha egasi Render Dashboard'da quyidagi parametrlarni tekshirishi shart:
1. **Servis Holati**: Render Web Service to'xtatilganmi (`Suspended`)?
2. **Branch va Commit**: Render qaysi git commitini deploy qilgan (`git log -1` bilan solishtiring)?
3. **Muhit O'zgaruvchilari (Environment Variables)**:
   - `DATABASE_URL` (to'g'ri bazaga ulanganmi?)
   - `BOT_TOKEN`, `STORAGE_CHANNEL_ID`, `AUTO_TOPIC_CHAT_ID`, `BOT_API_SECRET`
   - `AUTO_CONTENT_ENABLED` (garchi kodda ulanmagan bo'lsa ham)

### 4. Aniq Labaratoriyada Tasdiqlanmagan Faktlar va Egasi Taqdim Etishi Kerak Bo'lgan Ma'lumotlar
R2 va R3 xavfsizlik qoidalariga rioya qilingani sababli, quyidagi faktlar jonli ravishda tasdiqlanmadi (UNKNOWN):
1. **Jonli Bazadagi Aniq Qatorlar Soni**: `$env:FORENSIC_DATABASE_URL` berilmagani uchun `SELECT count(*)` natijalari NOT-RUN.
   - *Talab qilinadi*: Neon 'broken-oct17' branch snapshot URI si (`$env:FORENSIC_DATABASE_URL`).
2. **Render Servisining Haqiqiy Loglari**: 2026-10-16 va 2026-10-17 kunlaridagi Render console loglari.
3. **Telegram Superguruh Mavzulari Haqiqati**: `enumerate_sources.py` ni xavfsiz muhitda yurgizib, hosil bo'lgan `sources_truth.csv` fayli.
