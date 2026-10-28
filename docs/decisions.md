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
