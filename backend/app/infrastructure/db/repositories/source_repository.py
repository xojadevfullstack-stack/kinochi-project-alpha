from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from app.infrastructure.db.models.source import SourceModel

class SourceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_sources(self) -> Sequence[SourceModel]:
        stmt = select(SourceModel).order_by(SourceModel.id.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_source_by_id(self, source_id: int) -> SourceModel | None:
        return await self.session.get(SourceModel, source_id)

    async def create_source(self, data: dict) -> SourceModel:
        source = SourceModel(**data)
        self.session.add(source)
        await self.session.flush()
        await self.session.refresh(source)
        return source

    async def update_source(self, source_id: int, data: dict) -> SourceModel | None:
        if not data:
            return await self.get_source_by_id(source_id)
            
        stmt = (
            update(SourceModel)
            .where(SourceModel.id == source_id)
            .values(**data)
            .returning(SourceModel)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()

    async def delete_source(self, source_id: int) -> bool:
        stmt = delete(SourceModel).where(SourceModel.id == source_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
