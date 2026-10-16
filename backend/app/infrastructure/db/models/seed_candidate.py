"""
SeedCandidate ORM model.
TMDb Top Seed Ingestor (S3) uchun nomzodlar va O'zbek manbalari mosliklarini saqlovchi jadval.
Jarayon uzilib qolsa davom ettirish (resumable) va qayta-qayta qidirishni oldini olishni ta'minlaydi.
"""
from datetime import datetime
from typing import Any
from sqlalchemy import BigInteger, Boolean, DateTime, Float, Integer, String, UniqueConstraint, func
from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.session import Base

# PostgreSQL uchun JSONB, SQLite (unit testlar) uchun generic JSON
JsonType = JSON().with_variant(JSONB(), "postgresql")


class SeedCandidateModel(Base):
    __tablename__ = "seed_candidates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # 'movie' yoki 'tv'
    tmdb_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    title_en: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title_ru: Mapped[str | None] = mapped_column(String(255), nullable=True)
    original_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    release_year: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    vote_average: Mapped[float | None] = mapped_column(Float, nullable=True)
    vote_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    popularity: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0", nullable=False)
    is_anime: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False, index=True)

    # Statuslar: 'new', 'searching', 'found', 'not_found', 'ambiguous', 'queued', 'ingested', 'skipped'
    status: Mapped[str] = mapped_column(String(30), default="new", server_default="new", nullable=False, index=True)

    # Har bir manba bo'yicha topilgan ma'lumotlar: { 'uzmovi': {'code': 6282, 'url': '...', 'score': 1.0}, ... }
    matches: Mapped[dict[str, Any]] = mapped_column(JsonType, nullable=False, default=dict, server_default="{}")

    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    last_searched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("kind", "tmdb_id", name="uq_seed_candidates_kind_tmdb_id"),
    )
