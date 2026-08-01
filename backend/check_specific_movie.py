import asyncio
import os
from dotenv import load_dotenv

load_dotenv(os.path.abspath('.env'))

from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.movie import MovieModel
from sqlalchemy import select

async def main():
    async with async_session_factory() as session:
        stmt = select(MovieModel).where(MovieModel.code == '47KF9F')
        movie = (await session.execute(stmt)).scalar_one_or_none()
        if movie:
            print(f"Found movie: id={movie.id}, title='{movie.title}', source_chat_id={movie.source_chat_id}, source_topic_id={movie.source_topic_id}")
            print(f"User sent to chat=-1003941035700, topic=405")
            print(f"Matches chat? {str(movie.source_chat_id) == '-1003941035700'}")
            print(f"Matches topic? {str(movie.source_topic_id) == '405'}")
        else:
            print("Movie not found!")

if __name__ == "__main__":
    asyncio.run(main())
