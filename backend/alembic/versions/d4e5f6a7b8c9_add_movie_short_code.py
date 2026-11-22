"""add movies.short_code and update smm default bot_username

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-11-22 19:10:00.000000
"""
from typing import Sequence, Union
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE movies ADD COLUMN IF NOT EXISTS short_code VARCHAR(16)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_movies_short_code ON movies(short_code)")
    # Backfill existing movies with sequential 4-digit codes starting at 1001
    op.execute("""
        WITH numbered AS (
            SELECT id, (1000 + ROW_NUMBER() OVER (ORDER BY id))::text AS sc
            FROM movies
            WHERE short_code IS NULL
        )
        UPDATE movies m
        SET short_code = n.sc
        FROM numbered n
        WHERE m.id = n.id
          AND NOT EXISTS (SELECT 1 FROM movies x WHERE x.short_code = n.sc OR x.code = n.sc)
    """)
    op.execute("""
        UPDATE smm_settings
        SET bot_username = '@MediaPlusOfficialBot'
        WHERE bot_username = '@kinochi_mvp_bot'
    """)


def downgrade() -> None:
    # Non-destructive downgrade to preserve production short_codes (ADR-009)
    op.execute("""
        UPDATE smm_settings
        SET bot_username = '@kinochi_mvp_bot'
        WHERE bot_username = '@MediaPlusOfficialBot'
    """)
