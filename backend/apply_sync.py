import psycopg2
from app.core.config import settings

def apply_all_missing_migrations():
    url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
    url = url.replace("ssl=require", "sslmode=require")
    print("Connecting to", url)
    conn = psycopg2.connect(url)
    conn.autocommit = True
    cursor = conn.cursor()
    try:
        print("Applying f48fc97f1dff (channels, verified_subscribers)...")
        
        try:
            cursor.execute("ALTER TABLE channels ADD COLUMN subscriber_limit INTEGER")
            print("Added subscriber_limit to channels")
        except Exception as e:
            print(f"channels.subscriber_limit: {e}")
            
        try:
            cursor.execute("ALTER TABLE channels ADD COLUMN current_subscriber_count INTEGER DEFAULT 0 NOT NULL")
            print("Added current_subscriber_count to channels")
        except Exception as e:
            print(f"channels.current_subscriber_count: {e}")

        try:
            cursor.execute("""
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
            cursor.execute("CREATE INDEX ix_verified_subscribers_channel_id ON verified_subscribers (channel_id)")
            cursor.execute("CREATE INDEX ix_verified_subscribers_id ON verified_subscribers (id)")
            cursor.execute("CREATE INDEX ix_verified_subscribers_user_id ON verified_subscribers (user_id)")
            print("Created verified_subscribers table")
        except Exception as e:
            print(f"verified_subscribers table: {e}")

        print("\nApplying 2fb109c075d0 (auto index fields)...")
        try:
            cursor.execute("ALTER TABLE movies ADD COLUMN source_chat_id BIGINT")
            cursor.execute("ALTER TABLE movies ADD COLUMN source_topic_id INTEGER")
            print("Added source fields to movies")
        except Exception as e:
            print(f"movies source fields: {e}")

        try:
            cursor.execute("ALTER TABLE series ADD COLUMN source_chat_id BIGINT")
            cursor.execute("ALTER TABLE series ADD COLUMN source_topic_id INTEGER")
            print("Added source fields to series")
        except Exception as e:
            print(f"series source fields: {e}")

        try:
            cursor.execute("ALTER TABLE episodes ADD COLUMN source_message_id BIGINT")
            print("Added source_message_id to episodes")
        except Exception as e:
            print(f"episodes source_message_id: {e}")

        try:
            cursor.execute("ALTER TABLE episodes ADD CONSTRAINT uq_season_episode_number UNIQUE (season_id, episode_number)")
            print("Added UNIQUE constraint to episodes")
        except Exception as e:
            print(f"episodes UNIQUE constraint: {e}")

        try:
            cursor.execute("UPDATE alembic_version SET version_num='2fb109c075d0'")
            print("Alembic version updated to 2fb109c075d0")
        except Exception as e:
            print(f"Failed to update alembic version: {e}")

    finally:
        cursor.close()
        conn.close()
        print("Connection closed.")

if __name__ == "__main__":
    apply_all_missing_migrations()
