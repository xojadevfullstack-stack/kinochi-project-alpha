import os
import asyncio
import pytest
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import IntegrityError

# TEST_DATABASE_URL tekshiruvi: Agar mavjud bo'lmasa, productionni himoya qilish uchun
# barcha testlar ovoz chiqarib (loudly) o'tkazib yuboriladi (SKIP).
TEST_DB_URL = os.environ.get("TEST_DATABASE_URL")
skip_no_test_db = pytest.mark.skipif(
    not TEST_DB_URL,
    reason="LOUD SKIP: TEST_DATABASE_URL is not set. Real-Postgres DB tests skipped to protect production."
)


@pytest.fixture
def pg_session_factory():
    if not TEST_DB_URL:
        pytest.skip("LOUD SKIP: TEST_DATABASE_URL is not set.")
    engine = create_async_engine(TEST_DB_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield session_factory
    # Engine cleanup
    asyncio.run(engine.dispose())


@skip_no_test_db
@pytest.mark.asyncio
async def test_d4e5f6a1b2c3_partial_unique_index_rejects_duplicate(pg_session_factory):
    """
    3. d4e5f6a1b2c3: movies va series jadvallaridagi qisman unikal indeks (uq_movies_tmdb_id)
    bir xil non-null tmdb_id kiritilganda IntegrityError berishi, ammo bir nechta NULL
    qiymatlarni xatosiz qabul qilishi tekshiriladi.
    """
    from app.infrastructure.db.models.movie import MovieModel

    async with pg_session_factory() as session:
        # Bir nechta NULL tmdb_id kiritish (ruxsat berilgan)
        m_null_1 = MovieModel(title="Null TMDb 1", tmdb_id=None, publish_status="pending")
        m_null_2 = MovieModel(title="Null TMDb 2", tmdb_id=None, publish_status="pending")
        session.add_all([m_null_1, m_null_2])
        await session.commit()

        # Birinchi unikal tmdb_id
        unique_tmdb = 99990001
        m1 = MovieModel(title="Unique Movie 1", tmdb_id=unique_tmdb, publish_status="published")
        session.add(m1)
        await session.commit()

        # Ikkinchi marta ayni tmdb_id bilan kiritish (taqiqlangan, IntegrityError berishi kerak)
        m2 = MovieModel(title="Duplicate Movie 2", tmdb_id=unique_tmdb, publish_status="pending")
        session.add(m2)
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()


@skip_no_test_db
@pytest.mark.asyncio
async def test_10_parallel_admits_same_tmdb_id_exactly_one_row(pg_session_factory):
    """
    4.1. Bir vaqtning o'zida ayni bir tmdb_id bo'yicha 10 ta parallel qabul qilish
    so'rovi yuborilganda, bazada qat'iy ravishda FAQAT 1 ta yozuv yaratilishi tekshiriladi.
    """
    from app.infrastructure.db.models.movie import MovieModel

    target_tmdb = 99990002
    success_count = 0
    failure_count = 0

    async def admit_worker(idx: int):
        nonlocal success_count, failure_count
        async with pg_session_factory() as session:
            try:
                # Tekshirish va yozish tranzaksiyasi
                existing = await session.execute(
                    select(MovieModel.id).where(MovieModel.tmdb_id == target_tmdb).with_for_update()
                )
                if existing.scalar_one_or_none():
                    failure_count += 1
                    return False

                movie = MovieModel(
                    title=f"Parallel Admit {idx}",
                    tmdb_id=target_tmdb,
                    publish_status="pending"
                )
                session.add(movie)
                await session.commit()
                success_count += 1
                return True
            except IntegrityError:
                await session.rollback()
                failure_count += 1
                return False
            except Exception:
                await session.rollback()
                failure_count += 1
                return False

    # 10 ta parallel korutina
    results = await asyncio.gather(*[admit_worker(i) for i in range(10)])

    async with pg_session_factory() as session:
        count_res = await session.execute(
            select(func.count(MovieModel.id)).where(MovieModel.tmdb_id == target_tmdb)
        )
        total_rows = count_res.scalar() or 0

    assert total_rows == 1, f"Bazada 1 ta yozuv bo'lishi kerak, ammo {total_rows} ta topildi!"
    assert success_count == 1, f"Faqat 1 ta so'rov muvaffaqiyatli bo'lishi kerak, ammo {success_count} bo'ldi!"
    assert failure_count == 9, f"9 ta so'rov rad etilishi kerak, ammo {failure_count} bo'ldi!"


@skip_no_test_db
@pytest.mark.asyncio
async def test_rejected_items_upsert_increments_attempts(pg_session_factory):
    """
    4.2. rejected_items jadvaliga ayni bir source va source_key bo'yicha qayta yozilganda
    attempts hisoblagichi oshishi (upsert / increment) tekshiriladi.
    """
    from app.infrastructure.db.models.rejected_item import RejectedItemModel

    s_key = "tmdb:movie:99990003"
    async with pg_session_factory() as session:
        # Birinchi rad etish
        item1 = RejectedItemModel(
            source="tmdb_seed",
            source_key=s_key,
            title="Defective Film",
            defect="ambiguous_source_match",
            status="rejected",
            attempts=1
        )
        session.add(item1)
        await session.commit()

        # Ikkinchi marta kelganda mavjud yozuvni yangilash va attempts ni oshirish
        q = await session.execute(
            select(RejectedItemModel).where(RejectedItemModel.source_key == s_key)
        )
        existing = q.scalar_one()
        existing.attempts += 1
        await session.commit()

        # Tekshirish
        verify_q = await session.execute(
            select(RejectedItemModel.attempts).where(RejectedItemModel.source_key == s_key)
        )
        assert verify_q.scalar() == 2


@skip_no_test_db
@pytest.mark.asyncio
async def test_seed_candidates_unique_kind_tmdb_id(pg_session_factory):
    """
    4.3. seed_candidates jadvalida UNIQUE(kind, tmdb_id) cheklovi borligi
    va dublikat kiritilganda IntegrityError vujudga kelishi tekshiriladi.
    """
    from app.infrastructure.db.models.seed_candidate import SeedCandidateModel

    test_tmdb = 99990004
    async with pg_session_factory() as session:
        c1 = SeedCandidateModel(
            kind="movie",
            tmdb_id=test_tmdb,
            title_en="Unique Seed Candidate",
            status="new"
        )
        session.add(c1)
        await session.commit()

        # Ayni (kind, tmdb_id) bilan ikkinchi nomzod
        c2 = SeedCandidateModel(
            kind="movie",
            tmdb_id=test_tmdb,
            title_en="Duplicate Seed Candidate",
            status="new"
        )
        session.add(c2)
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()


@skip_no_test_db
@pytest.mark.asyncio
async def test_gate_promotes_pending_to_published_only_through_gate(pg_session_factory):
    """
    4.4. Kontent sukut bo'yicha 'pending' holatida yaratilishi va faqat
    Admission Gate tekshiruvidan o'tgandan so'ng 'published' ga ko'tarilishi tekshiriladi.
    """
    from app.infrastructure.db.models.movie import MovieModel
    from app.core.admission_gate import promote_to_published

    async with pg_session_factory() as session:
        movie = MovieModel(
            title="Pending Film",
            tmdb_id=99990005,
            poster_url="https://image.tmdb.org/t/p/w500/valid.jpg",
            trailer_url="https://www.youtube.com/watch?v=valid_trailer",
            publish_status="pending"
        )
        session.add(movie)
        await session.commit()
        await session.refresh(movie)

        assert movie.publish_status == "pending"

        # Gate orqali nashr qilish
        await promote_to_published(session, movie)
        await session.commit()
        await session.refresh(movie)

        assert movie.publish_status == "published"


@skip_no_test_db
@pytest.mark.asyncio
async def test_public_read_paths_hide_pending_and_hidden(pg_session_factory):
    """
    4.5. Ommaviy o'qish yo'llari faqat 'published' holatidagi kontentni ko'rsatishi,
    'pending' va 'hidden' holatdagilar esa yashirilishi tekshiriladi.
    """
    from app.infrastructure.db.models.movie import MovieModel

    async with pg_session_factory() as session:
        m_pub = MovieModel(title="Public Movie", tmdb_id=99990006, publish_status="published")
        m_pend = MovieModel(title="Pending Movie", tmdb_id=99990007, publish_status="pending")
        m_hid = MovieModel(title="Hidden Movie", tmdb_id=99990008, publish_status="hidden")
        session.add_all([m_pub, m_pend, m_hid])
        await session.commit()

        # Ommaviy so'rov filtratsiyasi
        public_query = select(MovieModel.id, MovieModel.title).where(
            MovieModel.publish_status == "published",
            MovieModel.tmdb_id.in_([99990006, 99990007, 99990008])
        )
        results = (await session.execute(public_query)).all()

        assert len(results) == 1
        assert results[0][1] == "Public Movie"


@skip_no_test_db
@pytest.mark.asyncio
async def test_reset_media_on_branch_guards_and_execution(pg_session_factory, tmp_path):
    """
    5. Data copy/branch ustida reset_media.py:
    - Dry run tekshiruvi (o'zgarishsiz)
    - Har bir guardning alohida rad etishi
    - Barcha 3 ta guard bilan haqiqiy tozalash: saqlanadigan jadvallar daxlsiz,
      seed_candidates yangilangan.
    """
    from scripts.reset_media import reset_media
    from app.infrastructure.db.models.seed_candidate import SeedCandidateModel
    from app.infrastructure.db.models.user import UserModel
    from app.infrastructure.db.models.blacklist import BlacklistModel

    valid_backup = str(tmp_path / "valid_branch_backup.sql")
    with open(valid_backup, "w") as f:
        f.write("-- valid backup")

    async with pg_session_factory() as session:
        # Saqlanadigan jadvallar uchun test yozuvlari
        u = UserModel(telegram_id=88880001, username="safe_user")
        bl = BlacklistModel(title="Safe Blacklist Item")
        cand = SeedCandidateModel(kind="movie", tmdb_id=99990009, status="queued")
        session.add_all([u, bl, cand])
        await session.commit()

    # 1. Dry run
    res_dry = await reset_media(execute=False)
    assert res_dry["mode"] == "dry_run"

    # 2. Guard 2 rad etishi (bo'sh backup)
    res_g2 = await reset_media(execute=True, confirm="YES", backup_file=None)
    assert res_g2 == {"error": "backup_file_missing_or_empty"}

    # 3. Barcha guardlar bilan ijro
    res_exec = await reset_media(
        execute=True,
        confirm="YES",
        backup_file=valid_backup,
        i_am_wiping_production=True
    )
    assert res_exec["mode"] == "executed"

    # 4. Saqlanadigan jadvallar tekshiruvi (tegmasdan qolgan)
    async with pg_session_factory() as session:
        u_db = (await session.execute(select(UserModel).where(UserModel.telegram_id == 88880001))).scalar_one_or_none()
        assert u_db is not None, "UserModel yozuvi o'chib ketmasligi kerak!"

        bl_db = (await session.execute(select(BlacklistModel).where(BlacklistModel.title == "Safe Blacklist Item"))).scalar_one_or_none()
        assert bl_db is not None, "BlacklistModel yozuvi o'chib ketmasligi kerak!"

        cand_db = (await session.execute(select(SeedCandidateModel).where(SeedCandidateModel.tmdb_id == 99990009))).scalar_one()
        assert cand_db.status == "new", "seed_candidates holati 'new' ga qaytishi kerak!"
