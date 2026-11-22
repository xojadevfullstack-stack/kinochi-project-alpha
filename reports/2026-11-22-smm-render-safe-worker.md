# Slice Report: 2026-11-22-smm-render-safe-worker

## What was done
1. `scraper/smm_clipper.py` ga `low_ram` rejimi (`720x1280`, `270x480` fon blur, `-threads 1`, `-preset superfast`, `-crf 26`) qo'shildi va `720p` video balandligi uchun xavfsiz xromatik `boxblur` radiuslari (`10:4:5:2`, `16:5:8:3`) o'rnatildi.
2. `scraper/smm_pipeline.py` va `scraper/smm_scene_scorer.py` dagi sinxron FFmpeg/OpenCV chaqiruvlari `asyncio.to_thread` ga o'tkazilib FastAPI + Bot event loop bloklanishi bartaraf etildi.
3. `scraper/smm_worker.py` ga `resolve_smm_session_string` (faqat `SMM_TELEGRAM_STRING_SESSION` — `AuthKeyDuplicatedError` himoyasi), `run_smm_worker_cycle` va `supervised_run_smm_worker` qo'shilib, `run.py` ga ulandi.
4. `scripts/smm_telegram_login.py` (2-Telegram akkaunt uchun `SMM_TELEGRAM_STRING_SESSION` generatori + `STORAGE_CHANNEL_ID` ruxsat tekshiruvi) va `backend/tests/test_smm_login_script.py` qo'shildi.
5. Ikkita real kino (`#MSGXKC`, `8.24 MB`, `720x1280` va `#BSZ47F`, `8.92 MB`, `720x1280`, `FFmpeg peak=149.7 MB`, `Python peak=249.8 MB`, render `8.13s`, jami `90.32s`) ustida jonli E2E test muvaffaqiyatli tasdiqlandi.

## Changed files
- `scraper/smm_clipper.py` - `low_ram=True` (720x1280 + `-threads 1`) va xavfsiz `boxblur` radiuslari.
- `scraper/smm_pipeline.py` - `asyncio.to_thread` render va `SMM_LOW_RAM` (default `true`) uzatish.
- `scraper/smm_scene_scorer.py` - `asyncio.to_thread` audio/frame tekshiruvlari.
- `scraper/smm_worker.py` - `resolve_smm_session_string`, `run_smm_worker_cycle`, `supervised_run_smm_worker`.
- `run.py` - `asyncio.gather` ichiga `supervised_run_smm_worker()` ulandi.
- `backend/tests/test_smm_clipper.py`, `backend/tests/test_smm_worker.py` - `low_ram` va session izolyatsiya TDD testlari.
- `STATE.md`, `docs/learned.md` - holat va yangi konsepsiya yozildi.

## check output
```text
# ruff check (run.py + SMM modules & tests):
All checks passed!

# pytest (test_alembic.py + all test_smm_*.py):
======================= 40 passed, 2 warnings in 18.11s =======================
```

## Risks and unknowns
- Render `512 MB` muhitida jonli `low_ram=True` + `supervised_run_smm_worker()` haqiqiy ishga tushirilishi hali deploy qilinmagan (`UNVERIFIED` until pushed & tested with `SMM_TELEGRAM_STRING_SESSION`).
- Agar `SMM_TELEGRAM_STRING_SESSION` kiritilmasa, Render `publishing`/`scheduled` navbatini yurgizadi, lekin yangi `generating` kliplarni Storage'dan yuklab kesa olmaydi (`TELEGRAM_STRING_SESSION` bilan to'qnashmaslik uchun ataylab ajratilgan).

## Concept to explain to the user
- `asyncio.to_thread` + `270x480` -> `720x1280` blur: asosiy FastAPI/Bot jarayonini qotirmasdan, Render'ning 512 MB xotira chegarasi ichida klip kesish.

## Next step
- Foydalanuvchi tasdig'i bilan `SMM-S5-RenderSafe` ni commit/push qilib `main` ga chiqarish va Render Environment'da 2-Telegram akkaunt uchun `SMM_TELEGRAM_STRING_SESSION` ni qo'yib jonli test o'tkazish.
