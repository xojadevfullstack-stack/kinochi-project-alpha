import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath('backend'))

from dotenv import load_dotenv
load_dotenv(os.path.abspath('backend/.env'))

from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.translation import MovieTranslationModel
from sqlalchemy import select, func

async def main():
    async with async_session_factory() as session:
        # Count all movies
        total_stmt = select(func.count(MovieModel.id))
        total = (await session.execute(total_stmt)).scalar()
        
        # Count movies without translations
        subq = select(MovieTranslationModel.movie_id).distinct()
        no_trans_stmt = select(func.count(MovieModel.id)).where(MovieModel.id.not_in(subq))
        affected = (await session.execute(no_trans_stmt)).scalar()
        
        print(f"Total Movies: {total}")
        print(f"Movies without translations (affected): {affected}")

if __name__ == "__main__":
    asyncio.run(main())
