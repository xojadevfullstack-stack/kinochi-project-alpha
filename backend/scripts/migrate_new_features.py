import asyncio
from app.infrastructure.db.session import engine
from sqlalchemy import text

MIGRATION_SQL = """
-- 1. Add source branding columns to movies if they don't exist
ALTER TABLE movies ADD COLUMN IF NOT EXISTS source_type VARCHAR(50) DEFAULT 'uzmovi';
ALTER TABLE movies ADD COLUMN IF NOT EXISTS custom_source_name VARCHAR(255);
ALTER TABLE movies ADD COLUMN IF NOT EXISTS custom_source_logo VARCHAR(1024);

-- 2. Add source branding columns to series if they don't exist
ALTER TABLE series ADD COLUMN IF NOT EXISTS source_type VARCHAR(50) DEFAULT 'uzmovi';
ALTER TABLE series ADD COLUMN IF NOT EXISTS custom_source_name VARCHAR(255);
ALTER TABLE series ADD COLUMN IF NOT EXISTS custom_source_logo VARCHAR(1024);

-- 3. Create blacklist table
CREATE TABLE IF NOT EXISTS blacklist (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    url VARCHAR(1024),
    reason VARCHAR(255) DEFAULT 'Buzilgan / bo''sh kontent',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_blacklist_title ON blacklist (title);
CREATE INDEX IF NOT EXISTS ix_blacklist_url ON blacklist (url);

-- 4. Create series_subscriptions table for episode alerts
CREATE TABLE IF NOT EXISTS series_subscriptions (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT NOT NULL,
    series_id INTEGER NOT NULL REFERENCES series(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_series_user_subscription UNIQUE (telegram_user_id, series_id)
);
CREATE INDEX IF NOT EXISTS ix_series_subscriptions_series ON series_subscriptions (series_id);
CREATE INDEX IF NOT EXISTS ix_series_subscriptions_user ON series_subscriptions (telegram_user_id);
"""

async def run_migration():
    print("Executing database migration...")
    async with engine.begin() as conn:
        for statement in MIGRATION_SQL.strip().split(";"):
            cleaned = statement.strip()
            if cleaned:
                print(f"Running: {cleaned[:60]}...")
                await conn.execute(text(cleaned))
    print("[OK] Migration executed successfully!")

if __name__ == "__main__":
    asyncio.run(run_migration())
