from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.infrastructure.db.session import Base

class WatchHistoryModel(Base):
    __tablename__ = "watch_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id: Mapped[int | None] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=True)
    episode_id: Mapped[int | None] = mapped_column(ForeignKey("episodes.id", ondelete="CASCADE"), nullable=True)
    
    # "in_progress" | "completed"
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    
    last_watched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )

    # Relationships
    user = relationship("UserModel", backref="watch_history")
    movie = relationship("MovieModel")
    episode = relationship("EpisodeModel")

    __table_args__ = (
        CheckConstraint(
            "(movie_id IS NOT NULL AND episode_id IS NULL) OR (movie_id IS NULL AND episode_id IS NOT NULL)",
            name="check_movie_or_episode"
        ),
        Index("uix_watch_history_user_movie", "user_id", "movie_id", unique=True, postgresql_where=Column('movie_id').isnot(None)),
        Index("uix_watch_history_user_episode", "user_id", "episode_id", unique=True, postgresql_where=Column('episode_id').isnot(None)),
    )
