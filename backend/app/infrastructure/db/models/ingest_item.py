"""
IngestItem ORM model.
Yagona navbat va qabul qilish holatlari mashinasi (ingest_items jadvali).
"""
from datetime import datetime
from typing import Any
from sqlalchemy import BigInteger, DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.session import Base

JsonType = JSON().with_variant(JSONB(), "postgresql")

INGEST_STATUSES = (
    "discovered",
    "queued",
    "in_progress",
    "needs_review",
    "rejected",
    "blacklisted",
    "already_exists",
    "failed",
    "published",
)

ALLOWED_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "discovered": {"queued", "already_exists", "rejected", "blacklisted", "needs_review"},
    "queued": {"in_progress", "already_exists", "rejected", "blacklisted", "needs_review", "failed"},
    "in_progress": {"published", "failed", "needs_review", "rejected", "blacklisted", "already_exists", "queued"},
    "needs_review": {"queued", "in_progress", "rejected", "blacklisted", "already_exists", "failed"},
    "failed": {"queued", "in_progress", "rejected", "blacklisted", "needs_review"},
    "rejected": {"queued", "blacklisted"},
    "already_exists": {"queued", "in_progress"},
    "blacklisted": set(),
    "published": set(),
}


def validate_status_transition(current_status: str, new_status: str) -> None:
    if current_status == new_status:
        return
    if new_status not in INGEST_STATUSES:
        raise ValueError(f"Noto'g'ri ingest_items statusi: '{new_status}'")
    allowed = ALLOWED_STATUS_TRANSITIONS.get(current_status)
    if allowed is None or new_status not in allowed:
        raise ValueError(
            f"Taqiqlangan status o'tishi: '{current_status}' -> '{new_status}'"
        )


class IngestItemModel(Base):
    __tablename__ = "ingest_items"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
        index=True,
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    media_type: Mapped[str] = mapped_column(String(20), nullable=False, default="movie", server_default="movie")
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="", server_default="")
    original_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    poster_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    tmdb_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JsonType, nullable=False, default=dict, server_default="{}")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="discovered", server_default="discovered", index=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0", index=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    topic_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    topic_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_message_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    media_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_ingest_items_source_source_id"),
    )
