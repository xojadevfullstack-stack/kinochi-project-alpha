"""add publish_status to movies and series

Revision ID: b3a1c2d4e5f6
Revises: 7a1b2c3d4e5f
Create Date: 2026-10-16 00:48:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3a1c2d4e5f6'
down_revision: Union[str, None] = '7a1b2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. movies jadvaliga publish_status ustunini qo'shish
    # server_default='published' orqali mavjud barcha qatorlar 'published' bo'lib qoladi
    op.add_column(
        'movies',
        sa.Column('publish_status', sa.String(length=50), nullable=False, server_default='published')
    )
    op.create_index(op.f('ix_movies_publish_status'), 'movies', ['publish_status'], unique=False)
    # Kelajakdagi yangi yozuvlar uchun default 'pending' ga o'tkaziladi
    op.alter_column('movies', 'publish_status', server_default='pending')

    # 2. series jadvaliga publish_status ustunini qo'shish
    # server_default='published' orqali mavjud barcha qatorlar 'published' bo'lib qoladi
    op.add_column(
        'series',
        sa.Column('publish_status', sa.String(length=50), nullable=False, server_default='published')
    )
    op.create_index(op.f('ix_series_publish_status'), 'series', ['publish_status'], unique=False)
    # Kelajakdagi yangi yozuvlar uchun default 'pending' ga o'tkaziladi
    op.alter_column('series', 'publish_status', server_default='pending')


def downgrade() -> None:
    op.drop_index(op.f('ix_series_publish_status'), table_name='series')
    op.drop_column('series', 'publish_status')
    op.drop_index(op.f('ix_movies_publish_status'), table_name='movies')
    op.drop_column('movies', 'publish_status')
