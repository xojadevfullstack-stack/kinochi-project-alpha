import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import text
from app.infrastructure.db.session import engine


async def migrate():
    print("Running migration for collection_subscriptions and category_type...")
    async with engine.begin() as conn:
        # 1. Add category_type to collections if not exists
        await conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name='collections' AND column_name='category_type'
                ) THEN
                    ALTER TABLE collections ADD COLUMN category_type VARCHAR(50) DEFAULT 'franchise' NOT NULL;
                END IF;
            END $$;
        """))

        # 2. Create collection_subscriptions table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS collection_subscriptions (
                id SERIAL PRIMARY KEY,
                telegram_user_id BIGINT NOT NULL,
                collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                CONSTRAINT uq_collection_user_subscription UNIQUE (telegram_user_id, collection_id)
            )
        """))

        # 3. Create indices separately for asyncpg
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_collection_subscriptions_user_id ON collection_subscriptions(telegram_user_id)
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_collection_subscriptions_collection_id ON collection_subscriptions(collection_id)
        """))

    print("Migration finished successfully!")


if __name__ == "__main__":
    asyncio.run(migrate())
