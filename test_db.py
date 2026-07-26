import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath('backend'))
from app.infrastructure.db.session import async_session_maker
from app.infrastructure.db.repositories.movie_repo import MovieRepositoryImpl
from app.infrastructure.db.repositories.series_repository import SeriesRepositoryImpl
from sqlalchemy import select

async def main():
    async with async_session_maker() as session:
        movie_repo = MovieRepositoryImpl(session)
        series_repo = SeriesRepositoryImpl(session)
        
        movies, _ = await movie_repo.list_movies(limit=1)
        if movies:
            print("Found movie:", movies[0].model_dump())
        else:
            print("No movies found")
            
        series, _ = await series_repo.list_series(limit=1)
        if series:
            print("Found series:", series[0].model_dump())
        else:
            print("No series found")

if __name__ == "__main__":
    asyncio.run(main())
