"""Add subscriber limit, count and verified_subscriptions

Revision ID: f48fc97f1dff
Revises: 5f880cb7b638
Create Date: 2026-07-14 15:04:23.157255
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f48fc97f1dff'
down_revision: Union[str, None] = '5f880cb7b638'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add subscriber_limit and current_subscriber_count to mandatory_channels
    op.add_column('mandatory_channels', sa.Column('subscriber_limit', sa.Integer(), nullable=True))
    op.add_column('mandatory_channels', sa.Column('current_subscriber_count', sa.Integer(), server_default='0', nullable=False))
    
    # Create verified_subscriptions table
    op.create_table('verified_subscriptions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('channel_id', sa.Integer(), nullable=False),
    sa.Column('verified_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['channel_id'], ['mandatory_channels.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'channel_id', name='uq_user_channel_subscription')
    )
    op.create_index(op.f('ix_verified_subscriptions_channel_id'), 'verified_subscriptions', ['channel_id'], unique=False)
    op.create_index(op.f('ix_verified_subscriptions_id'), 'verified_subscriptions', ['id'], unique=False)
    op.create_index(op.f('ix_verified_subscriptions_user_id'), 'verified_subscriptions', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop verified_subscriptions table
    op.drop_index(op.f('ix_verified_subscriptions_user_id'), table_name='verified_subscriptions')
    op.drop_index(op.f('ix_verified_subscriptions_id'), table_name='verified_subscriptions')
    op.drop_index(op.f('ix_verified_subscriptions_channel_id'), table_name='verified_subscriptions')
    op.drop_table('verified_subscriptions')
    
    # Drop columns from mandatory_channels
    op.drop_column('mandatory_channels', 'current_subscriber_count')
    op.drop_column('mandatory_channels', 'subscriber_limit')
