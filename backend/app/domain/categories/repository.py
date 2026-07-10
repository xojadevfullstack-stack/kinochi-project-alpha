"""
Category repository interface.
"""
from abc import ABC, abstractmethod
from typing import Sequence

from app.domain.categories.entities import Category


class ICategoryRepository(ABC):
    @abstractmethod
    async def create(self, category: Category) -> Category:
        pass

    @abstractmethod
    async def get_by_id(self, category_id: int) -> Category | None:
        pass
        
    @abstractmethod
    async def get_by_slug(self, slug: str) -> Category | None:
        pass

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> Sequence[Category]:
        pass

    @abstractmethod
    async def update(self, category: Category) -> Category:
        pass

    @abstractmethod
    async def delete(self, category_id: int) -> bool:
        pass
