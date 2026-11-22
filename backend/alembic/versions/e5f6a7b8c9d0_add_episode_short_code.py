"""add episodes.short_code shared with movies.short_code global sequence

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-11-22 20:30:00.000000
"""
from typing import Sequence, Union
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE episodes ADD COLUMN IF NOT EXISTS short_code VARCHAR(16)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_episodes_short_code ON episodes(short_code)")
    # Backfill existing episodes after max(movies.short_code, episodes.short_code, 1000)
    op.execute("""
        WITH base AS (
            SELECT GREATEST(
                1000,
                COALESCE((SELECT MAX(short_code::int) FROM movies WHERE short_code ~ '^[0-9]+$' AND LENGTH(short_code) <= 6), 1000),
                COALESCE((SELECT MAX(short_code::int) FROM episodes WHERE short_code ~ '^[0-9]+$' AND LENGTH(short_code) <= 6), 1000)
            ) AS start_num
        ),
        numbered AS (
            SELECT e.id, (b.start_num + ROW_NUMBER() OVER (ORDER BY e.id))::text AS sc
            FROM episodes e
            CROSS JOIN base b
            WHERE e.short_code IS NULL
        )
        UPDATE episodes e
        SET short_code = n.sc
        FROM numbered n
        WHERE e.id = n.id
          AND NOT EXISTS (SELECT 1 FROM movies m WHERE m.short_code = n.sc OR m.code = n.sc)
          AND NOT EXISTS (SELECT 1 FROM episodes x WHERE x.short_code = n.sc OR x.code = n.sc)
    """)


def downgrade() -> None:
    # Non-destructive downgrade to preserve production short_codes (ADR-009)
    pass
