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
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'reports') THEN
                ALTER TABLE reports ADD COLUMN IF NOT EXISTS telegram_user_id BIGINT;
                CREATE INDEX IF NOT EXISTS ix_reports_telegram_user_id ON reports (telegram_user_id);
            END IF;
        EXCEPTION WHEN others THEN NULL;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'reports') THEN
                DROP INDEX IF EXISTS ix_reports_telegram_user_id;
                ALTER TABLE reports DROP COLUMN IF EXISTS telegram_user_id;
            END IF;
        EXCEPTION WHEN others THEN NULL;
        END $$;
    """)
