import pytest
import os
import json
from unittest.mock import patch
from sqlalchemy import select
from app.infrastructure.db.models.seed_candidate import SeedCandidateModel
from scripts.reset_media import reset_media


@pytest.mark.asyncio
async def test_s8_reset_media_dry_run_does_not_modify(setup_test_db, engine, tmp_path):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        cand_queued = SeedCandidateModel(kind="movie", tmdb_id=601, status="queued")
        cand_not_found = SeedCandidateModel(kind="movie", tmdb_id=602, status="not_found")
        session.add_all([cand_queued, cand_not_found])
        await session.commit()

    q_file = str(tmp_path / "queue.json")
    with open(q_file, "w") as f:
        json.dump([{"id": "test_1"}], f)

    with patch("scripts.reset_media.async_session_factory", return_value=session_factory()):
        with patch("scripts.reset_media.QUEUE_FILE", q_file):
            res = await reset_media(execute=False)
            assert res["mode"] == "dry_run"

            # Check file was NOT cleared
            with open(q_file, "r") as f:
                data = json.load(f)
                assert len(data) == 1

    # Check candidates status was NOT updated
    async with session_factory() as session:
        c1 = (await session.execute(select(SeedCandidateModel).where(SeedCandidateModel.tmdb_id == 601))).scalar_one()
        assert c1.status == "queued"


@pytest.mark.asyncio
async def test_s8_reset_media_execute_with_guards(setup_test_db, engine, tmp_path):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        cand_queued = SeedCandidateModel(kind="movie", tmdb_id=701, status="queued")
        cand_ingested = SeedCandidateModel(kind="movie", tmdb_id=702, status="ingested")
        cand_skipped = SeedCandidateModel(kind="movie", tmdb_id=703, status="skipped")
        cand_not_found = SeedCandidateModel(kind="movie", tmdb_id=704, status="not_found")
        session.add_all([cand_queued, cand_ingested, cand_skipped, cand_not_found])
        await session.commit()

    q_file = str(tmp_path / "queue.json")
    s_file = str(tmp_path / "state.json")
    quar_file = str(tmp_path / "quarantine.json")

    with open(q_file, "w") as f:
        json.dump([{"id": "q1"}], f)
    with open(s_file, "w") as f:
        json.dump({"uzmovi": 5}, f)
    with open(quar_file, "w") as f:
        json.dump([{"id": "quar1"}], f)

    with patch("scripts.reset_media.async_session_factory", return_value=session_factory()):
        with patch("scripts.reset_media.QUEUE_FILE", q_file):
            with patch("scripts.reset_media.STATE_FILE", s_file):
                with patch("scripts.reset_media.QUARANTINE_FILE", quar_file):
                    # Execute with YES confirmation
                    res = await reset_media(execute=True, confirm="YES")
                    assert res["mode"] == "executed"

                    # Verify JSON files cleared
                    with open(q_file, "r") as f:
                        assert json.load(f) == []
                    with open(s_file, "r") as f:
                        assert json.load(f) == {}
                    with open(quar_file, "r") as f:
                        assert json.load(f) == []

    # Verify seed_candidates status update:
    # queued, ingested, skipped -> new; not_found -> still not_found!
    async with session_factory() as session:
        c1 = (await session.execute(select(SeedCandidateModel).where(SeedCandidateModel.tmdb_id == 701))).scalar_one()
        assert c1.status == "new"
        c2 = (await session.execute(select(SeedCandidateModel).where(SeedCandidateModel.tmdb_id == 702))).scalar_one()
        assert c2.status == "new"
        c3 = (await session.execute(select(SeedCandidateModel).where(SeedCandidateModel.tmdb_id == 703))).scalar_one()
        assert c3.status == "new"
        c4 = (await session.execute(select(SeedCandidateModel).where(SeedCandidateModel.tmdb_id == 704))).scalar_one()
        assert c4.status == "not_found"
