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
    # 1. Mavjud tarixiy dublikat tmdb_id larni xavfsiz tozalash (DELETE emas, faqat dublikatlarni NULL qilish)
    op.execute(sa.text("""
        UPDATE movies
        SET tmdb_id = NULL
        WHERE id IN (
            SELECT id FROM (
                SELECT id, ROW_NUMBER() OVER (PARTITION BY tmdb_id ORDER BY id ASC) as rn
                FROM movies
                WHERE tmdb_id IS NOT NULL
            ) t WHERE t.rn > 1
        )
    """))

    op.execute(sa.text("""
        UPDATE series
        SET tmdb_id = NULL
        WHERE id IN (
            SELECT id FROM (
                SELECT id, ROW_NUMBER() OVER (PARTITION BY tmdb_id ORDER BY id ASC) as rn
                FROM series
                WHERE tmdb_id IS NOT NULL
            ) t WHERE t.rn > 1
        )
    """))

    # 2. Additive unique partial indexes: only non-null tmdb_id values must be unique
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
