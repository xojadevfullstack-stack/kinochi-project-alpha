import pytest
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure.db.session import Base
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.category import CategoryModel
from app.infrastructure.db.repositories.movie_repo import MovieRepositoryImpl

@pytest.mark.asyncio
async def test_guest_issue_001_movie_search_no_name_error():
    """GUEST-ISSUE-001: movie_repo.search_by_title must NOT crash with NameError (re must be imported)."""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        # Seed one movie
        movie = MovieModel(
            title="Avatar: Suv Yo'li",
            code="AVTR01",
            publish_status="published",
        )
        session.add(movie)
        await session.commit()

        repo = MovieRepositoryImpl(session)
        # This will trigger line 341 in movie_repo.py where re.split is called
        items, total = await repo.search_by_title("Avatar", skip=0, limit=10)
        assert total >= 1
        assert items[0].title == "Avatar: Suv Yo'li"
    
    await test_engine.dispose()
