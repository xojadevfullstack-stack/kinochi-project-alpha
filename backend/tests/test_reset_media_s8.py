import pytest
import os
import json
from unittest.mock import patch
from sqlalchemy import select, text
from app.infrastructure.db.models.seed_candidate import SeedCandidateModel
from app.infrastructure.db.models.ingest_item import IngestItemModel
from scripts.reset_media import reset_media


@pytest.mark.asyncio
async def test_s8_reset_media_dry_run_does_not_modify(setup_test_db, engine):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        await session.execute(text("DELETE FROM seed_candidates"))
        await session.execute(text("DELETE FROM ingest_items"))
        cand_queued = SeedCandidateModel(kind="movie", tmdb_id=601, status="queued")
        cand_not_found = SeedCandidateModel(kind="movie", tmdb_id=602, status="not_found")
        ing_item = IngestItemModel(source="uzmovi", source_id="601", media_type="movie", title="Test 1", status="queued")
        session.add_all([cand_queued, cand_not_found, ing_item])
        await session.commit()

    with patch("scripts.reset_media.async_session_factory", session_factory):
        res = await reset_media(execute=False)
        assert res["mode"] == "dry_run"
        assert res["queue_count"] == 1

    # Check candidates status was NOT updated
    async with session_factory() as session:
        c1 = (await session.execute(select(SeedCandidateModel).where(SeedCandidateModel.tmdb_id == 601))).scalar_one()
        assert c1.status == "queued"


@pytest.mark.asyncio
async def test_s8_reset_media_guard_1_confirm_not_yes_stays_dry_run(setup_test_db, engine):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    with patch("scripts.reset_media.async_session_factory", session_factory):
        res = await reset_media(execute=True, confirm="NO")
        assert res["mode"] == "dry_run"


@pytest.mark.asyncio
async def test_s8_reset_media_guard_2_backup_file_missing_or_empty(setup_test_db, engine, tmp_path):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    empty_backup = str(tmp_path / "empty_backup.sql")
    with open(empty_backup, "w") as f:
        pass  # 0 baytlik bo'sh fayl

    non_existent = str(tmp_path / "does_not_exist.sql")

    with patch("scripts.reset_media.async_session_factory", session_factory):
        # 1. backup_file berilmagan
        res1 = await reset_media(execute=True, confirm="YES", backup_file=None)
        assert res1 == {"error": "backup_file_missing_or_empty"}

        # 2. Mavjud bo'lmagan fayl
        res2 = await reset_media(execute=True, confirm="YES", backup_file=non_existent)
        assert res2 == {"error": "backup_file_missing_or_empty"}

        # 3. 0 baytlik bo'sh fayl
        res3 = await reset_media(execute=True, confirm="YES", backup_file=empty_backup)
        assert res3 == {"error": "backup_file_missing_or_empty"}


@pytest.mark.asyncio
async def test_s8_reset_media_guard_3_host_mismatch_without_override(setup_test_db, engine, tmp_path):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    valid_backup = str(tmp_path / "valid_backup.sql")
    with open(valid_backup, "w") as f:
        f.write("-- valid non-empty backup")

    with patch("scripts.reset_media.async_session_factory", session_factory):
        with patch("scripts.reset_media.settings.DATABASE_URL", "postgresql+asyncpg://user:pass@prod-db.neon.tech/kinochi"):
            with patch.dict(os.environ, {"TEST_DATABASE_URL": "postgresql+asyncpg://user:pass@test-branch.neon.tech/kinochi"}):
                # Hostlar mos emas, override bayrog'i yo'q
                res = await reset_media(execute=True, confirm="YES", backup_file=valid_backup, i_am_wiping_production=False)
                assert res == {"error": "target_db_host_mismatch"}


@pytest.mark.asyncio
async def test_s8_reset_media_guard_3_override_with_i_am_wiping_production(setup_test_db, engine, tmp_path):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    valid_backup = str(tmp_path / "valid_backup.sql")
    with open(valid_backup, "w") as f:
        f.write("-- valid non-empty backup content")

    s_file = str(tmp_path / "state.json")
    quar_file = str(tmp_path / "quarantine.json")
    with open(s_file, "w") as f:
        json.dump({}, f)
    with open(quar_file, "w") as f:
        json.dump([], f)

    with patch("scripts.reset_media.async_session_factory", session_factory):
        with patch("scripts.reset_media.STATE_FILE", s_file):
            with patch("scripts.reset_media.QUARANTINE_FILE", quar_file):
                with patch("scripts.reset_media.settings.DATABASE_URL", "postgresql+asyncpg://user:pass@prod-db.neon.tech/kinochi"):
                    # Hostlar mos bo'lmasa ham, --i-am-wiping-production va --backup-file berilganda ishlaydi
                    res = await reset_media(
                        execute=True,
                        confirm="YES",
                        backup_file=valid_backup,
                        i_am_wiping_production=True
                    )
                    assert res["mode"] == "executed"


@pytest.mark.asyncio
async def test_s8_reset_media_guard_3_matching_test_host_succeeds(setup_test_db, engine, tmp_path):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        await session.execute(text("DELETE FROM seed_candidates"))
        cand_queued = SeedCandidateModel(kind="movie", tmdb_id=701, status="queued")
        cand_ingested = SeedCandidateModel(kind="movie", tmdb_id=702, status="ingested")
        cand_skipped = SeedCandidateModel(kind="movie", tmdb_id=703, status="skipped")
        cand_not_found = SeedCandidateModel(kind="movie", tmdb_id=704, status="not_found")
        session.add_all([cand_queued, cand_ingested, cand_skipped, cand_not_found])
        await session.commit()

    valid_backup = str(tmp_path / "valid_backup.sql")
    with open(valid_backup, "w") as f:
        f.write("-- valid non-empty backup content")

    s_file = str(tmp_path / "state.json")
    quar_file = str(tmp_path / "quarantine.json")

    with open(s_file, "w") as f:
        json.dump({"uzmovi": 5}, f)
    with open(quar_file, "w") as f:
        json.dump([{"id": "quar1"}], f)

    test_host_url = "postgresql+asyncpg://user:pass@test-branch.neon.tech/kinochi"

    with patch("scripts.reset_media.async_session_factory", session_factory):
        with patch("scripts.reset_media.STATE_FILE", s_file):
            with patch("scripts.reset_media.QUARANTINE_FILE", quar_file):
                with patch("scripts.reset_media.settings.DATABASE_URL", test_host_url):
                    with patch.dict(os.environ, {"TEST_DATABASE_URL": test_host_url}):
                        # Nishon DB xosti TEST_DATABASE_URL ga to'liq mos
                        res = await reset_media(execute=True, confirm="YES", backup_file=valid_backup)
                        assert res["mode"] == "executed"

                        # JSON fayllar tozalangan
                        with open(s_file, "r") as f:
                            assert json.load(f) == {}
                        with open(quar_file, "r") as f:
                            assert json.load(f) == []

    # seed_candidates holati yangilangan: queued, ingested, skipped -> new; not_found -> not_found
    async with session_factory() as session:
        c1 = (await session.execute(select(SeedCandidateModel).where(SeedCandidateModel.tmdb_id == 701))).scalar_one()
        assert c1.status == "new"
        c2 = (await session.execute(select(SeedCandidateModel).where(SeedCandidateModel.tmdb_id == 702))).scalar_one()
        assert c2.status == "new"
        c3 = (await session.execute(select(SeedCandidateModel).where(SeedCandidateModel.tmdb_id == 703))).scalar_one()
        assert c3.status == "new"
        c4 = (await session.execute(select(SeedCandidateModel).where(SeedCandidateModel.tmdb_id == 704))).scalar_one()
        assert c4.status == "not_found"


@pytest.mark.asyncio
async def test_s8_reset_media_with_wipe_media(setup_test_db, engine, tmp_path):
    """wipe_media=True bo'lganda media jadvallari (movies, series) tozalanadi."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from app.infrastructure.db.models.movie import MovieModel
    from sqlalchemy import select, func
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        movie = MovieModel(title="Test Movie To Wipe", code=12345, tmdb_id=8888, release_year=2024, publish_status="published")
        session.add(movie)
        await session.commit()

    valid_backup = str(tmp_path / "valid_backup.sql")
    with open(valid_backup, "w") as f:
        f.write("-- valid backup content")

    s_file = str(tmp_path / "s.json")
    quar_file = str(tmp_path / "quar.json")
    for fpath, data in [(s_file, {}), (quar_file, [])]:
        with open(fpath, "w") as f:
            json.dump(data, f)

    with patch("scripts.reset_media.async_session_factory", session_factory):
        with patch("scripts.reset_media.STATE_FILE", s_file):
            with patch("scripts.reset_media.QUARANTINE_FILE", quar_file):
                test_host_url = "postgresql+asyncpg://user:pass@test-branch.neon.tech/kinochi"
                with patch("scripts.reset_media.settings.DATABASE_URL", test_host_url):
                    with patch.dict(os.environ, {"TEST_DATABASE_URL": test_host_url}):
                        res = await reset_media(
                            execute=True,
                            confirm="YES",
                            backup_file=valid_backup,
                            wipe_media=True,
                        )
                        assert res["mode"] == "executed"
                        assert res.get("media_wiped") is True

    async with session_factory() as session:
        count = (await session.execute(select(func.count(MovieModel.id)))).scalar()
        assert count == 0
