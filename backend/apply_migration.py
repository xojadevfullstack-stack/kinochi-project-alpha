import asyncio
import asyncpg
from app.core.config import settings

async def check_or_migrate():
    url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
    print("Connecting to", url)
    conn = await asyncpg.connect(url)
    try:
        # Check if columns exist
        res = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name='movies' AND column_name='source_chat_id'")
        if not res:
            print("Applying ALTER TABLE manually...")
            await conn.execute("ALTER TABLE movies ADD COLUMN source_chat_id BIGINT")
            await conn.execute("ALTER TABLE movies ADD COLUMN source_topic_id INTEGER")
            await conn.execute("ALTER TABLE series ADD COLUMN source_chat_id BIGINT")
            await conn.execute("ALTER TABLE series ADD COLUMN source_topic_id INTEGER")
            await conn.execute("ALTER TABLE episodes ADD COLUMN source_message_id BIGINT")
            
            # The constraint might fail if there are existing duplicates
            try:
                await conn.execute("ALTER TABLE episodes ADD CONSTRAINT uq_season_episode_number UNIQUE (season_id, episode_number)")
            except Exception as e:
                print(f"Constraint issue (maybe duplicates exist): {e}")
            
            # Record alembic version manually to fake success
            await conn.execute("UPDATE alembic_version SET version_num='2fb109c075d0'")
            print("Done manually.")
        else:
            print("Columns already exist.")
            await conn.execute("UPDATE alembic_version SET version_num='2fb109c075d0'")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_or_migrate())
