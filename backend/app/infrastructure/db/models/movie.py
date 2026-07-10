"""
Movie ORM model and association tables.
"""
from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, ForeignKey, Column, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.session import Base


# Many-to-many association table between movies and categories
movie_category_table = Table(
    "movie_category",
    Base.metadata,
    Column("movie_id", Integer, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)


class MovieModel(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    original_title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    
    imdb_rating: Mapped[float | None] = mapped_column(Float)
    tmdb_rating: Mapped[float | None] = mapped_column(Float)
    
    genres: Mapped[str | None] = mapped_column(String(255))
    cast: Mapped[str | None] = mapped_column(Text)
    director: Mapped[str | None] = mapped_column(String(255))
    
    release_year: Mapped[int | None] = mapped_column(Integer, index=True)
    runtime: Mapped[int | None] = mapped_column(Integer)
    
    poster_url: Mapped[str | None] = mapped_column(String(1024))
    trailer_url: Mapped[str | None] = mapped_column(String(1024))
    
    code: Mapped[str] = mapped_column(String(8), nullable=False, unique=True, index=True)
    telegram_file_id: Mapped[str | None] = mapped_column(String(255))
    storage_channel_message_id: Mapped[int | None] = mapped_column(Integer)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    categories: Mapped[list["CategoryModel"]] = relationship(
        secondary=movie_category_table, back_populates="movies", lazy="selectin"
    )
