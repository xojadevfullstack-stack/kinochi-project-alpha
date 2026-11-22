# Slice Report: 2026-11-22-smm-episode-short-code

## What was done
1. `backend/app/infrastructure/db/short_code_alloc.py` yaratildi: `pg_advisory_xact_lock(90210)` va `MovieModel`/`EpisodeModel` kesishma tekshiruvi bilan yagona global ketma-ketlik (`next_global_short_code`).
2. `EpisodeModel.short_code`, `Episode.short_code`, `SeriesRepository.create_episode/get_episode_*` va `e5f6a7b8c9d0_add_episode_short_code.py` migratsiyasi qo'shildi (`MovieRepositoryImpl.get_by_code` ham `Episode.short_code` bilan `MovieModel.id` to'qnashuvini oldini oladi).
3. `/api/v1/search/live`, Bot (`code_resolver.py` `4+` xonali raqam tekshiruvi + `episode_sender.py`), `/go` (`website/app/go/page.tsx`) va `scraper/smm_worker.py` (`_resolve_job_media` — `movie` + `episode`) to'liq ulandi.

## Changed files
- `backend/app/infrastructure/db/short_code_alloc.py` - yagona global allocator.
- `backend/app/infrastructure/db/models/series.py`, `backend/app/domain/series/entities.py` - `episodes.short_code`.
- `backend/app/infrastructure/db/repositories/movie_repo.py`, `series_repository.py` - collision-safe lookup va auto-alloc.
- `backend/alembic/versions/e5f6a7b8c9d0_add_episode_short_code.py` - Supabase backfill (`1091..3954`).
- `backend/app/api/v1/search.py`, `backend/app/api/v1/smm.py`, `scraper/smm_worker.py` - LiveSearch, SMM API (`episode`), va `_resolve_job_media`.
- `bot/utils/code_resolver.py`, `bot/utils/episode_sender.py`, `website/app/go/page.tsx` - Bot UX va `/go` yo'naltirish.
- `backend/tests/test_episode_short_code.py`, `bot/tests/test_bot_episode_short_code.py`, `backend/tests/test_smm_worker.py` - TDD testlari.

## check output
```text
- Supabase Alembic: e5f6a7b8c9d0 (head), MOVIES=(90,90,1001,1090), EPISODES=(2864,2864,1091,3954), OVERLAP=0
- Backend (test_episode_short_code + test_movie_short_code + test_alembic + test_requirements_and_entrypoint + test_phase1_security + test_smm*.py): 60 passed, 1 warning in 15.60s
- Bot full suite (bot/tests/): 106 passed in 8.19s
```

## Risks and unknowns
- Render va Vercel yangi commitlar bilan qayta deploy tugatishi kerak; `website` `next build` (`/go` o'zgarishidan keyin) commit oldidan yana tekshiriladi.

## Concept to explain to the user
- **Global Sequence + Anti-Collision Lookup Priority:** Kinolar va qismlar yagona hisoblagichdan ketma-ket raqam oladi (`1001..1090` kinolar, `1091..3954` qismlar, `3955+` umumiy) va qidiruv avval aniq `short_code` ni tekshiradi, keyin ichki DB `id` ga qaraydi — kelajakda `movies.id >= 1091` bo'lganda ham eski qism kodi adashib kinoni ochib yubormaydi.
