"""
Infrastructure — DB repositories.
"""
from app.infrastructure.db.repositories.category_repo import CategoryRepositoryImpl
from app.infrastructure.db.repositories.movie_repo import MovieRepositoryImpl

__all__ = ["CategoryRepositoryImpl", "MovieRepositoryImpl"]
