"""
Concrete implementation of ICategoryRepository.
"""
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.categories.entities import Category
from app.domain.categories.repository import ICategoryRepository
from app.infrastructure.db.models.category import CategoryModel


class CategoryRepositoryImpl(ICategoryRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, model: CategoryModel) -> Category:
        return Category.model_validate(model)

    def _to_model(self, entity: Category) -> CategoryModel:
        return CategoryModel(**entity.model_dump(exclude={"id", "created_at"}, exclude_unset=True))

    async def create(self, category: Category) -> Category:
        model = self._to_model(category)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, category_id: int) -> Category | None:
        model = await self.session.get(CategoryModel, category_id)
        return self._to_domain(model) if model else None

    async def get_by_slug(self, slug: str) -> Category | None:
        result = await self.session.execute(select(CategoryModel).where(CategoryModel.slug == slug))
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_all(self, skip: int = 0, limit: int = 100) -> Sequence[Category]:
        result = await self.session.execute(select(CategoryModel).offset(skip).limit(limit))
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def update(self, category: Category) -> Category:
        model = await self.session.get(CategoryModel, category.id)
        if not model:
            raise ValueError(f"Category with id {category.id} not found")
            
        update_data = category.model_dump(exclude={"id", "created_at"}, exclude_unset=True)
        for key, value in update_data.items():
            setattr(model, key, value)
            
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def delete(self, category_id: int) -> bool:
        model = await self.session.get(CategoryModel, category_id)
        if not model:
            return False
        await self.session.delete(model)
        await self.session.flush()
        return True
