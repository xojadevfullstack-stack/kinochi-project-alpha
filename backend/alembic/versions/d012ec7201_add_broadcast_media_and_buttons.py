"""add broadcast media and button fields

Revision ID: d012ec7201
Revises: c011ec7100
Create Date: 2026-10-25 05:40:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'd012ec7201'
down_revision: Union[str, None] = 'c011ec7100'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'broadcasts') THEN
                ALTER TABLE broadcasts ADD COLUMN IF NOT EXISTS media_type VARCHAR(20) DEFAULT 'text' NOT NULL;
                ALTER TABLE broadcasts ADD COLUMN IF NOT EXISTS media_url VARCHAR(1024);
                ALTER TABLE broadcasts ADD COLUMN IF NOT EXISTS button_text VARCHAR(255);
                ALTER TABLE broadcasts ADD COLUMN IF NOT EXISTS button_url VARCHAR(1024);
            END IF;
        EXCEPTION WHEN others THEN NULL;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE broadcasts DROP COLUMN IF EXISTS button_url;
        ALTER TABLE broadcasts DROP COLUMN IF EXISTS button_text;
        ALTER TABLE broadcasts DROP COLUMN IF EXISTS media_url;
        ALTER TABLE broadcasts DROP COLUMN IF EXISTS media_type;
    """)
