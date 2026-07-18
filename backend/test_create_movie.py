import asyncio
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.repositories.movie_repo import MovieRepositoryImpl
from app.domain.movies.entities import Movie

async def test_create():
    async with async_session_factory() as session:
        repo = MovieRepositoryImpl(session)
        movie = Movie(
            title="Test Movie",
            code="test_c1",
            source_chat_id=-1001234567,
            source_topic_id=None
        )
        try:
            m = await repo.create(movie, category_ids=[1], page_ids=[])
            print("Successfully created movie:", m.title, "Categories:", len(m.categories))
            await session.commit()
        except Exception as e:
            print("Error creating movie:", str(e))
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_create())
