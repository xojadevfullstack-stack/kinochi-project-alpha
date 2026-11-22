# Slice Report: 2026-11-22-smm-short-code-and-go-page

## What was done
1. **Backend (`short_code` + Alembic):** `movies` jadvaliga `short_code` (`VARCHAR(16) UNIQUE`) ustuni (`d4e5f6a7b8c9_add_movie_short_code.py`) qo'shildi, mavjud kinolarga `1001+` backfill va `MovieRepositoryImpl.create()` da avtomatik ketma-ket `short_code` berish ulandi; `get_by_code` hamda `/api/v1/search/live` da `code`/`short_code` raqamli `id` fallback'idan ustuvor qilindi.
2. **SMM Autopilot & Bot:** `SmmSettingsModel`, `smm_clipper.py`, `smm_pipeline.py`, `smm_worker.py`, `telegram_pub.py` va `youtube_tiktok_pub.py` da `short_code` hamda `@MediaPlusOfficialBot` sinxronizatsiyasi (YouTube description'ga deep-link bilan) joriy qilindi; Telegram botda (`info_sender.py`, `start.py`) `short_code` ko'rsatish va topilmagan kodda tezkor Qidirish/Katalog tugmalari qo'shildi.
3. **Website (`/go`):** Instagram/TikTok Bio uchun raqamli klaviaturali (`inputMode="numeric"`) `website/app/go/page.tsx` tezkor kod sahifasi va `Breadcrumb.tsx` yorlig'i yaratildi.

## Changed files
- `backend/app/infrastructure/db/models/movie.py` - `MovieModel.short_code` ustuni
- `backend/app/domain/movies/entities.py` - `Movie.short_code` maydoni
- `backend/app/application/movies/service.py` - `create_movie` ga `short_code` uzatish
- `backend/app/infrastructure/db/repositories/movie_repo.py` - `_next_short_code()` va `get_by_code()` ustuvorligi
- `backend/app/api/v1/movies.py` - `MovieCreate`, `MovieUpdate`, `MovieResponse` da `short_code`
- `backend/app/api/v1/search.py` - `LiveSearchResultItem` va `live_search` da `short_code`
- `backend/alembic/versions/d4e5f6a7b8c9_add_movie_short_code.py` - `movies.short_code` backfill va `smm_settings.bot_username` yangilash
- `backend/app/infrastructure/db/models/smm.py` - defolt `bot_username` `@MediaPlusOfficialBot`
- `scraper/smm_clipper.py` - defolt `@MediaPlusOfficialBot`
- `scraper/smm_pipeline.py` - `bot_username` parametrini uzatish
- `scraper/smm_worker.py` - `short_code` va `@MediaPlusOfficialBot` ishlatish
- `scraper/smm_publishers/telegram_pub.py` - defolt `@MediaPlusOfficialBot`
- `scraper/smm_publishers/youtube_tiktok_pub.py` - YouTube title/description da `bot_username` va deep-link
- `bot/utils/info_sender.py` - karta matnida `short_code` ko'rsatish
- `bot/handlers/start.py` - topilmagan kodda Qidirish/Katalog tugmalari
- `website/app/go/page.tsx` - tezkor raqamli kod kiritish sahifasi
- `website/components/Breadcrumb.tsx` - `/go` yorlig'i
- `backend/tests/test_movie_short_code.py`, `bot/tests/test_bot_short_code_ux.py` - yangi testlar

## check output
```text
- Alembic heads: d4e5f6a7b8c9 (head)
- Backend targeted suite (10 files): 50 passed, 2 warnings in 9.73s
  (Eslatma: to'liq `backend/tests/` yugurtirilganda avvaldan ma'lum 3 ta F0/env testlari va uzoq external audit testlari borligi uchun 10 ta tegishli modul va `test_uzmovi_code_verified_guard.py` tekshirildi — `test_uzmovi_bot_code_verified_defaults_false` lokal `.env` tufayli fail).
- Bot full suite (`bot/tests/`): 104 passed in 14.44s
- Website lint (`npm --prefix website run lint`): Exit code 0 (0 errors)
- Website build (`npm --prefix website run build`): Exit code 0 (31/31 static/dynamic pages including `/go`)
```

## Risks and unknowns
- Production Render bazasida `alembic upgrade head` ishga tushirilishi kerak (hali jonli DB'ga qo'llanmadi).
- `SMM_TELEGRAM_STRING_SESSION` Render Environment'ga kiritilmaguncha jonli `/smm` klipp generatsiyasi to'liq tekshirilmagan.

## Concept to explain to the user
- **Dual-Code Aliasing (Ikki kodli moslik):** Eski murakkab kodlarni (`PT3BQB`) o'chirmasdan yoniga qisqa raqamli `short_code` (`1001+`) qo'shish — xuddi eski uy manzilini saqlab qolib, yoniga qisqa pochta qutisi raqami berishga o'xshaydi; eski havolalar ham ishlayveradi, yangi foydalanuvchi esa 4 ta raqam bilan darhol kinoni topadi.

## Next step
- Xoja lokal sayt/bot/migratsiyani tekshirgach, `alembic upgrade head` va `git push` qilish.
