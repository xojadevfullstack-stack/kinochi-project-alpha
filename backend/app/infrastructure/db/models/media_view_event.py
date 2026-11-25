"""Media view event ORM model for real-time and time-windowed analytics."""
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.session import Base


class MediaViewEventModel(Base):
    __tablename__ = "media_view_events"
    __table_args__ = (
        Index("ix_media_view_events_created_source", "created_at", "source"),
        Index("ix_media_view_events_movie_created", "movie_id", "created_at"),
        Index("ix_media_view_events_series_created", "series_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "movie" | "series"
    movie_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=True
    )
    series_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("series.id", ondelete="CASCADE"), nullable=True
    )
    episode_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("episodes.id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="web")  # "bot" | "web" | "stream"
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
