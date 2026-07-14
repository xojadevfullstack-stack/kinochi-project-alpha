"""auto index fields

Revision ID: 2fb109c075d0
Revises: f48fc97f1dff
Create Date: 2026-07-14 15:57:55.585074
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2fb109c075d0'
down_revision: Union[str, None] = 'f48fc97f1dff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add to movies
    op.add_column('movies', sa.Column('source_chat_id', sa.BigInteger(), nullable=True))
    op.add_column('movies', sa.Column('source_topic_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_movies_source_chat_id'), 'movies', ['source_chat_id'], unique=False)
    op.create_index(op.f('ix_movies_source_topic_id'), 'movies', ['source_topic_id'], unique=False)
    
    # Add to series
    op.add_column('series', sa.Column('source_chat_id', sa.BigInteger(), nullable=True))
    op.add_column('series', sa.Column('source_topic_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_series_source_chat_id'), 'series', ['source_chat_id'], unique=False)
    op.create_index(op.f('ix_series_source_topic_id'), 'series', ['source_topic_id'], unique=False)

    # Add to episodes
    op.add_column('episodes', sa.Column('source_message_id', sa.BigInteger(), nullable=True))
    op.create_index(op.f('ix_episodes_source_message_id'), 'episodes', ['source_message_id'], unique=False)
    op.create_unique_constraint('uq_season_episode_number', 'episodes', ['season_id', 'episode_number'])


def downgrade() -> None:
    # Remove from episodes
    op.drop_constraint('uq_season_episode_number', 'episodes', type_='unique')
    op.drop_index(op.f('ix_episodes_source_message_id'), table_name='episodes')
    op.drop_column('episodes', 'source_message_id')
    
    # Remove from series
    op.drop_index(op.f('ix_series_source_topic_id'), table_name='series')
    op.drop_index(op.f('ix_series_source_chat_id'), table_name='series')
    op.drop_column('series', 'source_topic_id')
    op.drop_column('series', 'source_chat_id')

    # Remove from movies
    op.drop_index(op.f('ix_movies_source_topic_id'), table_name='movies')
    op.drop_index(op.f('ix_movies_source_chat_id'), table_name='movies')
    op.drop_column('movies', 'source_topic_id')
    op.drop_column('movies', 'source_chat_id')
