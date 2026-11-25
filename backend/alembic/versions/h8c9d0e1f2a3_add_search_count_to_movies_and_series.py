"""add search_count to movies and series

Revision ID: h8c9d0e1f2a3
Revises: g7b8c9d0e1f2
Create Date: 2026-11-25 18:50:00.000000
"""
from typing import Sequence, Union
from alembic import op

revision: str = "h8c9d0e1f2a3"
down_revision: Union[str, None] = "g7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE movies ADD COLUMN IF NOT EXISTS search_count INTEGER NOT NULL DEFAULT 0")
    op.execute("CREATE INDEX IF NOT EXISTS ix_movies_search_count ON movies (search_count)")
    op.execute("ALTER TABLE series ADD COLUMN IF NOT EXISTS search_count INTEGER NOT NULL DEFAULT 0")
    op.execute("CREATE INDEX IF NOT EXISTS ix_series_search_count ON series (search_count)")


def downgrade() -> None:
    # Non-destructive downgrade to preserve search ranking data
    pass
