"""MandatoryChannel repository implementation."""
from typing import Sequence
from sqlalchemy import select, update, delete, case, and_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.channels.entities import MandatoryChannel
from app.domain.channels.repository import IMandatoryChannelRepository
from app.infrastructure.db.models.channel import MandatoryChannelModel, VerifiedSubscriptionModel

class MandatoryChannelRepositoryImpl(IMandatoryChannelRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: MandatoryChannelModel) -> MandatoryChannel:
        return MandatoryChannel.model_validate(model)

    async def create(self, channel: MandatoryChannel) -> MandatoryChannel:
        model = MandatoryChannelModel(
            channel_id=channel.channel_id,
            channel_username=channel.channel_username,
            channel_title=channel.channel_title,
            is_active=channel.is_active
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, id: int) -> MandatoryChannel | None:
        model = await self.session.get(MandatoryChannelModel, id)
        return self._to_entity(model) if model else None

    async def update(self, channel: MandatoryChannel) -> MandatoryChannel | None:
        model = await self.session.get(MandatoryChannelModel, channel.id)
        if not model:
            return None
        model.channel_id = channel.channel_id
        model.channel_username = channel.channel_username
        model.channel_title = channel.channel_title
        model.is_active = channel.is_active
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def delete(self, id: int) -> bool:
        model = await self.session.get(MandatoryChannelModel, id)
        if not model:
            return False
        await self.session.delete(model)
        await self.session.commit()
        return True

    async def list_active(self) -> Sequence[MandatoryChannel]:
        stmt = select(MandatoryChannelModel).where(MandatoryChannelModel.is_active == True)
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def list_all(self, skip: int = 0, limit: int = 20) -> tuple[Sequence[MandatoryChannel], int]:
        stmt = select(MandatoryChannelModel).order_by(MandatoryChannelModel.id.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        from sqlalchemy import func
        count_stmt = select(func.count(MandatoryChannelModel.id))
        total = await self.session.scalar(count_stmt) or 0
        
        return [self._to_entity(m) for m in models], total

    async def verify_subscription(self, channel_id: int, user_id: int) -> bool:
        channel = await self.session.get(MandatoryChannelModel, channel_id)
        if not channel:
            return False

        stmt = insert(VerifiedSubscriptionModel).values(
            user_id=user_id,
            channel_id=channel_id
        ).on_conflict_do_nothing(
            index_elements=['user_id', 'channel_id']
        ).returning(VerifiedSubscriptionModel.id)
        
        result = await self.session.execute(stmt)
        inserted = result.scalar_one_or_none()
        
        if not inserted:
            # Already subscribed and verified
            return False
            
        update_stmt = update(MandatoryChannelModel).where(
            MandatoryChannelModel.id == channel_id
        ).values(
            current_subscriber_count=MandatoryChannelModel.current_subscriber_count + 1,
            is_active=case(
                (
                    and_(
                        MandatoryChannelModel.subscriber_limit != None,
                        MandatoryChannelModel.current_subscriber_count + 1 >= MandatoryChannelModel.subscriber_limit
                    ),
                    False
                ),
                else_=MandatoryChannelModel.is_active
            )
        )
        await self.session.execute(update_stmt)
        await self.session.commit()
        return True
