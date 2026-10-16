import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select, text
from app.infrastructure.db.models.seed_candidate import SeedCandidateModel
from app.infrastructure.db.models.rejected_item import RejectedItemModel
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel
from app.infrastructure.external.tmdb_client import tmdb_client
from scraper.tmdb_top_ingestor import evaluate_candidate_match, TmdbTopIngestor
from scraper.queue_manager import QueueManager, QueueItem


def test_evaluate_candidate_match_exact():
    is_match, reason = evaluate_candidate_match(
        seed_title_ru="Интерстеллар",
        seed_title_en="Interstellar",
        seed_orig_title="Interstellar",
        seed_year=2014,
        scraped_title="Interstellar Uzbek tilida 2014 HD",
        scraped_year=2014,
        scraped_url="https://uzmovi.net/6282-interstellar.html",
    )
    assert is_match is True
    assert "mos keldi" in reason


def test_evaluate_candidate_match_wrong_year():
    # Remake or different movie with same title but > 1 year apart
    is_match, reason = evaluate_candidate_match(
        seed_title_ru="Гладиатор",
        seed_title_en="Gladiator",
        seed_orig_title="Gladiator",
        seed_year=2000,
        scraped_title="Gladiator Uzbek tilida 1992",
        scraped_year=1992,
        scraped_url="https://uzmovi.net/gladiator-1992.html",
    )
    assert is_match is False
    assert "Yil mos kelmadi" in reason


def test_evaluate_candidate_match_part_number_sequel():
    # Avatar 2 vs Avatar 1
    is_match, reason = evaluate_candidate_match(
        seed_title_ru="Аватар 2: Путь воды",
        seed_title_en="Avatar: The Way of Water",
        seed_orig_title="Avatar 2",
        seed_year=2022,
        scraped_title="Avatar 1 Uzbek tilida 2009",
        scraped_year=2009,
        scraped_url="https://uzmovi.net/avatar-1.html",
    )
    assert is_match is False
    assert "Qism raqami mos kelmadi" in reason or "Yil mos kelmadi" in reason


def test_queue_manager_priority_ordering(tmp_path):
    q_file = str(tmp_path / "test_queue.json")
    qm = QueueManager(filepath=q_file)

    item_low = QueueItem(id="low_1", source="uzmovi", title="Oddiy film", priority=0)
    item_high = QueueItem(id="high_1", source="uzmovi", title="TMDb Top Film", priority=100)
    item_mid = QueueItem(id="mid_1", source="uzmovi", title="O'rtacha film", priority=50)

    qm.add_item(item_low)
    qm.add_item(item_high)
    qm.add_item(item_mid)

    pending = qm.get_pending(limit=10)
    assert len(pending) == 3
    assert pending[0].id == "high_1"
    assert pending[0].priority == 100
    assert pending[1].id == "mid_1"
    assert pending[2].id == "low_1"


@pytest.mark.asyncio
async def test_search_candidates_ambiguous_writes_to_rejected_items(setup_test_db, engine, tmp_path):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    q_file = str(tmp_path / "test_queue.json")
    qm = QueueManager(filepath=q_file)
    ingestor = TmdbTopIngestor(queue_manager=qm)

    async with session_factory() as session:
        cand = SeedCandidateModel(
            kind="movie",
            tmdb_id=999991,
            title_en="Conflicting Film",
            title_ru="Конфликтный фильм",
            original_title="Conflicting Film",
            release_year=2023,
            status="new",
        )
        session.add(cand)
        await session.commit()

    # Mock search_sites returning 2 distinct passing candidates -> ambiguous!
    mock_results = [
        {"source": "uzmovi", "title": "Conflicting Film 2023", "year": 2023, "url": "https://uzmovi.net/100-conflicting.html", "source_code": "100"},
        {"source": "uzmovi", "title": "Conflicting Film (Dublyaj) 2023", "year": 2023, "url": "https://uzmovi.net/200-conflicting.html", "source_code": "200"},
    ]

    with patch("scraper.tmdb_top_ingestor.async_session_factory", return_value=session_factory()):
        with patch("scraper.tmdb_top_ingestor.search_sites", AsyncMock(return_value=mock_results)):
            stats = await ingestor.search_candidates(limit=10)
            assert stats["ambiguous"] == 1

    # Verify rejected_items recorded defect
    async with session_factory() as session:
        res = await session.execute(
            select(RejectedItemModel).where(RejectedItemModel.source_key == "tmdb:movie:999991")
        )
        rej = res.scalar_one()
        assert rej.status == "rejected"
        assert rej.source == "tmdb_seed"
        assert rej.defects[0]["defect"] == "ambiguous_source_match"


@pytest.mark.asyncio
async def test_enqueue_dry_run_vs_execute(setup_test_db, engine, tmp_path):
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    q_file = str(tmp_path / "test_queue.json")
    qm = QueueManager(filepath=q_file)
    ingestor = TmdbTopIngestor(queue_manager=qm)

    async with session_factory() as session:
        # Test izolyatsiyasi: faqat ushbu testdagi nomzodni qoldiramiz
        await session.execute(text("DELETE FROM seed_candidates"))
        cand = SeedCandidateModel(
            kind="movie",
            tmdb_id=888881,
            title_en="Approved Movie",
            title_ru="Одобренный фильм",
            original_title="Approved Movie",
            release_year=2021,
            status="found",
            matches={"uzmovi": {"code": "5555", "url": "https://uzmovi.net/5555.html", "title": "Approved Movie", "score": 1.0}},
        )
        session.add(cand)
        await session.commit()

    mock_details = {
        "tmdb_id": 888881,
        "content_type": "movie",
        "title": "Approved Movie",
        "poster_url": "https://image.tmdb.org/t/p/w500/poster.jpg",
        "trailer_url": "https://youtube.com/watch?v=123",
        "overview": "Tavsif",
        "release_year": 2021,
    }

    # 1. DRY-RUN
    with patch("scraper.tmdb_top_ingestor.async_session_factory", return_value=session_factory()):
        with patch.object(tmdb_client, "get_details", AsyncMock(return_value=mock_details)):
            stats_dry = await ingestor.enqueue_candidates(limit=10, execute=False)
            assert stats_dry["enqueued"] == 1
            # In Dry-run, QM should have 0 items!
            assert len(qm.items) == 0

    # 2. EXECUTE
    with patch("scraper.tmdb_top_ingestor.async_session_factory", return_value=session_factory()):
        with patch.object(tmdb_client, "get_details", AsyncMock(return_value=mock_details)):
            stats_exec = await ingestor.enqueue_candidates(limit=10, execute=True)
            assert stats_exec["enqueued"] == 1
            # Now QM has 1 item with priority 100
            assert "uzmovi_5555" in qm.items
            assert qm.items["uzmovi_5555"].priority == 100
            assert qm.items["uzmovi_5555"].tmdb_id == 888881

    # 3. Assert ingestor never wrote to movies or series
    async with session_factory() as session:
        m_res = await session.execute(select(MovieModel).where(MovieModel.tmdb_id == 888881))
        assert m_res.scalar_one_or_none() is None
        s_res = await session.execute(select(SeriesModel).where(SeriesModel.tmdb_id == 888881))
        assert s_res.scalar_one_or_none() is None
