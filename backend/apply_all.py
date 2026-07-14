import asyncio
import asyncpg
from app.core.config import settings

async def apply_all_missing_migrations():
    url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
    print("Connecting to", url)
    conn = await asyncpg.connect(url, timeout=60)
    try:
        print("Applying f48fc97f1dff (channels, verified_subscribers)...")
        # For channels
        try:
            await conn.execute("ALTER TABLE channels ADD COLUMN subscriber_limit INTEGER")
            print("Added subscriber_limit to channels")
        except Exception as e:
            print(f"channels.subscriber_limit: {e}")
            
        try:
            await conn.execute("ALTER TABLE channels ADD COLUMN current_subscriber_count INTEGER DEFAULT 0 NOT NULL")
            print("Added current_subscriber_count to channels")
        except Exception as e:
            print(f"channels.current_subscriber_count: {e}")

        # For verified_subscribers table
        try:
            await conn.execute("""
            CREATE TABLE verified_subscribers (
                id SERIAL NOT NULL, 
                user_id BIGINT NOT NULL, 
                channel_id INTEGER NOT NULL, 
                verified_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
                PRIMARY KEY (id), 
                FOREIGN KEY(channel_id) REFERENCES channels (id) ON DELETE CASCADE, 
                UNIQUE (user_id, channel_id)
            )
            """)
            await conn.execute("CREATE INDEX ix_verified_subscribers_channel_id ON verified_subscribers (channel_id)")
            await conn.execute("CREATE INDEX ix_verified_subscribers_id ON verified_subscribers (id)")
            await conn.execute("CREATE INDEX ix_verified_subscribers_user_id ON verified_subscribers (user_id)")
            print("Created verified_subscribers table")
        except Exception as e:
            print(f"verified_subscribers table: {e}")

        print("\nApplying 2fb109c075d0 (auto index fields)...")
        try:
            await conn.execute("ALTER TABLE movies ADD COLUMN source_chat_id BIGINT")
            await conn.execute("ALTER TABLE movies ADD COLUMN source_topic_id INTEGER")
            print("Added source fields to movies")
        except Exception as e:
            print(f"movies source fields: {e}")

        try:
            await conn.execute("ALTER TABLE series ADD COLUMN source_chat_id BIGINT")
            await conn.execute("ALTER TABLE series ADD COLUMN source_topic_id INTEGER")
            print("Added source fields to series")
        except Exception as e:
            print(f"series source fields: {e}")

        try:
            await conn.execute("ALTER TABLE episodes ADD COLUMN source_message_id BIGINT")
            print("Added source_message_id to episodes")
        except Exception as e:
            print(f"episodes source_message_id: {e}")

        try:
            await conn.execute("ALTER TABLE episodes ADD CONSTRAINT uq_season_episode_number UNIQUE (season_id, episode_number)")
            print("Added UNIQUE constraint to episodes")
        except Exception as e:
            print(f"episodes UNIQUE constraint: {e}")

        # Set alembic version
        try:
            await conn.execute("UPDATE alembic_version SET version_num='2fb109c075d0'")
            print("Alembic version updated to 2fb109c075d0")
        except Exception as e:
            print(f"Failed to update alembic version: {e}")

    finally:
        await conn.close()
        print("Connection closed.")

if __name__ == "__main__":
    asyncio.run(apply_all_missing_migrations())
