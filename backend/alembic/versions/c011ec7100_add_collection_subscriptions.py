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
        CREATE TABLE IF NOT EXISTS collections (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            slug VARCHAR(255) NOT NULL,
            description TEXT,
            poster_url VARCHAR(1024),
            banner_url VARCHAR(1024),
            is_franchise BOOLEAN DEFAULT TRUE NOT NULL,
            category_type VARCHAR(50) DEFAULT 'franchise' NOT NULL,
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            sort_order INTEGER DEFAULT 0 NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
        );
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_collections_slug ON collections(slug);")

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
    op.execute("DROP TABLE IF EXISTS collections CASCADE;")
