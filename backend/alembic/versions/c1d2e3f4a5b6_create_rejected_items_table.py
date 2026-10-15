"""create rejected_items table

Revision ID: c1d2e3f4a5b6
Revises: b3a1c2d4e5f6
Create Date: 2026-10-16 01:52:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'b3a1c2d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Dialect-agnostic JSON/JSONB column type
    json_col = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql')

    op.create_table(
        'rejected_items',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('media_type', sa.String(length=20), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('source_key', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('payload', json_col, nullable=False, server_default=sa.text("'{}'")),
        sa.Column('defects', json_col, nullable=False, server_default=sa.text("'[]'")),
        sa.Column('media_id', sa.BigInteger(), nullable=True),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='rejected'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source', 'source_key', name='uq_rejected_items_source_key')
    )
    op.create_index(op.f('ix_rejected_items_id'), 'rejected_items', ['id'], unique=False)
    op.create_index(op.f('ix_rejected_items_status'), 'rejected_items', ['status'], unique=False)
    op.create_index(op.f('ix_rejected_items_source'), 'rejected_items', ['source'], unique=False)
    op.create_index(op.f('ix_rejected_items_source_key'), 'rejected_items', ['source_key'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_rejected_items_source_key'), table_name='rejected_items')
    op.drop_index(op.f('ix_rejected_items_source'), table_name='rejected_items')
    op.drop_index(op.f('ix_rejected_items_status'), table_name='rejected_items')
    op.drop_index(op.f('ix_rejected_items_id'), table_name='rejected_items')
    op.drop_table('rejected_items')
