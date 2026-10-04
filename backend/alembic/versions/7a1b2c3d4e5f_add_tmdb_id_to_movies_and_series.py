"""add tmdb_id to movies and series

Revision ID: 7a1b2c3d4e5f
Revises: 55501de0fffd
Create Date: 2026-10-04 13:25:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a1b2c3d4e5f'
down_revision: Union[str, None] = '55501de0fffd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('movies', sa.Column('tmdb_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_movies_tmdb_id'), 'movies', ['tmdb_id'], unique=False)
    op.add_column('series', sa.Column('tmdb_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_series_tmdb_id'), 'series', ['tmdb_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_series_tmdb_id'), table_name='series')
    op.drop_column('series', 'tmdb_id')
    op.drop_index(op.f('ix_movies_tmdb_id'), table_name='movies')
    op.drop_column('movies', 'tmdb_id')
