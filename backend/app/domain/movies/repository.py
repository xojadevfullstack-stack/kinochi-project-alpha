"""
Movie repository interface.
"""
from abc import ABC, abstractmethod
from typing import Sequence

from app.domain.movies.entities import Movie


class IMovieRepository(ABC):
    @abstractmethod
    async def create(self, movie: Movie, category_ids: list[int] | None = None) -> Movie:
        pass

    @abstractmethod
    async def get_by_id(self, movie_id: int) -> Movie | None:
        pass

    @abstractmethod
    async def get_by_code(self, code: str) -> Movie | None:
        pass

    @abstractmethod
    async def search_by_title(self, title_query: str, skip: int = 0, limit: int = 20) -> tuple[Sequence[Movie], int]:
        """Returns a tuple of (movies, total_count)"""
        pass

    @abstractmethod
    async def list_movies(self, skip: int = 0, limit: int = 20, category_id: int | None = None) -> tuple[Sequence[Movie], int]:
        """Returns a tuple of (movies, total_count)"""
        pass

    @abstractmethod
    async def update(self, movie: Movie, category_ids: list[int] | None = None) -> Movie:
        pass

    @abstractmethod
    async def delete(self, movie_id: int) -> bool:
        pass
