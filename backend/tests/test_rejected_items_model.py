"""
Tests for RejectedItemModel and rejected_items table schema (B1).
"""
import pytest
import os
import importlib.util
from sqlalchemy import BigInteger, Integer, String, UniqueConstraint
from app.infrastructure.db.models.rejected_item import RejectedItemModel

MIGRATION_PATH = os.path.join(
    os.path.dirname(__file__), "..", "alembic", "versions", "c1d2e3f4a5b6_create_rejected_items_table.py"
)
spec = importlib.util.spec_from_file_location("migration_b1", MIGRATION_PATH)
migration_b1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration_b1)


def test_rejected_item_model_attributes():
    """RejectedItemModel atributlari va ustunlar turlari to'g'riligini tekshirish."""
    table = RejectedItemModel.__table__

    assert "id" in table.c
    assert isinstance(table.c.id.type, BigInteger)
    assert table.c.id.primary_key is True

    assert "media_type" in table.c
    assert isinstance(table.c.media_type.type, String)
    assert table.c.media_type.type.length == 20
    assert table.c.media_type.nullable is False

    assert "source" in table.c
    assert isinstance(table.c.source.type, String)
    assert table.c.source.type.length == 50
    assert table.c.source.nullable is False

    assert "source_key" in table.c
    assert isinstance(table.c.source_key.type, String)
    assert table.c.source_key.type.length == 255
    assert table.c.source_key.nullable is False

    assert "payload" in table.c
    assert table.c.payload.nullable is False

    assert "defects" in table.c
    assert table.c.defects.nullable is False

    assert "media_id" in table.c
    assert isinstance(table.c.media_id.type, BigInteger)
    assert table.c.media_id.nullable is True

    assert "attempts" in table.c
    assert isinstance(table.c.attempts.type, Integer)

    assert "status" in table.c
    assert isinstance(table.c.status.type, String)
    assert table.c.status.type.length == 30


def test_rejected_item_model_unique_constraint():
    """(source, source_key) bo'yicha UniqueConstraint mavjudligini tekshirish."""
    unique_constraints = [
        c for c in RejectedItemModel.__table__.constraints
        if isinstance(c, UniqueConstraint)
    ]
    uq_names = [c.name for c in unique_constraints]
    assert "uq_rejected_items_source_key" in uq_names

    uq = next(c for c in unique_constraints if c.name == "uq_rejected_items_source_key")
    col_names = [col.name for col in uq.columns]
    assert "source" in col_names
    assert "source_key" in col_names


def test_migration_b1_revisions():
    """Alembic migratsiya zanjiri to'g'riligini tekshirish."""
    assert migration_b1.revision == "c1d2e3f4a5b6"
    assert migration_b1.down_revision == "b3a1c2d4e5f6"
