from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.broadcasts.entities import Broadcast, BroadcastStatus
from app.domain.broadcasts.repository import IBroadcastRepository
from app.infrastructure.db.models.broadcast import BroadcastModel

class BroadcastRepositoryImpl(IBroadcastRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: BroadcastModel) -> Broadcast:
        return Broadcast.model_validate(model)

    async def create(self, broadcast: Broadcast) -> Broadcast:
        model = BroadcastModel(
            message_text=broadcast.message_text,
            status=broadcast.status,
            total_recipients=broadcast.total_recipients,
            sent_count=broadcast.sent_count,
            failed_count=broadcast.failed_count
        )
        self.session.add(model)
        await self.session.flush()   # commit() emas — Unit of Work pattern: session deps.py da commit qiladi
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, id: int) -> Broadcast | None:
        stmt = select(BroadcastModel).where(BroadcastModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_broadcasts(self, skip: int = 0, limit: int = 20) -> tuple[Sequence[Broadcast], int]:
        stmt = select(BroadcastModel).order_by(BroadcastModel.id.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        from sqlalchemy import func
        count_stmt = select(func.count(BroadcastModel.id))
        total = await self.session.scalar(count_stmt) or 0
        
        return [self._to_entity(m) for m in models], total

    async def update_status(self, id: int, status: BroadcastStatus) -> Broadcast | None:
        stmt = select(BroadcastModel).where(BroadcastModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            model.status = status
            await self.session.commit()
            await self.session.refresh(model)
            return self._to_entity(model)
        return None

    async def increment_counts(self, id: int, sent: int = 0, failed: int = 0) -> None:
        # Avoid race conditions via direct SQL updates if possible, 
        # but for simplicity and since we have one sender task, we can use ORM updates:
        stmt = select(BroadcastModel).where(BroadcastModel.id == id).with_for_update()
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.sent_count += sent
            model.failed_count += failed
            await self.session.commit()
