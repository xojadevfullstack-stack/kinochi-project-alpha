# Sud-Texnik Ekspertizasi: 13_TELEGRAM_TOOLS.md
## Part 13: Telegram Manbalari Haqiqati va Tekshiruv Vositalari

### 1. `enumerate_sources.py` Skripti va Undan Foydalanish
Loyiha doirasida `docs/INCIDENT_2026-10-17/enumerate_sources.py` nomli mutlaqo xavfsiz (Read-Only) Telethon skripti tayyorlandi.
- **Xususiyatlari**:
  - Telegram API ga faqat o'qish rejimida ulanadi.
  - Hech qanday xabar yubormaydi, forward qilmaydi, o'chirmaydi yoki tahrirlamaydi.
  - Telegram FloodWait (429) yuz berganda avtomatik ravishda `fwe.seconds + 2` soniya kutadi.
  - Superguruh forum mavzulari (topic ID, sarlavha, xabarlar soni, birinchi va oxirgi xabar sanasi) va Storage kanaldagi jami xabarlar sonini CSV faylga eksport qiladi.
- **Qo'llash (Faqat Operator Tomonidan)**:
  ```powershell
  $env:TELEGRAM_API_ID = "..."
  $env:TELEGRAM_API_HASH = "..."
  $env:TELEGRAM_STRING_SESSION = "..."
  $env:AUTO_TOPIC_CHAT_ID = "-1003847632555"
  $env:STORAGE_CHANNEL_ID = "-1003762157591"
  python docs/INCIDENT_2026-10-17/enumerate_sources.py --output docs/INCIDENT_2026-10-17/sources_truth.csv
  ```

### 2. Kodda Manba yoki Saqlash Deb Qaraladigan Barcha Chat Identifikatorlari (Sozlamalar)
| Sozlama Nomi (Setting Name) | Kodda Qayerda Ishlatiladi? | Vazifasi va Xususiyati |
| :--- | :--- | :--- |
| `AUTO_TOPIC_CHAT_ID` | `backend/app/core/config.py:85`, `bot/config.py:11`, `scraper/config.py:55` | **Tartiblangan Superguruh (Ordered Forum Supergroup)**. Har bir kino yoki serial uchun alohida forum mavzusi (topic) ochilishi mo'ljallangan yagona tartibli manba. |
| `STORAGE_CHANNEL_ID` | `backend/app/core/config.py:75`, `bot/config.py:10`, `scraper/config.py:54` | **Fayllar Saqlash Kanali (Storage Channel)**. Barcha video fayllar doimiy saqlanadigan va `bot.copy_message` qilinadigan yopiq kanal. Foydalanuvchilar to'g'ridan-to'g'ri ko'rmaydi, bot shu yerdan videoni foydalanuvchiga uzatadi. |
| `OLD_STORAGE` (Hardcoded in scripts) | `scripts/migrate_*.py` | **Eski Xom Saqlash Kanali (`-1003926001543`)**. Eski manbadan olingan xom videolar saqlangan va agent tomonidan yangi superguruhga ko'chirilgan manba. |
| `mandatory_channels` (DB table / API) | `backend/app/api/v1/channels.py`, `bot/middlewares/subscription_check.py` | **Majburiy Obuna Kanallari**. Botdan foydalanish uchun foydalanuvchi obuna bo'lishi shart bo'lgan kanallar ro'yxati. |
