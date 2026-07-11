"""
Series ORM models (Seasons and Episodes).
"""
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, Column, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.session import Base

class SeasonModel(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), index=True)
    season_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024))
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # Relationships
    movie: Mapped["MovieModel"] = relationship(back_populates="seasons")
    episodes: Mapped[list["EpisodeModel"]] = relationship(
        back_populates="season", cascade="all, delete-orphan", lazy="selectin"
    )

class EpisodeModel(Base):
    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id", ondelete="CASCADE"), index=True)
    episode_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    
    # Generated code like "105-S1-CH1"
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    
    # Video details
    telegram_file_id: Mapped[str | None] = mapped_column(String(255))
    storage_channel_message_id: Mapped[int | None] = mapped_column(Integer)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # Relationships
    season: Mapped["SeasonModel"] = relationship(back_populates="episodes")
