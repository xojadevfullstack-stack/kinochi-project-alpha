# Slice Report: 2026-11-24-bot-transfer-and-legacy-redirect

## What was done
1. `bot/config.py`, `bot/redirect_bot.py` va `run.py` ichida ixtiyoriy `LEGACY_BOT_TOKEN` asosida ishlaydigan izolyatsiyalangan eski-bot redirect jarayoni qo'shildi (`?start=<payload>` deep-link va ixtiyoriy `REDIRECT_CHANNEL_URL` tugmasini saqlagan holda).
2. `scraper/telethon_moderator_pipeline.py` va `scraper/smm_worker.py` dagi qattiq yozilgan eski bot username fallback'lari `BOT_USERNAME` env o'zgaruvchisiga bog'landi (`topic`, `manbalar` va `STORAGE_CHANNEL_ID` o'zgarishsiz qoldirildi).
3. `bot/tests/test_redirect_bot.py` TDD testlari yozildi, `STATE.md` va `docs/learned.md` yangilandi.

## Changed files
- `bot/config.py` - Added `LEGACY_BOT_TOKEN` and `REDIRECT_CHANNEL_URL`, removed unused `Optional`
- `bot/redirect_bot.py` - Lightweight isolated legacy redirect bot preserving `?start=` payloads
- `run.py` - Added `safe_run_redirect_bot()` alongside API, primary bot, and SMM worker
- `scraper/telethon_moderator_pipeline.py` - Replaced hardcoded `@kinochi_mvp_bot` with `BOT_USERNAME` env
- `scraper/smm_worker.py` - Added `BOT_USERNAME` env fallback when `cfg.bot_username` is empty
- `bot/tests/test_redirect_bot.py` - Unit tests for deep-link URL builder, reply markup, handlers, and disabled guard

## check output
```text
ruff check bot/config.py bot/redirect_bot.py bot/tests/test_redirect_bot.py run.py scraper/smm_worker.py: All checks passed!
bot pytest (bot/tests/): 112 passed in 6.19s
backend pytest (test_smm*.py, test_smart_enricher_regression.py, test_video_verifier.py): 70 passed, 2 warnings in 12.11s
```

## Risks and unknowns
- Telegram `file_id` botga bog'liq bo'lgani uchun yangi bot eski filmlarda `STORAGE_CHANNEL_ID` dan `copy_message` fallback orqali ishlaydi — yangi bot albatta Storage kanali va Topic guruhida Admin bo'lishi shart.
- Render (`BOT_TOKEN`, `LEGACY_BOT_TOKEN`, `BOT_USERNAME`), Vercel (`NEXT_PUBLIC_BOT_USERNAME`), `@BotFather /setdomain` va `/smm` dagi `bot_username` + `telegram_channel_id` bir vaqtda yangilanishi kerak.

## Concept to explain to the user
- **Dual-Bot Strangler Pattern**: Eski botni o'chirmasdan alohida izolyatsiyalangan dispatcher orqali `?start=<kod>` parametrlari bilan yangi botga tugma berish eski SMM/veb havolalardan kelgan foydalanuvchilarni yo'qotmaydi.
  - Analogy: Eski do'kon eshigiga "ko'chdik" deb yozib qo'yibgina qolmay, kelgan har bir mijozni buyurtma raqami bilan birga to'g'ridan-to'g'ri yangi do'kon peshtaxtasiga yo'naltirish.

## Next step
- Render, Vercel, `@BotFather /setdomain`, Storage Admin va `/smm` sozlamalarini yangilab jonli sinab ko'rish (foydalanuvchi yangi bot tokeni va kanalini kiritgach).
