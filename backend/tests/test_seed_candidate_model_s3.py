import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.infrastructure.db.models.seed_candidate import SeedCandidateModel


@pytest.mark.asyncio
async def test_create_seed_candidate_and_defaults(setup_test_db, engine):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        candidate = SeedCandidateModel(
            kind="movie",
            tmdb_id=157336,
            title_en="Interstellar",
            title_ru="Интерстеллар",
            original_title="Interstellar",
            release_year=2014,
            vote_average=8.4,
            vote_count=34000,
            popularity=150.0,
            is_anime=False,
        )
        session.add(candidate)
        await session.commit()
        await session.refresh(candidate)

        assert candidate.id is not None
        assert candidate.status == "new"
        assert candidate.attempts == 0
        assert candidate.matches == {}
        assert candidate.is_anime is False


@pytest.mark.asyncio
async def test_seed_candidate_unique_constraint(setup_test_db, engine):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        cand1 = SeedCandidateModel(
            kind="movie",
            tmdb_id=278,
            title_en="The Shawshank Redemption",
            status="new",
        )
        session.add(cand1)
        await session.commit()

    # Adding duplicate (kind="movie", tmdb_id=278) must fail UniqueConstraint
    async with session_factory() as session:
        cand2 = SeedCandidateModel(
            kind="movie",
            tmdb_id=278,
            title_en="Duplicate Shawshank",
            status="new",
        )
        session.add(cand2)
        with pytest.raises(IntegrityError):
            await session.commit()


@pytest.mark.asyncio
async def test_seed_candidate_update_matches(setup_test_db, engine):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        cand = SeedCandidateModel(
            kind="tv",
            tmdb_id=1399,
            title_en="Game of Thrones",
            status="searching",
        )
        session.add(cand)
        await session.commit()
        await session.refresh(cand)

        cand.status = "found"
        cand.matches = {"uzmovi": {"code": "1234", "score": 1.0}}
        cand.attempts = 1
        await session.commit()

    async with session_factory() as session:
        res = await session.execute(
            select(SeedCandidateModel).where(SeedCandidateModel.kind == "tv", SeedCandidateModel.tmdb_id == 1399)
        )
        loaded = res.scalar_one()
        assert loaded.status == "found"
        assert loaded.matches["uzmovi"]["code"] == "1234"
        assert loaded.attempts == 1
