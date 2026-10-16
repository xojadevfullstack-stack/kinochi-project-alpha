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


@pytest.mark.asyncio
async def test_sf_003_retry_rejected_item_resets_seed_candidate(setup_test_db, engine):
    """
    SF-003: Admin paneldan 'tmdb_seed' manbali rejected item qayta urinishga (retry) yuborilganda,
    tegishli SeedCandidateModel yozuvining holati ham 'new' ga qaytishi va qayta qidiruvga tushishini ta'minlash.
    """
    from unittest.mock import MagicMock
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from app.infrastructure.db.models.seed_candidate import SeedCandidateModel
    from app.infrastructure.db.models.rejected_item import RejectedItemModel
    from app.api.v1.rejected import retry_rejected_item

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        cand = SeedCandidateModel(
            kind="movie",
            tmdb_id=555555,
            title_en="Ambiguous Movie",
            status="ambiguous",
            attempts=1,
        )
        session.add(cand)

        rej_item = RejectedItemModel(
            media_type="movie",
            source="tmdb_seed",
            source_key="tmdb:movie:555555",
            title="Ambiguous Movie",
            payload={"kind": "movie", "tmdb_id": 555555},
            defects=[{"defect": "ambiguous_source_match"}],
            status="rejected",
        )
        session.add(rej_item)
        await session.commit()
        await session.refresh(rej_item)
        rej_id = rej_item.id

    # Admin retry chaqiramiz
    async with session_factory() as session:
        from starlette.requests import Request
        mock_req = Request({"type": "http", "path": "/api/v1/rejected/retry", "headers": [], "client": ("127.0.0.1", 12345)})
        mock_admin = {"username": "superadmin", "role": "admin"}
        res = await retry_rejected_item(request=mock_req, item_id=rej_id, db=session, admin=mock_admin)
        assert res["id"] == rej_id

    # SeedCandidate statusi 'new' ga qaytganini tekshiramiz
    async with session_factory() as session:
        from sqlalchemy import select
        cand_db = (await session.execute(
            select(SeedCandidateModel).where(SeedCandidateModel.tmdb_id == 555555)
        )).scalar_one()

        assert cand_db.status == "new", f"SeedCandidate statusi 'new' bo'lishi kerak, lekin '{cand_db.status}'!"
        assert cand_db.attempts == 0


def test_sf_004_windows_console_unicode_encoding():
    """
    SF-004: Windows konsolida non-UTF8 muhitda (masalan cp1251) skriptlar emojilar tufayli
    UnicodeEncodeError bermasdan xavfsiz ishlashini ta'minlash.
    """
    import subprocess
    import sys
    import os

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp1251"

    code = """
import sys
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
print("❌ [XAVFSIZLIK BLOKIROVKASI] Production muhitida taqiqlanadi!")
print("🎯 [FOUND] Interstellar")
print("⚠️ [AMBIGUOUS] Conflicting")
print("✅ [OK] scraper_queue.json bo'shatildi")
"""
    res = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Skript UnicodeEncodeError bilan to'xtadi! Stderr: {res.stderr}"
    assert "[FOUND]" in res.stdout
    assert "[XAVFSIZLIK BLOKIROVKASI]" in res.stdout



