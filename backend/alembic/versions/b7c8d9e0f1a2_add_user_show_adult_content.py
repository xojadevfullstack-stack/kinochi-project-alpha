"""add users.show_adult_content preference column

Revision ID: b7c8d9e0f1a2
Revises: f6a7b8c9d0e1
Create Date: 2026-11-25 18:05:00.000000
"""
from typing import Sequence, Union
from alembic import op

revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS show_adult_content BOOLEAN NOT NULL DEFAULT FALSE")


def downgrade() -> None:
    # Non-destructive downgrade to keep user preferences safe
    pass
