# Slice Report: 2026-11-27-poster-backfill-and-smm-v10-wiring

## What was done
1. Implemented `backfill_one_unlocalized_poster` in `backend/app/api/v1/posters.py` with 7-day Redis/in-process cooldown (`poster:v10:skip:{media_type}:{id}`), wider `limit(100)` scan, and strict `POSTER_BACKFILL_DAILY_LIMIT=15` (`UTC+5`) daily quota cap so idle backfill consumes `<4%` of daily Gemini RPD and preserves quota for newly uploaded media & SMM.
2. Wired idle-tick poster backfill into `scraper/smm_worker.py` (`run_smm_worker_tick` when `generated == 0 and published == 0` under `POSTER_BACKFILL_ENABLED=1`) alongside existing SMM cover (`_ensure_localized_poster_url`) and ingest triggers (`telethon_moderator_pipeline.py`, `movies.py`, `series.py`), plus added CLI runner `scripts/backfill_uzbek_posters.py`.
3. Added TDD regression test in `backend/tests/test_posters_storage.py`, backfilled live `series#1000` (*Yigitlar*), `series#1014` (*Jodugarlar Jangi*), `series#1065` (*Arra odam*), and verified batch (`movie#918`, `#914`, `#911` localized; `#916`, `#913`, `#912` cleanly blocked by quality gate).

## Changed files
- `backend/app/api/v1/posters.py` - Added `backfill_one_unlocalized_poster` and 7-day skip cooldown helpers.
- `scraper/smm_worker.py` - Added safe idle-tick backfill invocation in `run_smm_worker_tick`.
- `scripts/backfill_uzbek_posters.py` - Added CLI batch runner for controlled live poster backfill.
- `backend/tests/test_posters_storage.py` - Added `test_backfill_one_unlocalized_poster_updates_db_and_skips_failed_with_cooldown`.
- `STATE.md`, `docs/learned.md` - Documented live backfill results and idle cooldown concept.

## check output
```text
ruff check backend/app/api/v1/posters.py scraper/smm_worker.py scripts/backfill_uzbek_posters.py backend/tests/test_posters_storage.py
All checks passed!

alembic heads
i9d0e1f2a3b4 (head)

pytest -p no:cacheprovider tests/test_smm_pipeline_and_telegram_pub.py tests/test_smm_worker.py tests/test_poster_localizer.py tests/test_poster_triggers.py tests/test_posters_storage.py tests/test_fix_f013_swallowed_exceptions.py -q
87 passed in 21.97s

pytest -p no:cacheprovider bot/tests -q
116 passed in 6.87s
```

## Risks and unknowns
- ~200 older media rows remain to be gradually backfilled on Render idle ticks (`1` per 3-minute tick); items whose posters fail quality gate (`score < 7`) keep their clean English posters under a 7-day cooldown.
- Unrelated dirty workspace files remain unstaged.

## Concept to explain to the user
- **Idle Quality-Gated Backfill + 7-Day Cooldown:** Bo'sh vaqtlarda bittadan eski posterni yangilab, sifat nazoratidan o'tmaganini 7 kunga muzlatib qo'yish server RAM va AI kvotasini himoyalaydi.

## Next step
- Render deploy (`origin/main`) ko'tarilgach `Job #10/#13/#19` va fon backfill natijalarini kuzatish.
