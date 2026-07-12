"""
Concrete implementation of IMovieRepository.
"""
from typing import Sequence
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.movies.entities import Movie
from app.domain.movies.repository import IMovieRepository
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.category import CategoryModel
from app.infrastructure.db.models.translation import MovieTranslationModel


class MovieRepositoryImpl(IMovieRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, model: MovieModel) -> Movie:
        return Movie.model_validate(model)

    async def create(self, movie: Movie, category_ids: list[int] | None = None) -> Movie:
        model = MovieModel(**movie.model_dump(exclude={"id", "created_at", "updated_at", "categories", "translations"}, exclude_unset=True))
        
        if category_ids:
            result = await self.session.execute(select(CategoryModel).where(CategoryModel.id.in_(category_ids)))
            categories = result.scalars().all()
            model.categories = list(categories)
            
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def get_by_id(self, movie_id: int) -> Movie | None:
        stmt = select(MovieModel).options(
            selectinload(MovieModel.categories),
            selectinload(MovieModel.translations)
        ).where(MovieModel.id == movie_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_code(self, code: str) -> Movie | None:
        stmt = select(MovieModel).options(
            selectinload(MovieModel.categories),
            selectinload(MovieModel.translations)
        ).where(MovieModel.code == code)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def search_by_title(self, title_query: str, skip: int = 0, limit: int = 20) -> tuple[Sequence[Movie], int]:
        query = select(MovieModel).options(
            selectinload(MovieModel.categories),
            selectinload(MovieModel.translations)
        ).where(
            or_(
                MovieModel.title.ilike(f"%{title_query}%"),
                MovieModel.original_title.ilike(f"%{title_query}%")
            )
        )
        
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)
        
        result = await self.session.execute(query.offset(skip).limit(limit))
        models = result.scalars().all()
        
        return [self._to_domain(m) for m in models], total or 0

    async def list_movies(self, skip: int = 0, limit: int = 20, category_id: int | None = None) -> tuple[Sequence[Movie], int]:
        query = select(MovieModel).options(
            selectinload(MovieModel.categories),
            selectinload(MovieModel.translations)
        )
        if category_id:
            query = query.filter(MovieModel.categories.any(id=category_id))
            
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)
        
        result = await self.session.execute(query.offset(skip).limit(limit))
        models = result.scalars().all()
        
        return [self._to_domain(m) for m in models], total or 0

    async def update(self, movie: Movie, category_ids: list[int] | None = None) -> Movie:
        model = await self.session.get(MovieModel, movie.id)
        if not model:
            raise ValueError(f"Movie with id {movie.id} not found")
            
        update_data = movie.model_dump(exclude={"id", "created_at", "updated_at", "categories", "translations"}, exclude_unset=True)
        for key, value in update_data.items():
            setattr(model, key, value)
            
        if category_ids is not None:
            result = await self.session.execute(select(CategoryModel).where(CategoryModel.id.in_(category_ids)))
            categories = result.scalars().all()
            model.categories = list(categories)
            
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def delete(self, movie_id: int) -> bool:
        model = await self.session.get(MovieModel, movie_id)
        if not model:
            return False
        await self.session.delete(model)
        await self.session.flush()
        return True

    async def add_translation(self, movie_id: int, language: str, telegram_file_id: str, storage_channel_message_id: int) -> Movie | None:
        translation = MovieTranslationModel(
            movie_id=movie_id,
            language=language,
            telegram_file_id=telegram_file_id,
            storage_channel_message_id=storage_channel_message_id
        )
        self.session.add(translation)
        await self.session.flush()
        return await self.get_by_id(movie_id)

    async def delete_translation(self, translation_id: int) -> bool:
        model = await self.session.get(MovieTranslationModel, translation_id)
        if not model:
            return False
        await self.session.delete(model)
        await self.session.flush()
        return True
