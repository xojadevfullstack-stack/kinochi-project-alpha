# Database Migrations — Alembic Rules

> **Glob:** `backend/alembic/**`

## Rules

1. **Always use Alembic** for schema changes — never modify the database
   schema by hand or via raw SQL in application code.

2. **One migration per logical change.** Don't bundle unrelated table
   changes into a single migration file.

3. **Autogenerate first, review second.**
   ```bash
   cd backend
   alembic revision --autogenerate -m "description"
   ```
   Always review the generated migration before committing — autogenerate
   can miss or misinterpret certain changes (e.g., column renames vs.
   drop+add).

4. **Every migration must have a working `downgrade()`.**  If a migration
   cannot be cleanly reversed, document why in a comment.

5. **Never run migrations automatically on app boot in production.**
   Migrations are a controlled deployment step executed explicitly.

6. **The async engine** is configured in `alembic/env.py` — it reads
   `DATABASE_URL` from `app.core.config.settings` so the .ini URL is
   only a fallback for offline mode.

7. **Import all models** in `env.py` (via `Base.metadata`) so that
   autogenerate can detect all tables.  When adding a new model in
   Phase 1+, make sure it is imported in the models package `__init__.py`.
