"""
Category application service.
"""
from typing import Sequence

from app.domain.categories.entities import Category
from app.domain.categories.repository import ICategoryRepository


class CategoryService:
    def __init__(self, category_repo: ICategoryRepository):
        self.category_repo = category_repo

    async def create_category(self, name: str, slug: str, is_active: bool = True) -> Category:
        category = Category(name=name, slug=slug, is_active=is_active)
        return await self.category_repo.create(category)

    async def get_category(self, category_id: int) -> Category | None:
        return await self.category_repo.get_by_id(category_id)

    async def get_category_by_slug(self, slug: str) -> Category | None:
        return await self.category_repo.get_by_slug(slug)

    async def list_categories(self, skip: int = 0, limit: int = 100) -> Sequence[Category]:
        return await self.category_repo.list_all(skip=skip, limit=limit)

    async def update_category(
        self, 
        category_id: int, 
        name: str | None = None, 
        slug: str | None = None,
        is_active: bool | None = None
    ) -> Category | None:
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            return None
        
        if name is not None:
            category.name = name
        if slug is not None:
            category.slug = slug
        if is_active is not None:
            category.is_active = is_active
            
        return await self.category_repo.update(category)

    async def delete_category(self, category_id: int) -> bool:
        return await self.category_repo.delete(category_id)
