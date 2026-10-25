"""
Content Request (Movie / Series user order) ORM model.
Allows users to search TMDB/Kinopoisk and request missing movies or series.
"""
from datetime import datetime
from sqlalchemy import String, Integer, Text, BigInteger, func, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.session import Base


class ContentRequestModel(Base):
    __tablename__ = "content_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    original_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    media_type: Mapped[str] = mapped_column(String(20), default="movie", server_default="movie", nullable=False)  # 'movie', 'series'
    release_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    poster_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    overview: Mapped[str | None] = mapped_column(Text, nullable=True)

    tmdb_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    kinopoisk_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    preferred_language: Mapped[str] = mapped_column(String(50), default="uz", server_default="uz", nullable=False)  # 'uz', 'ru', 'sub', 'any'
    user_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    vote_count: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending", nullable=False, index=True)  # 'pending', 'in_review', 'completed', 'rejected'
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_content_requests_tmdb_media", "tmdb_id", "media_type"),
    )
