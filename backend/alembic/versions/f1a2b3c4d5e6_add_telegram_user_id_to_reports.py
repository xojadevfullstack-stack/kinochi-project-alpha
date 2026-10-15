"""add telegram_user_id to reports

Revision ID: f1a2b3c4d5e6
Revises: d4e5f6a1b2c3
Create Date: 2026-10-16 03:30:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'd4e5f6a1b2c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reports', sa.Column('telegram_user_id', sa.BigInteger(), nullable=True))
    op.create_index(op.f('ix_reports_telegram_user_id'), 'reports', ['telegram_user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_reports_telegram_user_id'), table_name='reports')
    op.drop_column('reports', 'telegram_user_id')
