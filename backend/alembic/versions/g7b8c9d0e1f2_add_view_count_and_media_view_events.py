"""add view_count to movies/series and media_view_events table

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-11-25 18:00:00.000000
"""
from typing import Sequence, Union
from alembic import op

revision: str = "g7b8c9d0e1f2"
down_revision: Union[str, None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE movies ADD COLUMN IF NOT EXISTS view_count INTEGER NOT NULL DEFAULT 0")
    op.execute("CREATE INDEX IF NOT EXISTS ix_movies_view_count ON movies (view_count)")
    op.execute("ALTER TABLE series ADD COLUMN IF NOT EXISTS view_count INTEGER NOT NULL DEFAULT 0")
    op.execute("CREATE INDEX IF NOT EXISTS ix_series_view_count ON series (view_count)")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS media_view_events (
            id SERIAL PRIMARY KEY,
            media_type VARCHAR(20) NOT NULL,
            movie_id INTEGER REFERENCES movies(id) ON DELETE CASCADE,
            series_id INTEGER REFERENCES series(id) ON DELETE CASCADE,
            episode_id INTEGER REFERENCES episodes(id) ON DELETE SET NULL,
            source VARCHAR(20) NOT NULL DEFAULT 'web',
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_media_view_events_created_at ON media_view_events (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_media_view_events_user_id ON media_view_events (user_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_media_view_events_created_source ON media_view_events (created_at, source)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_media_view_events_movie_created ON media_view_events (movie_id, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_media_view_events_series_created ON media_view_events (series_id, created_at)"
    )


def downgrade() -> None:
    # Non-destructive downgrade to preserve analytics history in production
    pass
