# Slice Report: 2026-11-25-smm-lowram-redirect-poster-fixes

## What was done
1. Isolated `bot/redirect_bot.py` strictly to `private` chats (`F.chat.type == "private"` + runtime guard) so legacy redirect messages never spam supergroups/Forum Topics (`AUTO_TOPIC_CHAT_ID`).
2. Hardened Render `low_ram=True` video rendering in `scraper/smm_clipper.py` (single `[0:v]fps=24,scale=720:-2,split=2` decode, `max_zones=2` blur cap, `-preset ultrafast`, POSIX `os.nice(15)` CPU yield, `timeout=240s` `TimeoutExpired` guard) and added a `25s` Render startup delay (`SMM_STARTUP_DELAY_SEC`) in `scraper/smm_worker.py` so `/health` and Telegram bots stay responsive during background SMM clip generation.
3. Wired `localize_media_poster_safe` (automatic Uzbek poster localization) after scraper movie DB commits and `delete_storage_message_safe` to delete orphaned `STORAGE_CHANNEL_ID` messages whenever Admission Gate `final_check` rejects a movie (`Balandrau` root cause); also localized live `Movie #915` (`Xolms va Vatson`) poster.

## Changed files
- `bot/redirect_bot.py` - Restricted start, text, and callback handlers to `private` chats
- `bot/tests/test_redirect_bot.py` - Regression tests ensuring groups, supergroups, and channels are ignored
- `scraper/smm_clipper.py` - Single-decode `low_ram`, blur zone cap, `ultrafast`, `os.nice(15)`, and render `timeout`
- `scraper/smm_worker.py` - Render startup grace delay (`SMM_STARTUP_DELAY_SEC`)
- `scraper/telethon_moderator_pipeline.py` - `localize_media_poster_safe` hook + `delete_storage_message_safe` on `final_check` failure
- `backend/tests/test_smm_clipper.py`, `backend/tests/test_smm_worker.py`, `backend/tests/test_poster_triggers.py` - Unit/regression tests for all fixes

## check output
```text
bot/tests/: 116 passed in 8.10s
backend/tests/test_smm_*.py: 62 passed, 2 warnings in 21.88s
backend/tests/test_poster_* + test_fix_f002_pipeline_pre_check.py: 15 passed, 1 warning in 3.06s
ruff check bot/redirect_bot.py bot/tests/test_redirect_bot.py scraper/smm_clipper.py scraper/smm_worker.py backend/tests/test_smm_clipper.py backend/tests/test_smm_worker.py backend/tests/test_poster_triggers.py: All checks passed!
```

## Risks and unknowns
- Render `/analytics` (`Real Statistika`) returned `HTTP 500` earlier while the Render container was under `SMM Job #5` load; needs live verification once Render finishes deploying these fixes.
- `Ertangi kun afsonalari` (`Series #1124`) still has `30` episodes in DB (`Season #1415`) vs `36` messages in the Telegram Forum Topic (no `rejected_items` entry; happened in an earlier partial ingest).

## Concept to explain to the user
- **Single-Decode Split + CPU `nice(15)`:** Videoni 2 marta ochish va fon jarayonga cheksiz CPU berish o'rniga bitta yengil oqimni bo'lish (`split=2`) va FFmpeg ustuvorligini pasaytirish (`nice(15)`) FastAPI hamda Telegram bot doim birinchi navbatda javob berishini ta'minlaydi — xuddi kichik do'kon sotuvchisi og'ir yuk ko'targanda ham mijoz kelishi bilan kassaga qaytgani kabi.

## Next step
- Push commits to `origin/main` for Render redeploy, wait for `SMM Job #5` (`Xolms va Vatson`) clip completion, and verify live Admin Panel (`/analytics`, `/movies`, `/smm`) + `5/5` publish.
