"""set default pending on publish_status in movies and series

Revision ID: e8f9a0b1c2d3
Revises: a1b2c3d4e5f6
Create Date: 2026-10-16 08:15:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8f9a0b1c2d3'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # movies va series jadvallarida publish_status ustunining default qiymatini 'pending' ga o'zgartirish (idempotent)
    op.alter_column('movies', 'publish_status', server_default='pending')
    op.alter_column('series', 'publish_status', server_default='pending')


def downgrade() -> None:
    op.alter_column('series', 'publish_status', server_default='published')
    op.alter_column('movies', 'publish_status', server_default='published')
