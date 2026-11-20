# Slice Report: 2026-11-20-smm-tiktok-and-cycle1-hook

## What was done
1. TikTok Sandbox OAuth (`code` -> `TIKTOK_REFRESH_TOKEN` & `TIKTOK_ACCESS_TOKEN`) `backend/.env` ga saqlandi; Direct Post `403 unaudited_client_can_only_post_to_private_accounts` cheklovida akkauntni Private qilmasdan `/v2/post/publish/inbox/video/init/` (`200 OK`) ga avtomatik o'tish va aniq xato nomi (`type(exc).__name__`) qaytarish qo'shildi.
2. Cycle 1 -> Cycle 2 bog'lanishi (`maybe_enqueue_smm_for_movie`) `SMM_AUTOPILOT_ENABLED` va `db.begin_nested()` savepoint izolyatsiyasi bilan `scraper/telethon_moderator_pipeline.py` dagi 3 ta kino nashr nuqtasiga ulandi.
3. `Dockerfile` ga `ffmpeg` va `fonts-dejavu-core` qo'shildi; `ruff`, `alembic heads`, `test_alembic.py` + barcha `test_smm_*.py`, hamda `admin-panel` `tsc --noEmit` + `next build` muvaffaqiyatli tekshirildi.

## Changed files
- `scraper/smm_publishers/youtube_tiktok_pub.py` - TikTok `inbox/video/init/` fallback, `_prefer_explicit_token` va bo'sh `str(exc)` o'rniga class nomi fallback.
- `scraper/smm_worker.py` - `maybe_enqueue_smm_for_movie` (`SMM_AUTOPILOT_ENABLED` + `begin_nested()` savepoint + warning log).
- `scraper/telethon_moderator_pipeline.py` - 3 ta kino commit nuqtasida `maybe_enqueue_smm_for_movie` chaqiruvi (`animeelar`, `anitoob`, asosiy kino oqimi).
- `Dockerfile` - `ffmpeg` va `fonts-dejavu-core` OS paketlari qo'shildi.
- `backend/tests/test_smm_external_publishers.py` - `test_tiktok_publisher_falls_back_to_inbox_when_unaudited` qo'shildi.
- `backend/tests/test_smm_worker.py` - `test_maybe_enqueue_smm_for_movie_respects_env_guard_and_isolates_errors` qo'shildi va kod to'qnashuvi (`99889`) tuzatildi.
- `STATE.md`, `docs/learned.md` - joriy holat va Savepoint/Fallback konsepsiyasi yangilandi.

## check output
```text
# ruff check (SMM modules & tests):
All checks passed!

# alembic heads:
c3d4e5f6a7b8 (head)

# pytest (test_alembic.py + test_smm_*.py):
======================= 37 passed, 2 warnings in 10.09s =======================
(Eslatma: to'liq `backend/tests` yugurishida pre-existing `tests/test_bot_supervision_and_health.py::test_supervised_run_bot_retries_and_exits_nonzero` 70s+ to'xtab qolgani uchun bekor qilinib, filtrlangan `test_alembic.py + test_smm_*.py` to'liq o'tkazildi.)

# admin-panel TypeScript & Next.js build:
npx tsc --noEmit -> Exit code 0
npm --prefix admin-panel run build -> Exit code 0 (✓ Generating static pages 22/22, /smm 4.1 kB)
```

## Risks and unknowns
- TikTok hozir Sandbox rejimida (`inbox/video/init/` -> ilovadagi Inbox/Qoralamalar bo'limiga tushadi); to'liq avtomatik Public nashr (`PUBLIC_TO_EVERYONE`) uchun keyinroq TikTok App Review topshirish kerak.
- Neon PostgreSQL free quota (`InsufficientResourcesError`) sababli jonli DB migratsiyasi (`alembic upgrade head`) hali bajarilmagan.
- `tests/test_bot_supervision_and_health.py::test_supervised_run_bot_retries_and_exits_nonzero` nega to'xtab qolgani alohida tekshirilmagan.

## Live Verification (TikTok over VPN)
```text
PublishResult(platform='tiktok', success=True, post_id='v_inbox_file~v2.7710271558685689876', post_url=None, error=None)
```

## Concept to explain to the user
- Savepoint (`db.begin_nested()`): Asosiy tranzaksiya ichida alohida "orqa eshik" ochib, Cycle 2 da xato chiqsa ham Cycle 1 kinoni saqlashni bekor qilmaslik.

## Next step
- Postgres DB kvotasi/bazasi tiklangach `alembic upgrade head` ni yurgizish, Admin Panel `/smm` ni jonli tekshirish va `feat/smm-autopilot` ni GitHub'ga push qilish.
