# Slice Report: 2026-11-25-make-webhook-meta-publisher

## What was done
1. `scraper/smm_publishers/meta_pub.py` ichiga umumiy `_post_to_make_webhook()` yordamchisi qo'shildi: `MAKE_WEBHOOK_URL` berilganda `InstagramReelsPublisher`, `MAKE_FACEBOOK_WEBHOOK_URL` berilganda `FacebookReelsPublisher` `video_url`, `caption`, `movie_code` va `platform` ni Make.com Custom Webhook'iga yuboradi.
2. `backend/tests/test_smm_external_publishers.py` da Make webhook muvaffaqiyati, `video_url` majburiyligi va HTTP xatolarini tekshiruvchi 2 ta TDD test yozildi (avval RED, keyin GREEN).
3. `STATE.md` va `docs/learned.md` yangilandi.

## Changed files
- `scraper/smm_publishers/meta_pub.py` - Added shared `_post_to_make_webhook()` and `MAKE_WEBHOOK_URL` / `MAKE_FACEBOOK_WEBHOOK_URL` support
- `backend/tests/test_smm_external_publishers.py` - Added 2 TDD tests for Make.com webhook dispatch and error handling
- `STATE.md`, `docs/learned.md` - Recorded verification evidence and Webhook Bridge pattern

## check output
```text
ruff check scraper/smm_publishers/meta_pub.py backend/tests/test_smm_external_publishers.py: All checks passed!
pytest (test_smm*.py, test_smart_enricher_regression.py, test_video_verifier.py): 72 passed, 2 warnings in 14.31s
pytest (bot/tests/): 115 passed in 7.97s
```

## Risks and unknowns
- Render'da `MAKE_WEBHOOK_URL` kiritilib, Make.com scenariysi `Active` (`ON`) qilinmaguncha Instagram hali eski Meta tokeniga urilaveradi.
- Facebook Page Reels uchun Instagram ilovasida "Share Reels to Facebook" avtomatik yoqilmasa (yoki `MAKE_FACEBOOK_WEBHOOK_URL` berilmasa), `facebook` holati alohida failed qoladi.

## Concept to explain to the user
- **Webhook Bridge Pattern**: Rasmiy ilova ochish SMS/blokga tushganda video faylni qayta yozmasdan, uning ochiq URL manzili va izohini tasdiqlangan partner webhook'iga (`Make.com`) uzatish orqali avtopost zanjirini saqlab qolish.
  - Analogy: Shaharga kirish ruxsatnomasi kutib o'tirmasdan, tayyor yukni litsenziyali kuryer omboriga tashlab o'tish — u esa egasiga topshiradi.

## Next step
- Foydalanuvchi Render Environment'ga `MAKE_WEBHOOK_URL` ni qo'shib, Make.com scenariyni `Active` (`ON`) qilgach jonli bitta Reels yuborib tekshirish.
