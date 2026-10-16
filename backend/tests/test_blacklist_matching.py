import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.infrastructure.db.models.blacklist import BlacklistModel
from scraper.tmdb_top_ingestor import TmdbTopIngestor, extract_tmdb_ids_from_url


def test_extract_tmdb_ids_from_url():
    """
    URL ichidan alohida raqamli identifikatorlarni ajratib olish tekshiruvi.
    155 raqami 71550 ichidagi substring sifatida olinmasligi kerak.
    """
    assert 71550 in extract_tmdb_ids_from_url("https://www.themoviedb.org/movie/71550")
    assert 155 not in extract_tmdb_ids_from_url("https://www.themoviedb.org/movie/71550")

    assert 155 in extract_tmdb_ids_from_url("https://www.themoviedb.org/movie/155-the-dark-knight")
    assert 155 in extract_tmdb_ids_from_url("tmdb:155")
    assert 155 in extract_tmdb_ids_from_url("https://example.com/banned/155")
    assert 155 in extract_tmdb_ids_from_url("https://api.themoviedb.org/3/movie/155")


@pytest.mark.asyncio
async def test_blacklist_tmdb_id_155_vs_url_71550(setup_test_db, engine):
    """
    Regression Test 1: tmdb_id 155 URL da ...71550 bo'lgan yozuvga
    '%155%' substring qoidasi sababli mos kelib qolmasligi shart.
    """
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        banned = BlacklistModel(
            title="Boshqa Film",
            url="https://www.themoviedb.org/movie/71550",
            reason="Test"
        )
        session.add(banned)
        await session.commit()

        ingestor = TmdbTopIngestor()

        # tmdb_id = 155 (The Dark Knight) hech qachon 71550 ga mos kelmasligi kerak
        already_in, reason = await ingestor.is_candidate_already_in_system(
            session=session,
            kind="movie",
            tmdb_id=155,
            title="The Dark Knight"
        )
        assert already_in is False, f"tmdb_id 155 url 71550 ga mos kelmasligi kerak! Sabab: {reason}"


@pytest.mark.asyncio
async def test_blacklist_avatar_sequel_does_not_block_avatar(setup_test_db, engine):
    """
    Regression Test 2: Qora ro'yxatdagi 'Avatar: The Way of Water'
    asl 'Avatar' filmini bloklab qo'ymasligi shart.
    """
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        banned = BlacklistModel(
            title="Avatar: The Way of Water",
            url="https://example.com/avatar-2",
            reason="Buzilgan"
        )
        session.add(banned)
        await session.commit()

        ingestor = TmdbTopIngestor()

        # 'Avatar' filmi bloklanmasligi shart
        already_in, reason = await ingestor.is_candidate_already_in_system(
            session=session,
            kind="movie",
            tmdb_id=19995,
            title="Avatar"
        )
        assert already_in is False, f"'Avatar' filmi 'Avatar: The Way of Water' sababli bloklanmasligi kerak! Sabab: {reason}"

        # Lekin aynan 'Avatar: The Way of Water' qidirilganda bloklanishi kerak
        already_in_sequel, reason_seq = await ingestor.is_candidate_already_in_system(
            session=session,
            kind="movie",
            tmdb_id=76600,
            title="Avatar: The Way of Water"
        )
        assert already_in_sequel is True, f"Aynan bir xil sarlavha bloklanishi kerak! Sabab: {reason_seq}"
