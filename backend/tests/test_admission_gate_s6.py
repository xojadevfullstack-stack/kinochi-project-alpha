import pytest
from sqlalchemy import select
from app.infrastructure.db.models.seed_candidate import SeedCandidateModel
from app.infrastructure.db.models.movie import MovieModel
from app.core.admission_gate import promote_to_published, record_rejection


@pytest.mark.asyncio
async def test_s6_promote_to_published_updates_seed_candidate_to_ingested(setup_test_db, engine):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Create seed candidate with status 'queued'
        cand = SeedCandidateModel(
            kind="movie",
            tmdb_id=777001,
            title_en="Seed Ingested Test",
            status="queued",
        )
        session.add(cand)

        # Create movie with tmdb_id=777001
        movie = MovieModel(
            title="Seed Ingested Test",
            tmdb_id=777001,
            code=777001,
            publish_status="pending",
        )
        session.add(movie)
        await session.commit()
        await session.refresh(movie)

        # Promote to published via Admission Gate
        promoted = await promote_to_published(session, movie)
        assert promoted is True
        await session.commit()

    # Verify seed candidate transitioned to 'ingested'
    async with session_factory() as session:
        res = await session.execute(
            select(SeedCandidateModel).where(SeedCandidateModel.tmdb_id == 777001)
        )
        updated_cand = res.scalar_one()
        assert updated_cand.status == "ingested"


@pytest.mark.asyncio
async def test_s6_record_rejection_updates_seed_candidate_to_skipped(setup_test_db, engine):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Create seed candidate with status 'queued'
        cand = SeedCandidateModel(
            kind="movie",
            tmdb_id=777002,
            title_en="Seed Rejected Test",
            status="queued",
        )
        session.add(cand)
        await session.commit()

        # Record rejection via Admission Gate
        await record_rejection(
            session=session,
            media_type="movie",
            source="uzmovi",
            source_key="uzmovi_777002",
            title="Seed Rejected Test",
            payload={"tmdb_id": 777002, "title": "Seed Rejected Test"},
            defects=[{"defect": "missing_telegram_file_id"}],
        )
        await session.commit()

    # Verify seed candidate transitioned to 'skipped'
    async with session_factory() as session:
        res = await session.execute(
            select(SeedCandidateModel).where(SeedCandidateModel.tmdb_id == 777002)
        )
        updated_cand = res.scalar_one()
        assert updated_cand.status == "skipped"
