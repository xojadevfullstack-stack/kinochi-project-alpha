"""create seed_candidates table

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-10-16 04:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. seed_candidates jadvalini yaratish (faqat additiv)
    op.create_table(
        'seed_candidates',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('kind', sa.String(length=20), nullable=False),
        sa.Column('tmdb_id', sa.BigInteger(), nullable=False),
        sa.Column('title_en', sa.String(length=255), nullable=True),
        sa.Column('title_ru', sa.String(length=255), nullable=True),
        sa.Column('original_title', sa.String(length=255), nullable=True),
        sa.Column('release_year', sa.Integer(), nullable=True),
        sa.Column('vote_average', sa.Float(), nullable=True),
        sa.Column('vote_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('popularity', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('is_anime', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('status', sa.String(length=30), server_default='new', nullable=False),
        sa.Column('matches', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_searched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('kind', 'tmdb_id', name='uq_seed_candidates_kind_tmdb_id')
    )
    op.create_index(op.f('ix_seed_candidates_id'), 'seed_candidates', ['id'], unique=False)
    op.create_index(op.f('ix_seed_candidates_kind'), 'seed_candidates', ['kind'], unique=False)
    op.create_index(op.f('ix_seed_candidates_tmdb_id'), 'seed_candidates', ['tmdb_id'], unique=False)
    op.create_index(op.f('ix_seed_candidates_release_year'), 'seed_candidates', ['release_year'], unique=False)
    op.create_index(op.f('ix_seed_candidates_is_anime'), 'seed_candidates', ['is_anime'], unique=False)
    op.create_index(op.f('ix_seed_candidates_status'), 'seed_candidates', ['status'], unique=False)


def downgrade() -> None:
    # Additiv qoida: pastga tushirish talab etilganda indekslar va jadval olib tashlanadi
    op.drop_index(op.f('ix_seed_candidates_status'), table_name='seed_candidates')
    op.drop_index(op.f('ix_seed_candidates_is_anime'), table_name='seed_candidates')
    op.drop_index(op.f('ix_seed_candidates_release_year'), table_name='seed_candidates')
    op.drop_index(op.f('ix_seed_candidates_tmdb_id'), table_name='seed_candidates')
    op.drop_index(op.f('ix_seed_candidates_kind'), table_name='seed_candidates')
    op.drop_index(op.f('ix_seed_candidates_id'), table_name='seed_candidates')
    op.drop_table('seed_candidates')
