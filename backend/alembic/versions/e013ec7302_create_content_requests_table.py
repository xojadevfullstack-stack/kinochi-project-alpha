"""create content_requests table

Revision ID: e013ec7302
Revises: d012ec7201
Create Date: 2026-10-25 08:50:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa  # noqa: F401


revision: str = 'e013ec7302'
down_revision: Union[str, None] = 'd012ec7201'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS content_requests (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            original_title VARCHAR(255),
            media_type VARCHAR(20) DEFAULT 'movie' NOT NULL,
            release_year INTEGER,
            poster_url VARCHAR(1024),
            overview TEXT,
            tmdb_id INTEGER,
            kinopoisk_id INTEGER,
            preferred_language VARCHAR(50) DEFAULT 'uz' NOT NULL,
            user_contact VARCHAR(255),
            telegram_user_id BIGINT,
            ip_address VARCHAR(45),
            vote_count INTEGER DEFAULT 1 NOT NULL,
            status VARCHAR(20) DEFAULT 'pending' NOT NULL,
            admin_notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_content_requests_title ON content_requests(title);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_content_requests_tmdb_id ON content_requests(tmdb_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_content_requests_kinopoisk_id ON content_requests(kinopoisk_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_content_requests_telegram_user_id ON content_requests(telegram_user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_content_requests_status ON content_requests(status);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_content_requests_tmdb_media ON content_requests(tmdb_id, media_type);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS content_requests CASCADE;")
