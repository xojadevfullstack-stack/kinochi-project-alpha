"""
Collection and Franchise Subscriptions ORM model.
Allows users to subscribe to franchises / collections to get smart notifications
when a new movie, part, or spin-off is added.
"""
from datetime import datetime
from sqlalchemy import Integer, BigInteger, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.session import Base


class CollectionSubscriptionModel(Base):
    __tablename__ = "collection_subscriptions"
    __table_args__ = (
        UniqueConstraint("telegram_user_id", "collection_id", name="uq_collection_user_subscription"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    collection_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("collections.id", ondelete="CASCADE"), index=True, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    collection: Mapped["CollectionModel"] = relationship(back_populates="subscriptions")
