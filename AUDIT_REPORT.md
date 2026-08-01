# KINOCHI — FULL PROJECT TECHNICAL AUDIT

## PRIORITY INVESTIGATION — Render / uvloop / Neon IPv6 DNS issue
**Verdict: RESOLVED**

1. **Render Service Deploy Status**: UNVERIFIED. Render deployment logs could not be pulled as the environment lacks Render API credentials.
2. **`uvloop` Status**: `uvloop` is NOT the active event loop. `backend/requirements.txt` does not contain it, and `run.py` explicitly configures Uvicorn with `loop="asyncio"`.
3. **DB Connection String / Driver**: The project uses `postgresql+asyncpg` (asyncpg driver) as defined in `backend/app/core/config.py`.
4. **Workaround Code**: A DNS resolution workaround is actively in place. In `backend/app/infrastructure/db/session.py`, `socket.getaddrinfo` is monkey-patched to filter out IPv6 (AAAA) records and return only IPv4 (`socket.AF_INET`), preventing the Render IPv6 blackhole issue.
   ```python
   def _ipv4_only_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
       results = _original_getaddrinfo(host, port, family, type, proto, flags)
       ipv4_results = [r for r in results if r[0] == socket.AF_INET]
       return ipv4_results if ipv4_results else results
   socket.getaddrinfo = _ipv4_only_getaddrinfo
   ```
5. **Conclusion**: The DNS timeout issue is structurally resolved at the socket level, and `uvloop` is disabled, allowing `asyncpg` to connect successfully.

---

## 1. Test Suite
**Verdict: OK (Tests Growing)**

- **Results**: Run via `pytest backend/tests`. Total collected: 37 items. Passed: 37, Warnings: 21 (mostly deprecations), Failed: 0, Errors: 0.
- **Coverage**: No test coverage tooling (like `pytest-cov`) is configured in the environment.
- **Failing Tests**: None.
- **Baseline Comparison**: The test suite has grown from the baseline of 35 tests to 37 passing tests.

---

## 2. Backend/Bot code health (FastAPI + aiogram)
**Verdict: OK**

- **N+1 Queries**: A codebase sweep revealed no N+1 loop-based query anti-patterns.
- **Lazy-loading outside session**: Resolved. SQLAlchemy ORM models (e.g., `MovieModel`, `SeriesModel`) are strictly using `lazy="selectin"` for relationships (`categories`, `translations`, `pages`), which eager-loads relations natively via an `IN` query.
- **Merge (API + Bot)**: Intact. `run.py` accurately launches both via `asyncio.gather(run_api(), run_bot(), return_exceptions=True)`.
- **Bot Error Handling**: `bot/main.py` wraps the polling process in a `while True` loop with a generic `except Exception` catch and exponential backoff, preventing catastrophic crashes.

---

## 3. Security
**Verdict: ISSUE FOUND**

- **Hardcoded Secrets**: Clean. Only mocked placeholder strings exist in `backend/tests/test_auth.py`. No real API keys or tokens are hardcoded.
- **Env Validation**: Secure. `backend/app/core/config.py` uses Pydantic `BaseSettings`. Missing non-default variables (e.g., `BOT_TOKEN`) will fail-fast at startup.
- **Unescaped HTML (Vulnerability)**: `bot/utils/movie_sender.py` formats movie titles dynamically with `parse_mode="HTML"` but without escaping: `f"🍿 <b>{movie.get('title')}</b>\n\n{movie.get('description') or ''}"`. A movie title containing `<` or `&` will crash the Telegram bot with `TelegramBadRequest`. Only `info_sender.py` currently uses `html.escape`.
- **SQL Injection**: Safe. Uses parameterized queries via SQLAlchemy 2.0 ORM (`mapped_column`, `select()`). No raw f-strings executing SQL were found.
- **Rate Limiting / Abuse Protection**: API is protected via `SlowAPIMiddleware` (`backend/app/api/limiter.py`). However, **the Telegram bot lacks any throttling middleware** (checked `bot/middlewares/`), exposing it to bot spam/DDoS.
- **Subscription Bypass**: Protected. `SubscriptionMiddleware` is globally registered to both `message` and `callback_query` in `bot/main.py`.

---

## 4. Performance
**Verdict: ISSUE FOUND**

- **API Response Times**: UNVERIFIED. No local load-testing tooling/scripts (like Locust or k6) exist in the repository to measure this.
- **DB Connection Pool**: `backend/app/infrastructure/db/session.py` uses `create_async_engine` but relies on SQLAlchemy defaults (`pool_size=5`, `max_overflow=10`). This may be slightly restrictive or untuned for Render's tier, but no explicit bottleneck is visible yet.
- **Redis Usage**: Redis is utilized via `backend/app/core/job_manager.py` to manage background tasks (video uploads) with a 3-day TTL. It is **not** currently used for caching DB queries (e.g., movie catalogs), meaning all API read requests hit PostgreSQL directly.

---

## 5. Database
**Verdict: OK**

- **Schema & Indexes**: Explicit indexes are present on highly queried columns (e.g., `title`, `release_year`, `code`, `source_chat_id` in `MovieModel`).
- **Migrations (Alembic)**: Clean. Running `alembic current` correctly aligns with the `alembic history` head (`66bfb6a20149`). No pending or unapplied migrations exist.
- **Connection**: Using standard `asyncpg` strings; connection pooling is handled by SQLAlchemy.

---

## 6. Frontend (Next.js)
**Verdict: ISSUE FOUND**

- **Build**: FAILED. Running `npm run build` throws a `DYNAMIC_SERVER_USAGE` error because `/movies` and `/series` routes attempt to statically render while relying on dynamic `searchParams.category`. Additionally, `ECONNREFUSED` errors occur because the frontend requires the backend to be running during the static generation phase.
- **Lint / Typecheck**: FAILED. `npm run lint` fails because ESLint is not initialized (`next lint` hangs on an interactive prompt).
- **Bundle Size**: UNVERIFIED (Build could not finish).
- **API URLs**: Proper environment variables are utilized via Next.js proxy configs/env settings.

---

## 7. Deployment/Infra
**Verdict: PARTIALLY VERIFIED**

- **Render / Vercel Status**: UNVERIFIED (No API access or deploy logs available locally).
- **Health Checks**: Properly implemented. `backend/app/main.py` provides a `/health` endpoint. Additionally, the backend lifespan features an internal keep-alive coroutine that pings its own `/health` endpoint every 14 minutes to prevent Render's free-tier from sleeping.

---

## 8. Feature completeness snapshot
**Verdict: OK**

- **Movie/series catalog & search**: Implemented (`MovieModel`, `SeriesModel`, and respective API/Bot routers).
- **Mandatory channel subscription**: Implemented (`bot/middlewares/subscription_check.py`).
- **Trailer system**: Partially implemented (Schema column `trailer_url` added in Alembic migration `66bfb6a20149`), but missing full auto-detection logic.
- **User-facing bot flows**: Implemented (Start, Catalog, Search, Browsing, and Episode inline keyboards are fully registered in `bot/main.py`).
- **Admin/management**: Implemented (`AdminUserModel` and `/api/v1/auth/` routers exist).

---

**PRIORITIZED ISSUE LIST**

| # | Issue | Severity (Critical/High/Medium/Low) | File/Location | Evidence |
|---|---|---|---|---|
| 1 | Unescaped HTML in Telegram Bot | High | `bot/utils/movie_sender.py` | String formatting (`f"<b>{title}</b>"`) without `html.escape` combined with `parse_mode="HTML"`. Causes bot crashes on malformed text. |
| 2 | Next.js Build Failure | High | `website/app/movies/page.js` | `DYNAMIC_SERVER_USAGE` error during static generation due to `searchParams`. |
| 3 | Lack of Bot Rate Limiting | Medium | `bot/middlewares/` | `SlowAPI` is present on the backend, but no anti-spam/throttling middleware exists for the Aiogram bot. |
| 4 | Redis not used for read-caching | Low | `backend/app/core/job_manager.py` | Redis is actively connected for job states, but no DB caching is implemented for heavily-read catalogs. |
| 5 | Frontend Linter Unconfigured | Low | `website/` | `npm run lint` triggers an interactive initialization prompt and fails CI. |
