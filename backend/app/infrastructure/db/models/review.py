"""
Review ORM model for user ratings and comments.
"""
from datetime import datetime
from sqlalchemy import Integer, Text, ForeignKey, CheckConstraint, Index, DateTime, Column, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.session import Base

class ReviewModel(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    movie_id: Mapped[int | None] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), nullable=True, index=True)
    series_id: Mapped[int | None] = mapped_column(ForeignKey("series.id", ondelete="CASCADE"), nullable=True, index=True)
    episode_id: Mapped[int | None] = mapped_column(ForeignKey("episodes.id", ondelete="CASCADE"), nullable=True, index=True)

    # 1 to 10 rating scale (similar to IMDb)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

    # Relationships
    user = relationship("UserModel", backref="reviews", lazy="selectin")
    movie = relationship("MovieModel", backref="reviews")
    series = relationship("SeriesModel", backref="reviews")
    episode = relationship("EpisodeModel", backref="reviews")

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 10", name="check_valid_rating_range"),
        CheckConstraint(
            "movie_id IS NOT NULL OR series_id IS NOT NULL OR episode_id IS NOT NULL",
            name="check_target_item_not_null"
        ),
        Index("uix_review_user_movie", "user_id", "movie_id", unique=True, postgresql_where=Column('movie_id').isnot(None)),
        Index("uix_review_user_series", "user_id", "series_id", unique=True, postgresql_where=Column('series_id').isnot(None)),
        Index("uix_review_user_episode", "user_id", "episode_id", unique=True, postgresql_where=Column('episode_id').isnot(None)),
    )
