-- Channels jadvaliga yangi ustunlar qo'shish
ALTER TABLE channels ADD COLUMN IF NOT EXISTS subscriber_limit INTEGER;
ALTER TABLE channels ADD COLUMN IF NOT EXISTS current_subscriber_count INTEGER DEFAULT 0 NOT NULL;

-- Verified Subscribers jadvalini yaratish
CREATE TABLE IF NOT EXISTS verified_subscribers (
    id SERIAL NOT NULL, 
    user_id BIGINT NOT NULL, 
    channel_id INTEGER NOT NULL, 
    verified_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(channel_id) REFERENCES channels (id) ON DELETE CASCADE, 
    UNIQUE (user_id, channel_id)
);
CREATE INDEX IF NOT EXISTS ix_verified_subscribers_channel_id ON verified_subscribers (channel_id);
CREATE INDEX IF NOT EXISTS ix_verified_subscribers_id ON verified_subscribers (id);
CREATE INDEX IF NOT EXISTS ix_verified_subscribers_user_id ON verified_subscribers (user_id);

-- Movies jadvaliga yangi ustunlar qo'shish
ALTER TABLE movies ADD COLUMN IF NOT EXISTS source_chat_id BIGINT;
ALTER TABLE movies ADD COLUMN IF NOT EXISTS source_topic_id INTEGER;

-- Series jadvaliga yangi ustunlar qo'shish
ALTER TABLE series ADD COLUMN IF NOT EXISTS source_chat_id BIGINT;
ALTER TABLE series ADD COLUMN IF NOT EXISTS source_topic_id INTEGER;

-- Episodes jadvaliga yangi ustunlar va qoida (constraint) qo'shish
ALTER TABLE episodes ADD COLUMN IF NOT EXISTS source_message_id BIGINT;

-- Eslatma: agar allaqachon bir xil qismlar (duplicate) bo'lsa, bu qator xato berishi mumkin, ularni o'chirib keyin ishga tushiring
ALTER TABLE episodes ADD CONSTRAINT uq_season_episode_number UNIQUE (season_id, episode_number);

-- Alembic (Migration) versiyasini so'nggi versiyaga o'tkazib qo'yish
UPDATE alembic_version SET version_num='2fb109c075d0';
