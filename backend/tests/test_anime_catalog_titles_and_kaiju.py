import pytest
import sys, os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import select
from app.infrastructure.db.models import MovieModel, SeriesModel, SeasonModel, EpisodeModel
from app.infrastructure.db.models.translation import EpisodeTranslationModel
from scraper.smart_enricher import ANIME_TITLE_MAP


def test_anime_title_map_canonical_entries():
    """Barcha muammoli nomlar uchun kanonik xaritalar mavjudligini tasdiqlaydi."""
    # 1. Chainsaw Man Reze Arc (film)
    reze = ANIME_TITLE_MAP.get("arra odam arc")
    assert reze is not None
    assert reze["tmdb_id"] == 1218925
    assert reze["type"] == "movie"
    assert reze["uz"] == "Chainsaw Man: Reze hikoyasi"

    reze_en = ANIME_TITLE_MAP.get("chainsaw man reze arc")
    assert reze_en is not None
    assert reze_en["tmdb_id"] == 1218925
    assert reze_en["type"] == "movie"

    # 2. Kaiju: 8-son
    kaiju = ANIME_TITLE_MAP.get("kaiju 8")
    assert kaiju is not None
    assert kaiju["tmdb_id"] == 207468
    assert kaiju["uz"] == "Kaiju: 8-son"

    kaiju_typo = ANIME_TITLE_MAP.get("kaiju ra 8-son")
    assert kaiju_typo is not None
    assert kaiju_typo["uz"] == "Kaiju: 8-son"

    # 3. Qilich san'ati onlayn (SAO)
    sao = ANIME_TITLE_MAP.get("qilich o'nlay magistrlari")
    assert sao is not None
    assert sao["uz"] == "Qilich san'ati onlayn"
    assert sao["tmdb_id"] == 45782

    # 4. Kelajak kundaligi (Mirai Nikki)
    mirai = ANIME_TITLE_MAP.get("kelajak kundlami")
    assert mirai is not None
    assert mirai["uz"] == "Kelajak kundaligi"
    assert mirai["tmdb_id"] == 46671

    # 5. U dunyo tsugaylari (Yomi no Tsugai)
    tsugai = ANIME_TITLE_MAP.get("u dunyo zugaylari")
    assert tsugai is not None
    assert tsugai["uz"] == "U dunyo tsugaylari"
    assert tsugai["tmdb_id"] == 260463

    # 6. Solo Leveling
    solo = ANIME_TITLE_MAP.get("solo leveling")
    assert solo is not None
    assert solo["uz"] == "Yakkaxon daraja oshirish (Solo Leveling)"
    assert solo["tmdb_id"] == 127532

    # 7. Black Clover (Qora klever)
    clover = ANIME_TITLE_MAP.get("qora klever")
    assert clover is not None
    assert clover.get("uz") == "Qora klever"
    assert clover.get("tmdb_id") == 73223
    assert clover.get("type") == "tv"

    clover_en = ANIME_TITLE_MAP.get("black clover")
    assert clover_en is not None
    assert clover_en.get("uz") == "Qora klever"
    assert clover_en.get("tmdb_id") == 73223

    # 8. A Silent Voice (Ovoz shakli / Koe no Katachi)
    silent = ANIME_TITLE_MAP.get("a silent voice")
    assert silent is not None
    assert silent.get("tmdb_id") == 378064
    assert silent.get("type") == "movie"
    assert silent.get("uz") == "A Silent Voice (Ovoz shakli)"

    silent_uz = ANIME_TITLE_MAP.get("ovoz shakli")
    assert silent_uz is not None
    assert silent_uz.get("tmdb_id") == 378064
    assert silent_uz.get("type") == "movie"


@pytest.mark.asyncio
async def test_kaiju_sequence_gap_detection_and_consecutive_flow(db_session):
    """Qismlar ketma-ketligi buzilishi va bo'shliqlar yo'qligini DB modeli darajasida tasdiqlaydi."""
    # Create test series
    series = SeriesModel(
        title="Kaiju: 8-son",
        status="ongoing",
        publish_status="published",
        tmdb_id=207468,
        release_year=2024
    )
    db_session.add(series)
    await db_session.flush()

    # Create season 1
    season = SeasonModel(
        series_id=series.id,
        season_number=1,
        title="1-fasl",
        episode_count=12
    )
    db_session.add(season)
    await db_session.flush()

    # Add 12 consecutive episodes
    for ep_num in range(1, 13):
        ep = EpisodeModel(
            season_id=season.id,
            episode_number=ep_num,
            code=f"KAIJU{ep_num:02d}",
            display_code=f"S1-CH{ep_num}",
            title=f"{ep_num}-qism",
            duration=24
        )
        db_session.add(ep)
        await db_session.flush()

        trans = EpisodeTranslationModel(
            episode_id=ep.id,
            language="O'zbekcha",
            telegram_file_id=f"file_id_test_{ep_num}",
            storage_channel_message_id=2700 + ep_num
        )
        db_session.add(trans)

    await db_session.commit()

    # Verify query
    res = await db_session.execute(
        select(EpisodeModel)
        .where(EpisodeModel.season_id == season.id)
        .order_by(EpisodeModel.episode_number)
    )
    eps = res.scalars().all()

    assert len(eps) == 12
    # Verify no gaps
    for idx, ep in enumerate(eps, start=1):
        assert ep.episode_number == idx
        assert ep.title == f"{idx}-qism"
        assert ep.display_code == f"S1-CH{idx}"


@pytest.mark.asyncio
async def test_chainsaw_man_reze_movie_card(db_session):
    """Chainsaw Man Reze hikoyasi film kartochkasi to'g'ri maydonlar bilan saqlanishini tasdiqlaydi."""
    movie = MovieModel(
        title="Chainsaw Man: Reze hikoyasi",
        original_title="劇場版 チェンソーマン レゼ篇",
        code="N6NCRY01",
        tmdb_id=1218925,
        release_year=2025,
        runtime=100,
        tmdb_rating=8.5,
        genres="Animatsiya, Jangari, Melodrama, Fantaziya",
        description="Yosh iblis ovchisi Denji haqida hikoya."
    )
    db_session.add(movie)
    await db_session.commit()

    res = await db_session.execute(select(MovieModel).where(MovieModel.code == "N6NCRY01"))
    saved_m = res.scalar_one_or_none()

    assert saved_m is not None
    assert saved_m.title == "Chainsaw Man: Reze hikoyasi"
    assert saved_m.original_title == "劇場版 チェンソーマン レゼ篇"
    assert saved_m.tmdb_id == 1218925
    assert saved_m.runtime == 100
    assert saved_m.release_year == 2025


def test_anitoob_button_pattern_matcher():
    """AniToob qismlar tugmasi regex va moslik qoidalarini tekshiradi."""
    import re
    def matches_ep(btn_text: str, current_ep: int) -> bool:
        b_txt = btn_text.strip()
        if b_txt == str(current_ep) or b_txt == f"{current_ep}-qism" or b_txt == f"[💽] - {current_ep}" or b_txt == f"[{current_ep}] - 💽":
            return True
        if re.match(rf'^(\[|\()?\s*{current_ep}\s*(\]|\))?(\s*-\s*qism|\s*qism|\s*💽)?$', b_txt, re.IGNORECASE):
            return True
        return False

    assert matches_ep("20", 20) is True
    assert matches_ep("20-qism", 20) is True
    assert matches_ep("[20]", 20) is True
    assert matches_ep("[💽] - 20", 20) is True
    assert matches_ep("[20] - 💽", 20) is True
    assert matches_ep("20 qism", 20) is True
    assert matches_ep("21", 20) is False
    assert matches_ep("2-qism", 20) is False
