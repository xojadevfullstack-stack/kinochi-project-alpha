# Slice Report: 2026-11-26-smm-video-head-restore-lock

## What was done
1. `backend/app/api/v1/smm.py` da `/jobs/{job_id}/video` endpointi `GET` va `HEAD` (`200 OK`, `Content-Length`, `Accept-Ranges`) ni qo'llab-quvvatlaydigan qilindi hamda `_restore_clip_from_telegram` ga har bir fayl bo'yicha `asyncio.Lock` (`_RESTORE_LOCKS`) va `uuid.uuid4().hex` vaqtinchalik fayl qo'shildi (`os.getpid()` poygasini yo'qotish uchun).
2. `scraper/smm_worker.py` da ham Storage restore vaqtinchalik fayli `uuid4().hex` ga o'tkazildi.
3. `backend/tests/test_smm_api.py` da RED -> GREEN testlar (`HEAD 200` + `test_restore_clip_from_telegram_coalesces_concurrent_requests`) qo'shildi, `STATE.md` va `docs/learned.md` yangilandi.

## Changed files
- `backend/app/api/v1/smm.py` - Added `HEAD` support and `_RESTORE_LOCKS` + `uuid4` temp swap in `_restore_clip_from_telegram`
- `scraper/smm_worker.py` - Replaced `os.getpid()` temp suffix with `uuid.uuid4().hex`
- `backend/tests/test_smm_api.py` - Added `HEAD 200` assertion and concurrent restore coalescing test
- `STATE.md`, `docs/learned.md`, `reports/2026-11-26-smm-video-head-restore-lock.md` - Tracking docs

## check output
```text
ruff check & ruff --select F821 -> All checks passed!
pytest backend/tests/test_smm_api.py -v -> 9 passed, 2 warnings in 2.58s
pytest backend/tests/test_smm_worker.py -q -> 18 passed, 1 warning in 19.07s
```

## Risks and unknowns
- Render bevosita yangilangach `Job #7` (`#1089`) uchun faqat `facebook` qayta yuborilib, Make.com Facebook ssenariysi ichidagi natija kuzatiladi (Make.com ichki Graph API tokeni ham expired bo'lsa, Make.com ssenariy ichidan alohida xato ko'rinadi).

## Concept to explain to the user
- **Per-File Async Lock (`Request Coalescing`) + `HEAD 200` Media Probe** — Bir vaqtda kelgan ikki tashqi yuklovchini bitta Storage tiklash poygasidan himoyalash va `HEAD` tekshiruvini ochish.
- Analogy: Ikki kuryer bir vaqtda ombordan bitta posilkani so'raganda ikkisi ham bitta qutini tortishmasligi uchun birinchisi olib chiqib beradi, ikkinchisi esa tayyor posilkani darhol oladi.

## Next step
- Commit + push qilib Render'da `HEAD /api/v1/smm/jobs/7/video == 200` bo'lishini kutish, so'ngra `Job #7` (`#1089`) ni Facebook'ka qayta yuborish.
