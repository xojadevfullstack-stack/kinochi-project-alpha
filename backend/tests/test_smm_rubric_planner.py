from datetime import datetime, timedelta, timezone

import pytest

from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.smm import SmmClipJobModel
from app.infrastructure.db.models.translation import MovieTranslationModel
from scraper.smm_rubric_planner import (
    RUBRIC_MODES,
    digits_to_uz_2plus2_spoken,
    lat_to_uz_cyrillic_tts,
    pick_rubric_media,
    select_weekly_rubric,
)

TASHKENT_TZ = timezone(timedelta(hours=5))


def test_select_weekly_rubric_schedule_slots():
    # Daytime slots always pick ordinary 'scene'
    mon_day = datetime(2026, 11, 23, 11, 5, tzinfo=TASHKENT_TZ)
    assert select_weekly_rubric(mon_day, completed_today=[], completed_week=[]) == "scene"

    # Prime evening 21:00 slots rotate all 4 Golden Standard rubrics on Mon/Wed/Fri/Sun
    cases = [
        (datetime(2026, 11, 23, 21, 5, tzinfo=TASHKENT_TZ), "tavsiya"),
        (datetime(2026, 11, 24, 21, 5, tzinfo=TASHKENT_TZ), "scene"),
        (datetime(2026, 11, 25, 21, 5, tzinfo=TASHKENT_TZ), "bilasizmi"),
        (datetime(2026, 11, 27, 21, 5, tzinfo=TASHKENT_TZ), "yangiliklar"),
        (datetime(2026, 11, 29, 21, 5, tzinfo=TASHKENT_TZ), "kadr_ortida"),
    ]
    for dt, expected in cases:
        assert select_weekly_rubric(dt, completed_today=[], completed_week=[]) == expected

    # Never duplicate a rubric on the same day; catch up missed rubric if weekly slot empty
    mon_eve = datetime(2026, 11, 23, 21, 10, tzinfo=TASHKENT_TZ)
    assert select_weekly_rubric(mon_eve, completed_today=["tavsiya"], completed_week=["tavsiya"]) == "scene"
    assert set(RUBRIC_MODES) == {"tavsiya", "bilasizmi", "yangiliklar", "kadr_ortida"}


def test_digits_to_uz_2plus2_spoken_and_cyrillic_tts():
    assert digits_to_uz_2plus2_spoken("1012") == "o'n, o'n ikki"
    assert digits_to_uz_2plus2_spoken("3955") == "o'ttiz to'qqiz, ellik besh"
    assert digits_to_uz_2plus2_spoken("1091") == "o'n, to'qson bir"
    assert digits_to_uz_2plus2_spoken("0508") == "nol besh, nol sakkiz"

    cyr = lat_to_uz_cyrillic_tts("Yo'l to'liq o'zbek tilida qo'shildi. Shoshmang!")
    assert "ў" in cyr and "қ" in cyr and "ш" in cyr
    assert "йўл" in cyr.lower()
    assert "қўшилди" in cyr.lower()


@pytest.mark.asyncio
async def test_pick_rubric_media_selects_eligible_movie_by_rubric(db_session):
    m_old_gem = MovieModel(
        title="Muqaddima",
        code="A1012",
        short_code="1012",
        release_year=2010,
        imdb_rating=8.4,
        tmdb_id=27205,
        genres="Triller, Fantastika",
        publish_status="published",
    )
    m_new_prem = MovieModel(
        title="Yulduzlar sari",
        code="A3955",
        short_code="3955",
        release_year=2026,
        imdb_rating=8.1,
        tmdb_id=1359005,
        genres="Fantastika",
        publish_status="published",
    )
    db_session.add_all([m_old_gem, m_new_prem])
    await db_session.flush()
    db_session.add_all([
        MovieTranslationModel(movie_id=m_old_gem.id, language="O'zbek tilida", storage_channel_message_id=111),
        MovieTranslationModel(movie_id=m_new_prem.id, language="O'zbek tilida", storage_channel_message_id=222),
    ])
    await db_session.flush()

    prem = await pick_rubric_media(db_session, "yangiliklar")
    assert prem is not None and prem["movie_code"] == "3955"

    # Mark 3955 used -> bilasizmi must pick 1012
    db_session.add(SmmClipJobModel(movie_code="3955", title="Yulduzlar sari", media_id=m_new_prem.id, clip_mode="yangiliklar", status="completed"))
    await db_session.flush()

    gem = await pick_rubric_media(db_session, "bilasizmi")
    assert gem is not None and gem["movie_code"] == "1012"
