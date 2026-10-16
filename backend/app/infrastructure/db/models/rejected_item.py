"""
RejectedItem ORM model.
Admission Gate tomonidan rad etilgan yoki kamchiliklari bo'lgan kontentlarni saqlash jadvali.
"""
from datetime import datetime
from typing import Any
from sqlalchemy import BigInteger, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.session import Base

# PostgreSQL uchun JSONB, boshqa DB lar (masalan SQLite unit testlar) uchun generic JSON
JsonType = JSON().with_variant(JSONB(), "postgresql")


class RejectedItemModel(Base):
    __tablename__ = "rejected_items"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, index=True)
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'movie', 'series', 'episode'
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="", server_default="")
    payload: Mapped[dict[str, Any]] = mapped_column(JsonType, nullable=False, default=dict)
    defects: Mapped[list[dict[str, Any]]] = mapped_column(JsonType, nullable=False, default=list)
    media_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="rejected", server_default="rejected", nullable=False, index=True)  # 'rejected', 'resolved', 'blacklisted'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("source", "source_key", name="uq_rejected_items_source_key"),
    )
