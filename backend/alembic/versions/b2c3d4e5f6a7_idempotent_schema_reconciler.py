"""idempotent schema reconciler for missing tables and columns

Revision ID: b2c3d4e5f6a7
Revises: 9c8d7e6f5a4b
Create Date: 2026-11-01 18:35:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa  # noqa: F401


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = '9c8d7e6f5a4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. series_sources table
    op.execute("""
        CREATE TABLE IF NOT EXISTS series_sources (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            type VARCHAR(50) DEFAULT 'kanal' NOT NULL,
            chat_id BIGINT NOT NULL,
            topic_id INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_series_sources_chat_id ON series_sources(chat_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_series_sources_topic_id ON series_sources(topic_id)")
    op.execute("ALTER TABLE series_sources ADD COLUMN IF NOT EXISTS type VARCHAR(50) DEFAULT 'kanal' NOT NULL")
    op.execute("ALTER TABLE series_sources ADD COLUMN IF NOT EXISTS chat_id BIGINT")
    op.execute("ALTER TABLE series_sources ADD COLUMN IF NOT EXISTS topic_id INTEGER")

    # 2. collections table
    op.execute("""
        CREATE TABLE IF NOT EXISTS collections (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            slug VARCHAR(255) NOT NULL,
            description TEXT,
            poster_url VARCHAR(1024),
            banner_url VARCHAR(1024),
            is_franchise BOOLEAN DEFAULT TRUE NOT NULL,
            category_type VARCHAR(50) DEFAULT 'franchise' NOT NULL,
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            sort_order INTEGER DEFAULT 0 NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_collections_slug ON collections(slug)")
    op.execute("ALTER TABLE collections ADD COLUMN IF NOT EXISTS is_franchise BOOLEAN DEFAULT TRUE NOT NULL")
    op.execute("ALTER TABLE collections ADD COLUMN IF NOT EXISTS category_type VARCHAR(50) DEFAULT 'franchise' NOT NULL")
    op.execute("ALTER TABLE collections ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE NOT NULL")
    op.execute("ALTER TABLE collections ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0 NOT NULL")

    # 3. collection_items table
    op.execute("""
        CREATE TABLE IF NOT EXISTS collection_items (
            id SERIAL PRIMARY KEY,
            collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
            movie_id INTEGER REFERENCES movies(id) ON DELETE CASCADE,
            series_id INTEGER REFERENCES series(id) ON DELETE CASCADE,
            chronological_order INTEGER DEFAULT 1 NOT NULL,
            release_order INTEGER DEFAULT 1 NOT NULL,
            timeline_event_desc VARCHAR(255),
            is_locked BOOLEAN DEFAULT FALSE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_collection_items_collection_id ON collection_items(collection_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_collection_items_movie_id ON collection_items(movie_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_collection_items_series_id ON collection_items(series_id)")
    op.execute("ALTER TABLE collection_items ADD COLUMN IF NOT EXISTS chronological_order INTEGER DEFAULT 1 NOT NULL")
    op.execute("ALTER TABLE collection_items ADD COLUMN IF NOT EXISTS release_order INTEGER DEFAULT 1 NOT NULL")
    op.execute("ALTER TABLE collection_items ADD COLUMN IF NOT EXISTS timeline_event_desc VARCHAR(255)")
    op.execute("ALTER TABLE collection_items ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE NOT NULL")

    # 4. series_subscriptions table
    op.execute("""
        CREATE TABLE IF NOT EXISTS series_subscriptions (
            id SERIAL PRIMARY KEY,
            series_id INTEGER NOT NULL REFERENCES series(id) ON DELETE CASCADE,
            telegram_user_id BIGINT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            CONSTRAINT uq_series_user_subscription UNIQUE (series_id, telegram_user_id)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_series_subscriptions_series ON series_subscriptions(series_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_series_subscriptions_user ON series_subscriptions(telegram_user_id)")

    # 5. reports table
    op.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id SERIAL PRIMARY KEY,
            media_type VARCHAR(20) NOT NULL,
            movie_id INTEGER REFERENCES movies(id) ON DELETE SET NULL,
            series_id INTEGER REFERENCES series(id) ON DELETE SET NULL,
            episode_id INTEGER REFERENCES episodes(id) ON DELETE SET NULL,
            issue_type VARCHAR(50) NOT NULL,
            description TEXT,
            file_url VARCHAR(1024),
            file_type VARCHAR(20),
            status VARCHAR(20) DEFAULT 'pending' NOT NULL,
            ip_address VARCHAR(45),
            telegram_user_id BIGINT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_reports_status ON reports(status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_reports_telegram_user_id ON reports(telegram_user_id)")
    op.execute("ALTER TABLE reports ADD COLUMN IF NOT EXISTS issue_type VARCHAR(50)")
    op.execute("ALTER TABLE reports ADD COLUMN IF NOT EXISTS file_url VARCHAR(1024)")
    op.execute("ALTER TABLE reports ADD COLUMN IF NOT EXISTS file_type VARCHAR(20)")
    op.execute("ALTER TABLE reports ADD COLUMN IF NOT EXISTS ip_address VARCHAR(45)")

    # 6. blacklist table
    op.execute("""
        CREATE TABLE IF NOT EXISTS blacklist (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255),
            url VARCHAR(1024),
            reason VARCHAR(255) DEFAULT 'Buzilgan / bo''sh kontent',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_blacklist_title ON blacklist(title)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_blacklist_url ON blacklist(url)")

    # 7. movies columns
    op.execute("ALTER TABLE movies ADD COLUMN IF NOT EXISTS is_18_plus BOOLEAN DEFAULT FALSE NOT NULL")
    op.execute("ALTER TABLE movies ADD COLUMN IF NOT EXISTS source_chat_id BIGINT")
    op.execute("ALTER TABLE movies ADD COLUMN IF NOT EXISTS source_topic_id INTEGER")
    op.execute("ALTER TABLE movies ADD COLUMN IF NOT EXISTS source_type VARCHAR(50) DEFAULT 'uzmovi'")
    op.execute("ALTER TABLE movies ADD COLUMN IF NOT EXISTS custom_source_name VARCHAR(255)")
    op.execute("ALTER TABLE movies ADD COLUMN IF NOT EXISTS custom_source_logo VARCHAR(1024)")
    op.execute("ALTER TABLE movies ADD COLUMN IF NOT EXISTS tmdb_id INTEGER")
    op.execute("ALTER TABLE movies ADD COLUMN IF NOT EXISTS tmdb_rating FLOAT")
    op.execute("ALTER TABLE movies ADD COLUMN IF NOT EXISTS kinochi_rating FLOAT")
    op.execute("ALTER TABLE movies ADD COLUMN IF NOT EXISTS kinochi_votes_count INTEGER DEFAULT 0 NOT NULL")

    # 8. series columns & source_id FK
    op.execute("ALTER TABLE series ADD COLUMN IF NOT EXISTS is_18_plus BOOLEAN DEFAULT FALSE NOT NULL")
    op.execute("ALTER TABLE series ADD COLUMN IF NOT EXISTS source_id INTEGER")
    op.execute("ALTER TABLE series ADD COLUMN IF NOT EXISTS source_type VARCHAR(50) DEFAULT 'uzmovi'")
    op.execute("ALTER TABLE series ADD COLUMN IF NOT EXISTS custom_source_name VARCHAR(255)")
    op.execute("ALTER TABLE series ADD COLUMN IF NOT EXISTS custom_source_logo VARCHAR(1024)")
    op.execute("ALTER TABLE series ADD COLUMN IF NOT EXISTS tmdb_id INTEGER")
    op.execute("ALTER TABLE series ADD COLUMN IF NOT EXISTS tmdb_rating FLOAT")
    op.execute("ALTER TABLE series ADD COLUMN IF NOT EXISTS kinochi_rating FLOAT")
    op.execute("ALTER TABLE series ADD COLUMN IF NOT EXISTS kinochi_votes_count INTEGER DEFAULT 0 NOT NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_series_source_id ON series(source_id)")

    op.execute("""
        DO $$
        DECLARE
            orphan_count integer;
        BEGIN
            -- 1. Agar constraint yo'q bo'lsa, NOT VALID bilan yaratish (mavjud qatorlarni bloklamaslik uchun)
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_series_source_id'
            ) THEN
                ALTER TABLE series
                ADD CONSTRAINT fk_series_source_id
                FOREIGN KEY (source_id) REFERENCES series_sources(id)
                ON DELETE SET NULL
                NOT VALID;
            END IF;

            -- 2. Yetim (orphan) qatorlarni tekshirish
            SELECT count(*) INTO orphan_count
            FROM series s
            WHERE s.source_id IS NOT NULL
              AND NOT EXISTS (SELECT 1 FROM series_sources ss WHERE ss.id = s.source_id);

            -- 3. Agar yetim qatorlar bo'lmasa VALIDATE qilish, aks holda ogohlantirish berish
            IF orphan_count > 0 THEN
                RAISE WARNING 'fk_series_source_id: % ta yetim (orphan) qator topildi; VALIDATE CONSTRAINT keyinga qoldirildi', orphan_count;
            ELSE
                ALTER TABLE series VALIDATE CONSTRAINT fk_series_source_id;
            END IF;
        EXCEPTION
            WHEN duplicate_object THEN
                NULL;
        END $$;
    """)


def downgrade() -> None:
    # Destructive drop of data tables in production is intentionally avoided (no-op with safety message)
    # to protect existing collections, reports, blacklist and user subscriptions.
    pass
