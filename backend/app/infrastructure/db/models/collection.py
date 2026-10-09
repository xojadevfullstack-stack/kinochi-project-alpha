"""
Collection and Franchise ORM models.
Supports Canonical Story Timeline (Chronological) vs Release Order.
"""
from datetime import datetime
from sqlalchemy import String, Integer, Text, Boolean, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.session import Base


class CollectionModel(Base):
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    poster_url: Mapped[str | None] = mapped_column(String(1024))
    banner_url: Mapped[str | None] = mapped_column(String(1024))
    
    is_franchise: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    items: Mapped[list["CollectionItemModel"]] = relationship(
        back_populates="collection",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="CollectionItemModel.chronological_order",
    )


class CollectionItemModel(Base):
    __tablename__ = "collection_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    collection_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("collections.id", ondelete="CASCADE"), index=True, nullable=False
    )
    movie_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("movies.id", ondelete="SET NULL"), index=True, nullable=True
    )
    series_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("series.id", ondelete="SET NULL"), index=True, nullable=True
    )

    # 1-indexed order in story timeline (e.g. Captain America: First Avenger = 1)
    chronological_order: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    # 1-indexed order in theater premiere (e.g. Iron Man 1 = 1)
    release_order: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)

    # Short lore / in-universe timeframe description
    # e.g., "1942–1945: 2-Jahon Urushi, Qasoskorning tug'ilishi"
    timeline_event_desc: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # If true, automated pipeline cannot modify or reorder this item
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    collection: Mapped["CollectionModel"] = relationship(back_populates="items")
    movie: Mapped["MovieModel | None"] = relationship(lazy="selectin")
    series: Mapped["SeriesModel | None"] = relationship(lazy="selectin")
