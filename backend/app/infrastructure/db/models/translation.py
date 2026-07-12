"""
Translation (Dubbing/Studio) ORM models for Movies and Episodes.
"""
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, Column, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.session import Base

class MovieTranslationModel(Base):
    __tablename__ = "movie_translations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), index=True, nullable=False)
    language: Mapped[str] = mapped_column(String(255), nullable=False)
    
    telegram_file_id: Mapped[str | None] = mapped_column(String(255))
    storage_channel_message_id: Mapped[int | None] = mapped_column(Integer)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    
    movie: Mapped["MovieModel"] = relationship(back_populates="translations")

class EpisodeTranslationModel(Base):
    __tablename__ = "episode_translations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    episode_id: Mapped[int] = mapped_column(ForeignKey("episodes.id", ondelete="CASCADE"), index=True, nullable=False)
    language: Mapped[str] = mapped_column(String(255), nullable=False)
    
    telegram_file_id: Mapped[str | None] = mapped_column(String(255))
    storage_channel_message_id: Mapped[int | None] = mapped_column(Integer)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    
    episode: Mapped["EpisodeModel"] = relationship(back_populates="translations")
