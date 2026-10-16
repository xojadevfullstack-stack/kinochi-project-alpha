import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select, text, func
from app.infrastructure.db.models.seed_candidate import SeedCandidateModel
from app.infrastructure.db.models.rejected_item import RejectedItemModel
from app.infrastructure.db.models.blacklist import BlacklistModel
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel
from app.infrastructure.external.tmdb_client import tmdb_client
from scraper.tmdb_top_ingestor import TmdbTopIngestor, evaluate_candidate_match
from scraper.queue_manager import QueueManager, QueueItem


@pytest.mark.asyncio
async def test_s9_build_seeds_filters_adult_and_low_votes_and_rating(setup_test_db, engine):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    ingestor = TmdbTopIngestor()

    mock_top_rated = {
        "page": 1,
        "results": [
            # 1. Adult movie -> Should be EXCLUDED
            {"id": 101, "title": "Adult Movie", "original_title": "Adult Movie", "adult": True, "vote_count": 5000, "vote_average": 8.5},
            # 2. Low vote count (< 1000) -> Should be EXCLUDED
            {"id": 102, "title": "Indie Gem", "original_title": "Indie Gem", "adult": False, "vote_count": 250, "vote_average": 8.5},
            # 3. Low rating (< 7.0) -> Should be EXCLUDED
            {"id": 103, "title": "Average Action", "original_title": "Average Action", "adult": False, "vote_count": 5000, "vote_average": 5.8},
            # 4. Valid Masterpiece -> Should be INCLUDED
            {"id": 104, "title": "Interstellar", "original_title": "Interstellar", "adult": False, "vote_count": 32000, "vote_average": 8.4, "release_date": "2014-11-05"},
        ],
    }
    mock_popular = {"page": 1, "results": []}

    with patch("scraper.tmdb_top_ingestor.async_session_factory", return_value=session_factory()):
        with patch.object(tmdb_client, "list_top_rated", AsyncMock(return_value=mock_top_rated)):
            with patch.object(tmdb_client, "list_popular", AsyncMock(return_value=mock_popular)):
                # Run build_seeds with target 1
                with patch("scraper.tmdb_top_ingestor.SEED_MOVIE_TARGET", 1):
                    stats = await ingestor.build_seeds()
                    assert stats["added"] == 1
                    assert stats["skipped_filter"] == 3

    # Assert only ID 104 exists in seed_candidates
    async with session_factory() as session:
        cands = (await session.execute(select(SeedCandidateModel.tmdb_id))).scalars().all()
        assert 104 in cands
        assert 101 not in cands
        assert 102 not in cands
        assert 103 not in cands


@pytest.mark.asyncio
async def test_s9_already_in_db_blacklist_or_rejected_skipped(setup_test_db, engine, tmp_path):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    q_file = str(tmp_path / "test_queue.json")
    qm = QueueManager(filepath=q_file)
    ingestor = TmdbTopIngestor(queue_manager=qm)

    async with session_factory() as session:
        await session.execute(text("DELETE FROM seed_candidates"))
        # Prepopulate Movie in DB
        session.add(MovieModel(title="Existing Movie", tmdb_id=201, code=201, publish_status="published"))
        # Prepopulate Blacklist
        session.add(BlacklistModel(title="Blacklisted Seed", reason="Pornographic"))
        # Prepopulate Rejected Item
        session.add(RejectedItemModel(media_type="movie", source="tmdb_seed", source_key="tmdb:movie:203", title="Rejected Seed", defects=[]))

        # Add 3 candidates to test skip logic
        cand_db = SeedCandidateModel(kind="movie", tmdb_id=201, title_en="Existing Movie", status="new")
        cand_bl = SeedCandidateModel(kind="movie", tmdb_id=202, title_en="Blacklisted Seed", status="new")
        cand_rej = SeedCandidateModel(kind="movie", tmdb_id=203, title_en="Rejected Seed", status="new")
        session.add_all([cand_db, cand_bl, cand_rej])
        await session.commit()

    with patch("scraper.tmdb_top_ingestor.async_session_factory", return_value=session_factory()):
        with patch("scraper.tmdb_top_ingestor.search_sites", AsyncMock(return_value=[])):
            stats = await ingestor.search_candidates(limit=10)
            assert stats["skipped"] == 3

    # Verify all 3 were marked status='skipped'
    async with session_factory() as session:
        c1 = (await session.execute(select(SeedCandidateModel).where(SeedCandidateModel.tmdb_id == 201))).scalar_one()
        assert c1.status == "skipped"
        c2 = (await session.execute(select(SeedCandidateModel).where(SeedCandidateModel.tmdb_id == 202))).scalar_one()
        assert c2.status == "skipped"
        c3 = (await session.execute(select(SeedCandidateModel).where(SeedCandidateModel.tmdb_id == 203))).scalar_one()
        assert c3.status == "skipped"


@pytest.mark.asyncio
async def test_s9_none_found_transitions_to_not_found(setup_test_db, engine, tmp_path):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    q_file = str(tmp_path / "test_queue.json")
    qm = QueueManager(filepath=q_file)
    ingestor = TmdbTopIngestor(queue_manager=qm)

    async with session_factory() as session:
        await session.execute(text("DELETE FROM seed_candidates"))
        cand = SeedCandidateModel(
            kind="movie",
            tmdb_id=301,
            title_en="Ultra Rare Film",
            status="new",
        )
        session.add(cand)
        await session.commit()

    # search_sites returns nothing
    with patch("scraper.tmdb_top_ingestor.async_session_factory", return_value=session_factory()):
        with patch("scraper.tmdb_top_ingestor.search_sites", AsyncMock(return_value=[])):
            stats = await ingestor.search_candidates(limit=10)
            assert stats["not_found"] == 1

    async with session_factory() as session:
        updated = (await session.execute(select(SeedCandidateModel).where(SeedCandidateModel.tmdb_id == 301))).scalar_one()
        assert updated.status == "not_found"
        assert updated.attempts == 1
        assert updated.last_searched_at is not None


@pytest.mark.asyncio
async def test_s9_remake_with_same_title_fails_year_check():
    # Gladiator 2000 vs Gladiator 1992
    is_match, reason = evaluate_candidate_match(
        seed_title_ru="Гладиатор",
        seed_title_en="Gladiator",
        seed_orig_title="Gladiator",
        seed_year=2000,
        scraped_title="Gladiator 1992",
        scraped_year=1992,
    )
    assert is_match is False
    assert "Yil mos kelmadi" in reason


@pytest.mark.asyncio
async def test_s9_rerunning_enqueue_creates_no_duplicate_queue_items(setup_test_db, engine, tmp_path):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    q_file = str(tmp_path / "test_queue.json")
    qm = QueueManager(filepath=q_file)
    ingestor = TmdbTopIngestor(queue_manager=qm)

    async with session_factory() as session:
        await session.execute(text("DELETE FROM seed_candidates WHERE tmdb_id = 401"))
        cand = SeedCandidateModel(
            kind="movie",
            tmdb_id=401,
            title_en="No Duplicate Enqueue Test",
            status="found",
            matches={"uzmovi": {"code": "4010", "url": "https://uzmovi.net/4010.html", "title": "Test", "score": 1.0}},
        )
        session.add(cand)
        await session.commit()

    mock_details = {
        "tmdb_id": 401,
        "content_type": "movie",
        "title": "No Duplicate Enqueue Test",
        "poster_url": "https://image.tmdb.org/t/p/w500/p.jpg",
        "release_year": 2020,
    }

    with patch("scraper.tmdb_top_ingestor.async_session_factory", return_value=session_factory()):
        with patch.object(tmdb_client, "get_details", AsyncMock(return_value=mock_details)):
            # 1st run
            res1 = await ingestor.enqueue_candidates(limit=10, execute=True)
            assert res1["enqueued"] == 1
            assert len(qm.items) == 1

            # 2nd run
            res2 = await ingestor.enqueue_candidates(limit=10, execute=True)
            # Item was already queued, so enqueued count is 0
            assert res2["enqueued"] == 0
            assert len(qm.items) == 1


@pytest.mark.asyncio
async def test_s9_ingestor_never_writes_to_movies_or_series(setup_test_db, engine, tmp_path):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    q_file = str(tmp_path / "test_queue.json")
    qm = QueueManager(filepath=q_file)
    ingestor = TmdbTopIngestor(queue_manager=qm)

    # Initial counts
    async with session_factory() as session:
        m_initial = (await session.execute(select(func.count(MovieModel.id)))).scalar()
        s_initial = (await session.execute(select(func.count(SeriesModel.id)))).scalar()

    mock_top = {
        "page": 1,
        "results": [
            {"id": 501, "title": "Safety Test Movie", "original_title": "Safety Test Movie", "adult": False, "vote_count": 2000, "vote_average": 8.0, "release_date": "2020-01-01"}
        ]
    }
    mock_search = [
        {"source": "uzmovi", "title": "Safety Test Movie 2020", "year": 2020, "url": "https://uzmovi.net/5010.html", "source_code": "5010"}
    ]
    mock_details = {
        "tmdb_id": 501,
        "content_type": "movie",
        "title": "Safety Test Movie",
        "poster_url": "https://image.tmdb.org/t/p/w500/test.jpg",
        "release_year": 2020,
    }

    with patch("scraper.tmdb_top_ingestor.async_session_factory", return_value=session_factory()):
        with patch.object(tmdb_client, "list_top_rated", AsyncMock(return_value=mock_top)):
            with patch.object(tmdb_client, "list_popular", AsyncMock(return_value={"page": 1, "results": []})):
                with patch.object(tmdb_client, "get_details", AsyncMock(return_value=mock_details)):
                    with patch("scraper.tmdb_top_ingestor.search_sites", AsyncMock(return_value=mock_search)):
                        with patch("scraper.tmdb_top_ingestor.SEED_MOVIE_TARGET", 1):
                            await ingestor.build_seeds()
                            await ingestor.search_candidates(limit=1)
                            await ingestor.enqueue_candidates(limit=1, execute=True)

    # Assert movies and series tables were NEVER written to by the ingestor
    async with session_factory() as session:
        m_final = (await session.execute(select(func.count(MovieModel.id)))).scalar()
        s_final = (await session.execute(select(func.count(SeriesModel.id)))).scalar()
        assert m_final == m_initial
        assert s_final == s_initial
