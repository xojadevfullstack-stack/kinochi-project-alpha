"""create ingest_items table

Revision ID: a1b2c3d4e5f6
Revises: f1322da82a96
Create Date: 2026-10-29 14:26:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "9c8d7e6f5a4b"
down_revision: Union[str, None] = "f1322da82a96"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ingest_items",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), autoincrement=True, nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("media_type", sa.String(length=20), server_default="movie", nullable=False),
        sa.Column("title", sa.String(length=255), server_default="", nullable=False),
        sa.Column("original_title", sa.String(length=255), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("url", sa.String(length=1024), nullable=True),
        sa.Column("poster_url", sa.String(length=1024), nullable=True),
        sa.Column("tmdb_id", sa.Integer(), nullable=True),
        sa.Column(
            "payload",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("status", sa.String(length=30), server_default="discovered", nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("priority", sa.Integer(), server_default="0", nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.String(length=100), nullable=True),
        sa.Column("topic_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.Column("storage_message_id", sa.Integer(), nullable=True),
        sa.Column("media_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source", "source_id", name="uq_ingest_items_source_source_id"),
    )
    op.create_index(op.f("ix_ingest_items_id"), "ingest_items", ["id"], unique=False)
    op.create_index(op.f("ix_ingest_items_source"), "ingest_items", ["source"], unique=False)
    op.create_index(op.f("ix_ingest_items_source_id"), "ingest_items", ["source_id"], unique=False)
    op.create_index(op.f("ix_ingest_items_year"), "ingest_items", ["year"], unique=False)
    op.create_index(op.f("ix_ingest_items_tmdb_id"), "ingest_items", ["tmdb_id"], unique=False)
    op.create_index(op.f("ix_ingest_items_status"), "ingest_items", ["status"], unique=False)
    op.create_index(op.f("ix_ingest_items_priority"), "ingest_items", ["priority"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ingest_items_priority"), table_name="ingest_items")
    op.drop_index(op.f("ix_ingest_items_status"), table_name="ingest_items")
    op.drop_index(op.f("ix_ingest_items_tmdb_id"), table_name="ingest_items")
    op.drop_index(op.f("ix_ingest_items_year"), table_name="ingest_items")
    op.drop_index(op.f("ix_ingest_items_source_id"), table_name="ingest_items")
    op.drop_index(op.f("ix_ingest_items_source"), table_name="ingest_items")
    op.drop_index(op.f("ix_ingest_items_id"), table_name="ingest_items")
    op.drop_table("ingest_items")
