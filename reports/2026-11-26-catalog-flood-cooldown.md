# Slice Report: 2026-11-26-catalog-flood-cooldown

## What was done
1. `scraper/catalog_worker.py` ga `_parse_flood_sleep_seconds` va `_handle_unpublished_outcome` qo'shildi: donor bot flood limiti (`"flood"` / `"daqiqa kutilishi"`) aniqlanganda item `failed` holatida yo'qotilmasdan `queued` ga qaytariladi hamda worker o'sha daqiqa bo'yicha (`min 300s .. max 3600s`) uxlaydi; ketma-ket 4 ta muvaffaqiyatsizlikda esa `60s` o'rniga `600s` backoff qo'llanadi.
2. `backend/tests/test_catalog_worker.py` ga 2 ta RED -> GREEN test qo'shildi (`test_next_tick_sleep_seconds_backs_off_on_flood_wait_and_failure_streak`, `test_run_catalog_worker_tick_requeues_item_on_bot_flood_limit`).
3. `STATE.md` va `docs/learned.md` yangilandi.

## Changed files
- `scraper/catalog_worker.py` - Added flood-safe requeue (`_handle_unpublished_outcome`) and cooldown/streak backoff (`next_tick_sleep_seconds`)
- `backend/tests/test_catalog_worker.py` - Added 2 unit tests verifying flood requeue and cooldown sleep durations
- `STATE.md`, `docs/learned.md`, `reports/2026-11-26-catalog-flood-cooldown.md` - Tracking updates

## check output
```text
ruff check & ruff --select F821 -> All checks passed!
alembic heads -> h8c9d0e1f2a3 (head)
pytest backend/tests/test_catalog_worker.py -v -> 8 passed, 1 warning in 1.67s
pytest backend/tests/test_smm_worker.py -q -> 18 passed
pytest backend/tests/test_smm_api.py -q -> 9 passed
pytest bot/tests/ -q -> 116 passed
```

## Risks and unknowns
- `@UzmovieTV_Bot` dan `"Serial tugmalari topilmadi"` yoki `"video olinmadi"` xatolari chiqayotgan kontentlar forward-only usulda olinmasa 4 tadan keyin worker `10` daqiqa kutishga tushadi (`failed` lar ko'paymasligi uchun xavfsiz).

## Concept to explain to the user
- **Semantic Flood Recovery + Failure-Streak Backoff** — Donor bot tanaffus berganini xato matnidan tanib, filmni kuydirmasdan navbatga qaytarish va `60s` o'rniga kutish vaqti tugaguncha uxlash.
- Analogy: Omborda "30 daqiqa tanaffus" bo'lganda har minutda yangi yuk mashinasi jo'natib qaytarish o'rniga, tanaffus tugashini kutish.

## Next step
- Push qilib Render yangilangach, flood tufayli `failed` bo'lgan `asilmedia` filmlarini `queued` ga qaytarish va `#1088` (*Ma'sumlik davri*) uchun yangi Variant 1 `SMM Job #8` ni jonli tekshirish.
