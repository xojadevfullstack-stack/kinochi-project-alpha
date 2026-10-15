"""add unique partial index for tmdb_id on movies and series

Revision ID: d4e5f6a1b2c3
Revises: c1d2e3f4a5b6
Create Date: 2026-10-16 03:15:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a1b2c3'
down_revision: Union[str, None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Additive unique partial indexes: only non-null tmdb_id values must be unique
    op.create_index(
        'uq_movies_tmdb_id',
        'movies',
        ['tmdb_id'],
        unique=True,
        postgresql_where=sa.text('tmdb_id IS NOT NULL')
    )
    op.create_index(
        'uq_series_tmdb_id',
        'series',
        ['tmdb_id'],
        unique=True,
        postgresql_where=sa.text('tmdb_id IS NOT NULL')
    )


def downgrade() -> None:
    op.drop_index('uq_series_tmdb_id', table_name='series')
    op.drop_index('uq_movies_tmdb_id', table_name='movies')
