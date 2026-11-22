# Slice Report: 2026-11-23-smm-autopost-fixes-and-diagnostics

## What was done
1. `approve_smm_job` / `bot_approve_smm_job` (`publish_now=true`) uchun FastAPI `BackgroundTasks` darhol publish, `process_publish_job()` da allaqachon `published` bo'lgan tarmoqlarni qayta yubormaslik va TikTok `PUT upload_url` uchun `TransportError` qayta urinishi qo'shildi.
2. Render jonli `/api/v1/smm/progress` da `worker` import xatosi yashirilishi hamda `cv2` (`libglib2.0-0` / `sys.path`) bog'liqligi sabab `scraper.smm_worker` yuklanmasdan qolishi aniqlandi va ixtiyoriy `cv2` fallback + `repo_root` `sys.path` + aniq `last_error` qaytarish bilan tuzatildi.
3. Admin Panel `/smm` sahifasida Render worker holati hamda har bir `failed` tarmoq xatolik matni ko'rsatildi; TDD testlar, `STATE.md` va `docs/learned.md` yangilandi.

## Changed files
- `backend/app/api/v1/smm.py` - Immediate `BackgroundTasks` publish, `_ensure_repo_root_on_path`, non-swallowed `_get_worker_state_safe`
- `scraper/smm_worker.py` - `_WORKER_STATE` diagnostics and skip already-`published` platforms on retry
- `scraper/smm_publishers/youtube_tiktok_pub.py` - 2-attempt `TransportError` retry on TikTok `PUT upload_url`
- `scraper/smm_scene_scorer.py` & `scraper/video_verifier.py` - Graceful `cv2 = None` fallback when shared libs are absent
- `Dockerfile` - Install `libglib2.0-0` for OpenCV headless runtime
- `admin-panel/app/smm/page.tsx` - Live Render worker indicator and inline per-platform error box
- `backend/tests/test_smm_api.py`, `backend/tests/test_smm_worker.py`, `backend/tests/test_smm_external_publishers.py` - Unit tests for all fixes

## check output
```text
ruff check: All checks passed!
pytest (SMM + smart_enricher + video_verifier): 70 passed, 2 warnings in 11.00s
bot pytest (bot/tests/): 108 passed in 5.95s
admin-panel node --test: 7 passed, 0 failed
admin-panel tsc --noEmit & next build: Exit 0 (22/22 routes)
```

## Risks and unknowns
- Render envdagi `FACEBOOK_ACCESS_TOKEN` / `META_ACCESS_TOKEN` muddati tugagani (`20-Nov-26 PST`) sababli Meta Developer Portal'dan token yangilanmaguncha Facebook/Instagram Reels chiqmaydi.
- TikTok `unaudited_client` cheklovi tufayli postlar TikTok Inbox'ga tushadi (`PUBLIC_TO_EVERYONE` uchun TikTok App Audit kerak).

## Concept to explain to the user
- **Idempotent Per-Platform Retry & Non-Swallowed Import Errors**: Qayta urinishda muvaffaqiyatli chiqqan tarmoqlarni o'tkazib yuborish dublikat postlarni oldini oladi; tashxis endpointlari esa xatoni `None` qilib yashirmasdan sababini ochiq ko'rsatishi shart.
  - Analogy: 5 ta do'konga posilka yuborganda 2 tasi allaqachon olgan bo'lsa qayta yuborishda faqat qolgan 3 tasiga jo'natish; pochta mashinasi buzilsa ham "hammasi joyida" demasdan qayeri buzilganini dispetcherga xabar berish.

## Next step
- Render deploy yakunlangach `/api/v1/smm/progress` da `worker.running` va `last_error` ni tekshirish, hamda foydalanuvchiga Meta tokenlarini yangilash ro'yxatini berish.
