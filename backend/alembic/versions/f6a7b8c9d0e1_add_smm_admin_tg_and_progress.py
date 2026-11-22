"""add smm_settings.admin_telegram_id and smm_clip_jobs progress fields

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-11-23 00:02:00.000000
"""
from typing import Sequence, Union
from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE smm_settings ADD COLUMN IF NOT EXISTS admin_telegram_id VARCHAR(64)")
    op.execute("ALTER TABLE smm_clip_jobs ADD COLUMN IF NOT EXISTS progress_pct INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE smm_clip_jobs ADD COLUMN IF NOT EXISTS progress_stage VARCHAR(64)")


def downgrade() -> None:
    # Non-destructive downgrade to keep settings and job history safe
    pass
