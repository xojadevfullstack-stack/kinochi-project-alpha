# Architecture Decisions (docs/decisions.md)

## ADR-001: Separation of Series and Movies
- **Context:** Initially, series and single movies shared overlapping database schemas and queries, leading to schema complexity and heavy data joins.
- **Decision:** Fully decouple Series and Movies domains. Series follows the clean hierarchy `Series -> Season -> Episode`. Series listing endpoints use lightweight summary models (`SeriesSummary`, `PaginatedSeriesSummaryResponse`) with `noload` on heavy relations.
- **Status:** Accepted & Implemented (Faza F0 - C0.4).

## ADR-002: Asyncpg Connection Pooler Settings for Production
- **Context:** Deployments on Render using Neon / PgBouncer experienced prepared statement name collisions and pool exhaustion.
- **Decision:** Disable asyncpg client-side prepared statement cache (`statement_cache_size=0`, `prepared_statement_cache_size=0`) and configure explicit pool boundaries (`DB_POOL_SIZE=10`, `DB_MAX_OVERFLOW=20`).
- **Status:** Accepted & Implemented (Faza F0 - C0.3).

## ADR-003: Rate-Limited Telegram Broadcast Pipeline
- **Context:** Broadcasting new episode and movie alerts to large subscriber lists caused Telegram API `429 Too Many Requests` flood wait errors and unhandled worker blocks.
- **Decision:** Implement token bucket throttling (max 20 messages/second with `0.05s` interval and `1.0s` pause every 500 dispatches). Handle `429` with exponential `retry_after`, and handle `403 Forbidden` by pruning deactivated user IDs.
- **Status:** Accepted & Implemented (Faza F0 - C0.5).

## ADR-004: Unified Linear Alembic Revision History
- **Context:** Multiple branch merges created dual head revisions in Alembic versions.
- **Decision:** Merge dual heads into a single linear head revision (`f1322da82a96`). All future migrations must branch strictly from this revision.
- **Status:** Accepted & Implemented (Faza F0 - C0.2).

## ADR-005: Clean Architecture Boundaries (Thin Bot Client)
- **Context:** Business logic leaking into Telegram bot handlers duplicated domain logic and complicated testing.
- **Decision:** Keep the `bot/` package as a thin UI client. All persistent operations, search indexing, and auth validation must route through the `backend/` REST API.
- **Status:** Accepted.

## ADR-006: Frontend Build Decoupled from Fast Quality Gate
- **Context:** Running Next.js production builds on every slice iteration and pre-commit checks significantly slowed down backend and bot development cycles.
- **Decision:** `make check` executes fast gates: `lint`, `typecheck`, and automated `test` suites. Full production website builds run via `make build` and `make check-release` during CI pipeline executions or release candidates.
- **Status:** Accepted (2026-10-27).

## ADR-007: Frozen Baseline Test Failure Handling Policy
- **Context:** Three specific test failures were frozen at the end of Faza F0 (`test_fix_f013_swallowed_exceptions.py`, `test_seed_config_s2.py`, `test_seed_ingestor_full_s9.py`).
- **Decision:** Do not touch or modify baseline failures blindly during initial F1 slices. Document their root causes, verify their origin from F0, and only fix an individual test if an F1 slice directly addresses its domain. Tests must never be deleted, skipped, or weakened.
- **Status:** Accepted (2026-10-27).

## ADR-008: Ambient Video Backdrop & Dedicated Hero Trailer Trigger
- **Context:** Bulky standalone trailer section consumed excessive vertical space and broke visual flow on movie and series details pages.
- **Decision:** Migrate trailers to an ambient background video layer (`HeroTrailerBackdrop.tsx`) behind the hero banner with protective vignette gradients, instant LCP poster fallback, muted loop playback, interactive floating sound toggle, and an ergonomic "TREYLER" modal trigger in the primary actions row.
- **Status:** Accepted & Implemented (F1-S27).


## ADR-009: Idempotent Schema Reconciler & Historical Alembic Migrations Integrity
- **Context:** Historical migrations `c011ec7100`, `da3404d65ffd`, and `8e4e155f48db` contain anomalies: `c011ec7100` references `collections(id)` which was historically created via `Base.metadata.create_all` rather than an earlier Alembic migration, and historical downgrades contain destructive drops or missing cascade clauses.
- **Decision:** Do not rewrite or modify historical migration files (`c011ec7100`, `da3404d65ffd`, `8e4e155f48db`), because they may have already been applied to existing production environments and editing them would cause checksum/history divergence. Instead, implement an idempotent schema reconciler migration (`b2c3d4e5f6a7`) with `IF NOT EXISTS` DDL guards for all drifted tables/columns (`series_sources`, `collections`, `collection_items`, `series_subscriptions`, `reports`, `blacklist`, and `movies`/`series` metadata columns including `tmdb_rating`). For foreign keys (`fk_series_source_id`), create constraints with `NOT VALID` to avoid deployment blockage if orphan rows exist, query orphan count and validate only when zero orphans exist, and narrow exception handling strictly to `duplicate_object`. Keep `downgrade()` in `b2c3d4e5f6a7` non-destructive to preserve user data in production. If historical migrations are replayed on empty databases, run initial bootstrap schema before stamping or replaying.
- **Status:** Accepted & Implemented (Phase 4, 2026-11-01).

## ADR-010: Poster Localization v7 Standard & Mandatory Localized SMM Clip Covers
- **Context:** Poster localization using Cloudflare `flux-2-klein-4b` alone had inconsistent font fidelity, occasional Cyrillic leaks (`ШОГУН`), face/scene distortion, and off-center placement; additionally, `scraper/smm_pipeline.py` and `scraper/smm_worker.py` fed unlocalized TMDb English posters into the `0.35s` social media video cover and used an invalid `app.infrastructure.external.telegram_client` import path.
- **Decision:** Standardize on the **v7 Studio Typography & Safety Pipeline**: (1) TMDb Textless Twin matching (`max_mae=25.0`) + `has_visible_title` clean guard, (2) Vision style extraction with `letter_spacing`, `font_weight`, `is_italic`, `texture_style`, `force_center=True` on textless posters, `_sanitize_font_text` (`ʻ`/`ʼ`/`‘`/`’` -> `'`), contrasting `_should_apply_rim`, and hue-preserving `metallic` + 3D extrusion bevel, (3) Cyrillic + outside-title MAE (`<= 10.5`) rejection gates on AI edits, and (4) automatic `_ensure_localized_poster_url` + direct `telegram_client.download_file_bytes` lookup before rendering every SMM clip cover.
- **Status:** Accepted & Deployed (2026-11-27).
