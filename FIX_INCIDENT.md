# Incident Fix Protocol: 2026-10-17
**Filial (Branch)**: `incident-fix-2026-10-17`  
**Muhandis**: Senior Backend Engineer  
**Qoidalar**: Safe defaults (hech narsa avtomatik yozilmaydi), read-only manbalar, tarmoqqa ulanmaslik, sirlarni (.env) ochmaslik, testlar mock/fixture bilan to'liq yashil (green) bo'lishi shart.  

---

## Qarorlar Jurnali (Decisions Log)
- **2026-10-17 Qaror 1**: Barcha o'zgarishlar yangi ajratilgan `incident-fix-2026-10-17` filialida amalga oshiriladi. `main` filialiga to'g'ridan-to'g'ri tegilmaydi.
- **2026-10-17 Qaror 2**: `AUTO_CONTENT_ENABLED` global o'chirgich (kill switch) sifatida joriy etiladi (default `False`). U barcha media yozish yo'llarini (bot auto-index, scraper yuklash, seed ingestor, admin ommaviy import) to'sib qo'yadi.
- **2026-10-17 Qaror 3**: `AUTO_INDEX_DRY_RUN` (default `True`) qo'shiladi. Bu rejimda auto-index faqat qarorlarni log qiladi, lekin bazaga yozish amalga oshirilmaydi.
- **2026-10-17 Qaror 4**: `AUTO_INDEX_ALLOWED_CHAT_IDS` (default bo'sh ro'yxat) orqali faqat ruxsat berilgan chatlar va faqat `topic_id` mavjud xabarlar qayta ishlanadi. Mavzusiz xabarlar e'tiborsiz qoldiriladi.
- **2026-10-17 Qaror 5**: `by-source` qidiruvlarida noaniqliklarga (`first()`, `scalar_one_or_none()`) yo'l qo'yilmaydi. Bitta topic birdan ortiq ob'ektga yoki bir vaqtning o'zida ham kino ham serialga tegishli bo'lsa, qat'iyan rad etiladi (`ambiguous_topic`).
- **2026-10-17 Qaror 6**: Mavjud tarjima yoki qism videolarini yangisiga almashtirish (overwrite) qat'iyan taqiqlanadi. Bir xil `telegram_file_id` yoki `storage_channel_message_id` boshqa kontentga biriktirilgan bo'lsa, xatolik qayd etiladi.
- **2026-10-17 Qaror 7**: Admission gate `final_check` har bir auto_index yozuvida majburiy bo'ladi: media turi muvofiqligi, TMDb davomiyligi bilan taqqoslash (tolerantlik bilan) va fayllar bir xilligi tekshiriladi.
- **2026-10-17 Qaror 8**: `bot/handlers/trailer.py` dagi `show_alert` xatosi tuzatiladi va barcha callback handlerlar `finally` blokida `callback.answer()` chaqirishi ta'minlanadi.
- **2026-10-17 Qaror 9**: Bot klaviaturalaridagi callback_data bilan handler filterlari to'liq sinxronlashtiriladi va avtotest bilan tekshiriladi.
- **2026-10-17 Qaror 10**: `subscription_check.py` Telegram API xatolarida (kanal topilmasa yoki bot huquqi bo'lmasa) fail-open rejimida ishlaydi (foydalanuvchi bloklanmaydi).
- **2026-10-17 Qaror 11**: `run.py` da xatolik yutib yuborilmaydi, exponential backoff bilan qayta ishga tushirish va Render restart qilishi uchun non-zero chiqish kodi beriladi.
- **2026-10-17 Qaror 12**: `code_resolver.py` da noaniq sof raqamli ID qidiruvi olib tashlanadi, faqat prefiksli kodlar qo'llab-quvvatlanadi.
- **2026-10-17 Qaror 13**: Kesh tizimida in-memory xotira ham Redis bilan birga tozalanadi, admin endpointi `POST /api/v1/admin/cache/flush` qo'shiladi.

---

## Nazorat Ro'yxati (Checklist)

- [x] 1. KILL SWITCH (`AUTO_CONTENT_ENABLED` default False, `AUTO_INDEX_DRY_RUN` default True) - Commit: `93874c8`
- [x] 2. AUTO_INDEX ALLOWLIST (`AUTO_INDEX_ALLOWED_CHAT_IDS`, topic_id majburiy, log qarorlar) - Commit: `463b45d`
- [x] 3. EXACT LOOKUPS (`by-source` aniq chat_id+topic_id, ambiguous rad etish, `rejected_items`) - Commit: `4efaf75`
- [x] 4. NO OVERWRITES (mavjud video ustiga yozmaslik, fayl takrorlanishini rad etish) - Commit: `e66c5bb`
- [x] 5. GATE FOR AUTO_INDEX (`final_check` filtri, type consistency, duration vs TMDb runtime, bitta fayl bitta nomga) - Commit: `bad7f8b`
- [x] 6. TRAILER BUG (`bot/handlers/trailer.py` show_alert tuzatish, barcha callback handlerlarda finally callback.answer()) - Commit: `8ddf17b`
- [x] 7. CALLBACK COVERAGE (barcha callback_data test qoplamasi, nomlarni unifikatsiya qilish) - Commit: `bc0288b`
- [x] 8. SUBSCRIPTION MIDDLEWARE FAIL-OPEN (`subscription_check.py` TelegramBadRequest/TelegramForbiddenError da foydalanuvchini bloklamaslik) - Commit: `a2c2d17`
- [x] 9. BOT SUPERVISION (`run.py` exception maskingni olib tashlash, supervision & restart, `bot_alive` in /health, `BOT_DROP_PENDING_UPDATES`) - Commit: `dfc49d0`
- [x] 10. CODE RESOLVER (`code_resolver.py` faqat prefiksli kodlar, ambiguous numeric ID lookupni o'chirish) - Commit: `ca722a0`
- [x] 11. CACHE (`cache.py` in-memory + Redis flush, `POST /api/v1/admin/cache/flush` endpointi) - Commit: `157fcfe`
- [x] 12. TOOLING (`enumerate_sources.py` topic creation date, old channel message count, unit testlar) - Commit: `258b68b`
- [x] 13. DOCS (`docs/INCIDENT_2026-10-17/FIXES.md` before/after tahlili, sozlamalar va yoqish ketma-ketligi) - Commit: `7f43d28`
