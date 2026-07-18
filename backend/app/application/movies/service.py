"""
Movie application service.
"""
from typing import Sequence
import shortuuid

from app.domain.movies.entities import Movie
from app.domain.movies.repository import IMovieRepository


class MovieService:
    def __init__(self, movie_repo: IMovieRepository):
        self.movie_repo = movie_repo

    async def _generate_unique_code(self) -> str:
        # Generates a short unique code (6 chars, unambiguous alphabet)
        alphabet = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
        
        while True:
            code = shortuuid.ShortUUID(alphabet=alphabet).random(length=6)
            existing = await self.movie_repo.get_by_code(code)
            if not existing:
                return code

    async def create_movie(
        self,
        title: str,
        code: str | None = None,
        original_title: str | None = None,
        description: str | None = None,
        imdb_rating: float | None = None,
        tmdb_rating: float | None = None,
        genres: str | None = None,
        cast: str | None = None,
        director: str | None = None,
        release_year: int | None = None,
        runtime: int | None = None,
        poster_url: str | None = None,
        trailer_url: str | None = None,
        category_ids: list[int] | None = None,
        page_ids: list[int] | None = None,
        source_chat_id: int | None = None,
        source_topic_id: int | None = None
    ) -> Movie:
        if code is None:
            code = await self._generate_unique_code()
            
        movie = Movie(
            title=title,
            code=code,
            original_title=original_title,
            description=description,
            imdb_rating=imdb_rating,
            tmdb_rating=tmdb_rating,
            genres=genres,
            cast=cast,
            director=director,
            release_year=release_year,
            runtime=runtime,
            poster_url=poster_url,
            trailer_url=trailer_url,
            source_chat_id=source_chat_id,
            source_topic_id=source_topic_id
        )
        return await self.movie_repo.create(movie, category_ids=category_ids, page_ids=page_ids)

    async def get_movie(self, movie_id: int) -> Movie | None:
        return await self.movie_repo.get_by_id(movie_id)

    async def get_movie_by_code(self, code: str) -> Movie | None:
        return await self.movie_repo.get_by_code(code)

    async def search_movies(self, title_query: str, skip: int = 0, limit: int = 20) -> tuple[Sequence[Movie], int]:
        return await self.movie_repo.search_by_title(title_query, skip=skip, limit=limit)

    async def list_movies(self, skip: int = 0, limit: int = 20, category_id: int | None = None, page_id: int | None = None) -> tuple[Sequence[Movie], int]:
        return await self.movie_repo.list_movies(skip=skip, limit=limit, category_id=category_id, page_id=page_id)

    async def update_movie(
        self,
        movie_id: int,
        title: str | None = None,
        original_title: str | None = None,
        description: str | None = None,
        imdb_rating: float | None = None,
        tmdb_rating: float | None = None,
        genres: str | None = None,
        cast: str | None = None,
        director: str | None = None,
        release_year: int | None = None,
        runtime: int | None = None,
        poster_url: str | None = None,
        trailer_url: str | None = None,
        category_ids: list[int] | None = None,
        page_ids: list[int] | None = None,
        source_chat_id: int | None = None,
        source_topic_id: int | None = None
    ) -> Movie | None:
        movie = await self.movie_repo.get_by_id(movie_id)
        if not movie:
            return None
            
        # Update fields if provided
        if title is not None: movie.title = title
        if original_title is not None: movie.original_title = original_title
        if description is not None: movie.description = description
        if imdb_rating is not None: movie.imdb_rating = imdb_rating
        if tmdb_rating is not None: movie.tmdb_rating = tmdb_rating
        if genres is not None: movie.genres = genres
        if cast is not None: movie.cast = cast
        if director is not None: movie.director = director
        if release_year is not None: movie.release_year = release_year
        if runtime is not None: movie.runtime = runtime
        if poster_url is not None: movie.poster_url = poster_url
        if trailer_url is not None: movie.trailer_url = trailer_url
        if source_chat_id is not None: movie.source_chat_id = source_chat_id
        if source_topic_id is not None: movie.source_topic_id = source_topic_id

        return await self.movie_repo.update(movie, category_ids=category_ids, page_ids=page_ids)

    async def delete_movie(self, movie_id: int) -> bool:
        return await self.movie_repo.delete(movie_id)

    async def link_movie_video_from_message(self, movie_id: int, message_id: int, language: str = "Asosiy") -> Movie | None:
        movie = await self.movie_repo.get_by_id(movie_id)
        if not movie:
            return None
            
        # Get file_id from telegram message
        from app.infrastructure.telegram.telegram_client import telegram_client
        file_id = await telegram_client.get_video_file_id_from_message(message_id)
        
        return await self.movie_repo.add_translation(movie_id, language, file_id, message_id)

    async def add_movie_translation(self, movie_id: int, language: str, file_id: str, message_id: int) -> Movie | None:
        return await self.movie_repo.add_translation(movie_id, language, file_id, message_id)
        
    async def delete_movie_translation(self, translation_id: int) -> bool:
        return await self.movie_repo.delete_translation(translation_id)
