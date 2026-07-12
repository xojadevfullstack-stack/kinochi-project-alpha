"""
Series ORM models.
"""
from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, ForeignKey, Column, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.session import Base

# Many-to-many association table between series and categories
series_category_table = Table(
    "series_category",
    Base.metadata,
    Column("series_id", Integer, ForeignKey("series.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)

class SeriesModel(Base):
    __tablename__ = "series"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    poster_url: Mapped[str | None] = mapped_column(String(1024))
    
    imdb_rating: Mapped[float | None] = mapped_column(Float)
    release_year: Mapped[int | None] = mapped_column(Integer, index=True)
    director: Mapped[str | None] = mapped_column(String(255))
    cast: Mapped[str | None] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    seasons: Mapped[list["SeasonModel"]] = relationship(
        back_populates="series", cascade="all, delete-orphan", lazy="selectin"
    )

    categories: Mapped[list["CategoryModel"]] = relationship(
        secondary=series_category_table, back_populates="series", lazy="selectin"
    )

class SeasonModel(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    series_id: Mapped[int] = mapped_column(ForeignKey("series.id", ondelete="CASCADE"), index=True, nullable=False)
    season_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    poster_url: Mapped[str | None] = mapped_column(String(1024))
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    series: Mapped["SeriesModel"] = relationship(back_populates="seasons")
    episodes: Mapped[list["EpisodeModel"]] = relationship(
        back_populates="season", cascade="all, delete-orphan", lazy="selectin"
    )

class EpisodeModel(Base):
    __tablename__ = "episodes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id", ondelete="CASCADE"), index=True, nullable=False)
    episode_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Internal unique short code (like movies code)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    # Human-readable format S1-CH1
    display_code: Mapped[str] = mapped_column(String(50), nullable=False)
    
    title: Mapped[str | None] = mapped_column(String(255))
    
    telegram_file_id: Mapped[str | None] = mapped_column(String(255))
    storage_channel_message_id: Mapped[int | None] = mapped_column(Integer)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    season: Mapped["SeasonModel"] = relationship(back_populates="episodes")
