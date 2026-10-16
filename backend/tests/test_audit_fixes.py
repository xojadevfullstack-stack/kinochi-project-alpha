import pytest
from scraper.tmdb_top_ingestor import evaluate_candidate_match


def test_sf_001_adversarial_matcher_no_substring_false_positive():
    """
    SF-001: Substring trap bo'yicha turli xil filmlar (masalan 'Drive' va 'Drive Angry')
    yoki nomsiz yilda sikvellarning soxta ijobiy (False Positive) mos kelishini oldini olish.
    """
    # 1. Drive (2011) vs Drive Angry (2011) - turli filmlar, bir xil yil
    matched, reason = evaluate_candidate_match(
        seed_title_ru="Драйв",
        seed_title_en="Drive",
        seed_orig_title="Drive",
        seed_year=2011,
        scraped_title="Drive Angry / G'azabli drayv",
        scraped_year=2011,
        scraped_url="https://uzmovi.tv/803-drive-angry.html",
    )
    assert matched is False, f"Drive va Drive Angry mos kelmasligi kerak! Sabab: {reason}"

    # 2. Avatar: The Way of Water (2022) vs Avatar (scraped_year is None)
    matched2, reason2 = evaluate_candidate_match(
        seed_title_ru="Аватар: Путь воды",
        seed_title_en="Avatar: The Way of Water",
        seed_orig_title="Avatar: The Way of Water",
        seed_year=2022,
        scraped_title="Avatar",
        scraped_year=None,
        scraped_url="https://uzmovi.tv/103-avatar.html",
    )
    assert matched2 is False, f"Avatar 2 (subtitle) va Avatar (no year) mos kelmasligi kerak! Sabab: {reason2}"


@pytest.mark.asyncio
async def test_sf_002_empty_title_blacklist_does_not_match_all(setup_test_db, engine):
    """
    SF-002: Sarlavha bo'sh bo'lganda (title="") BlacklistModel dagi ixtiyoriy elementga
    LIKE '%%' orqali mos kelib, nomzodni asossiz rad etilishini oldini olish.
    """
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from app.infrastructure.db.models.blacklist import BlacklistModel
    from scraper.tmdb_top_ingestor import TmdbTopIngestor

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Qora ro'yxatga bitta film qo'shamiz
        banned = BlacklistModel(title="Zararli Film", url="https://example.com/banned/999")
        session.add(banned)
        await session.commit()

        ingestor = TmdbTopIngestor()

        # tmdb_id = 777777, title = "" (bo'sh satr)
        already_in, reason = await ingestor.is_candidate_already_in_system(
            session=session,
            kind="movie",
            tmdb_id=777777,
            title="",
        )

        assert already_in is False, f"Bo'sh sarlavha qora ro'yxatga mos kelmasligi kerak! Sabab: {reason}"

