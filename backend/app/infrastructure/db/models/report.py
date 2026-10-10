"""
Report (Error / Issue feedback) ORM model.
"""
from datetime import datetime
from sqlalchemy import String, Integer, Text, ForeignKey, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.session import Base


class ReportModel(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'movie', 'series', 'episode'
    
    movie_id: Mapped[int | None] = mapped_column(ForeignKey("movies.id", ondelete="SET NULL"), nullable=True)
    series_id: Mapped[int | None] = mapped_column(ForeignKey("series.id", ondelete="SET NULL"), nullable=True)
    episode_id: Mapped[int | None] = mapped_column(ForeignKey("episodes.id", ondelete="SET NULL"), nullable=True)
    
    issue_type: Mapped[str] = mapped_column(String(50), nullable=False)  # wrong_poster, duplicate, wrong_video, audio_issue, wrong_meta, broken_trailer, other
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 'image', 'video'
    
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending", nullable=False, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    movie = relationship("MovieModel", lazy="selectin")
    series = relationship("SeriesModel", lazy="selectin")
    episode = relationship("EpisodeModel", lazy="selectin")
