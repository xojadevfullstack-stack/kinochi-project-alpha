"""add clip_mode and hook_text to smm_clip_jobs and 28s default duration

Revision ID: i9d0e1f2a3b4
Revises: h8c9d0e1f2a3
Create Date: 2026-11-27 00:10:00.000000
"""
from typing import Sequence, Union
from alembic import op

revision: str = "i9d0e1f2a3b4"
down_revision: Union[str, None] = "h8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE smm_clip_jobs ADD COLUMN IF NOT EXISTS clip_mode VARCHAR(20) NOT NULL DEFAULT 'scene'")
    op.execute("ALTER TABLE smm_clip_jobs ADD COLUMN IF NOT EXISTS hook_text TEXT")
    op.execute("ALTER TABLE smm_settings ALTER COLUMN clip_duration_sec SET DEFAULT 28")


def downgrade() -> None:
    # Non-destructive downgrade to preserve SMM job metadata
    pass
