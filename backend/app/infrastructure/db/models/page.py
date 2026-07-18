"""
Page ORM model and association tables.
"""
from datetime import datetime
from sqlalchemy import String, Boolean, Column, Table, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.session import Base

# Many-to-many association table between pages and movies
page_movie_table = Table(
    "page_movie",
    Base.metadata,
    Column("page_id", Integer, ForeignKey("pages.id", ondelete="CASCADE"), primary_key=True),
    Column("movie_id", Integer, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
)

# Many-to-many association table between pages and series
page_series_table = Table(
    "page_series",
    Base.metadata,
    Column("page_id", Integer, ForeignKey("pages.id", ondelete="CASCADE"), primary_key=True),
    Column("series_id", Integer, ForeignKey("series.id", ondelete="CASCADE"), primary_key=True),
)

class PageModel(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    movies: Mapped[list["MovieModel"]] = relationship(
        secondary=page_movie_table, back_populates="pages"
    )

    series: Mapped[list["SeriesModel"]] = relationship(
        secondary=page_series_table, back_populates="pages"
    )
