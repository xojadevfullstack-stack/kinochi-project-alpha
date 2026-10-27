"""add collection_subscriptions and category_type

Revision ID: c011ec7100
Revises: f1a2b3c4d5e6
Create Date: 2026-10-21 05:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa  # noqa: F401


revision: str = 'c011ec7100'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'collections') THEN
                ALTER TABLE collections ADD COLUMN IF NOT EXISTS category_type VARCHAR(50) DEFAULT 'franchise' NOT NULL;
            END IF;
        EXCEPTION WHEN others THEN NULL;
        END $$;
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS collection_subscriptions (
            id SERIAL PRIMARY KEY,
            telegram_user_id BIGINT NOT NULL,
            collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            CONSTRAINT uq_collection_user_subscription UNIQUE (telegram_user_id, collection_id)
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_collection_subscriptions_user_id ON collection_subscriptions(telegram_user_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_collection_subscriptions_collection_id ON collection_subscriptions(collection_id);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS collection_subscriptions CASCADE;")
    op.execute("ALTER TABLE collections DROP COLUMN IF EXISTS category_type;")
