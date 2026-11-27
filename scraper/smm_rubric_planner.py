"""Weekly 4-Rubric SMM Planner, Media Selector & Uzbek Phonetic TTS Helper."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Iterable, Optional

from sqlalchemy import exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.smm import SmmClipJobModel
from app.infrastructure.db.models.translation import MovieTranslationModel

RUBRIC_MODES: tuple[str, ...] = ("tavsiya", "bilasizmi", "yangiliklar", "kadr_ortida")

# Mon(0)=Tavsiya, Wed(2)=Bilasizmi, Fri(4)=Yangiliklar, Sun(6)=Kadr Ortida at evening prime slot
WEEKLY_PRIME_SCHEDULE: dict[int, str] = {
    0: "tavsiya",
    2: "bilasizmi",
    4: "yangiliklar",
    6: "kadr_ortida",
}

_ONES = ("nol", "bir", "ikki", "uch", "to'rt", "besh", "olti", "yetti", "sakkiz", "to'qqiz")
_TENS = ("", "o'n", "yigirma", "o'ttiz", "qirq", "ellik", "oltmish", "yetmish", "sakson", "to'qson")


def _two_digits_uz(pair: str) -> str:
    n = int(pair)
    if pair.startswith("0") and len(pair) == 2:
        return f"nol {_ONES[int(pair[1])]}"
    t, o = divmod(n, 10)
    return _TENS[t] if o == 0 else f"{_TENS[t]} {_ONES[o]}"


def digits_to_uz_2plus2_spoken(code: str) -> str:
    """Read numeric code cleanly as 2+2 digit Uzbek pairs (e.g., 1012 -> \"o'n, o'n ikki\")."""
    digits = "".join(ch for ch in str(code or "") if ch.isdigit())
    if not digits:
        return ""
    if len(digits) == 4:
        return f"{_two_digits_uz(digits[:2])}, {_two_digits_uz(digits[2:])}"
    if len(digits) % 2 == 0 and len(digits) <= 6:
        return ", ".join(_two_digits_uz(digits[i : i + 2]) for i in range(0, len(digits), 2))
    return " ".join(_ONES[int(d)] for d in digits)


def lat_to_uz_cyrillic_tts(text: str) -> str:
    """Convert Latin Uzbek text to Cyrillic Uzbek for clean rounded o' (ў) / q / g' TTS."""
    s = (text or "").replace("\u02bb", "'").replace("\u02bc", "'").replace("\u2018", "'").replace("\u2019", "'")
    # Preserve common Cyrillic-friendly substitutions for digraphs and apostrophe letters
    repl_multi = [
        ("O'", "Ў"), ("o'", "ў"),
        ("G'", "Ғ"), ("g'", "ғ"),
        ("SH", "Ш"), ("Sh", "Ш"), ("sh", "ш"),
        ("CH", "Ч"), ("Ch", "Ч"), ("ch", "ч"),
        ("YO", "Ё"), ("Yo", "Ё"), ("yo", "ё"),
        ("YA", "Я"), ("Ya", "Я"), ("ya", "я"),
        ("YU", "Ю"), ("Yu", "Ю"), ("yu", "ю"),
        ("YE", "Е"), ("Ye", "Е"), ("ye", "е"),
        ("TS", "Ц"), ("Ts", "Ц"), ("ts", "ц"),
    ]
    for a, b in repl_multi:
        s = s.replace(a, b)

    # Initial/post-vowel 'e' -> 'э' so Uzbek /e/ stays unpalatalized
    s = re.sub(r"(?<![A-Za-zЎҒШЧЁЯЮЕЦўғшчёяюец])E", "Э", s)
    s = re.sub(r"(?<![A-Za-zЎҒШЧЁЯЮЕЦўғшчёяюец])e", "э", s)
    s = s.replace("'", "ъ")

    cmap = str.maketrans({
        "A": "А", "B": "Б", "D": "Д", "E": "Е", "F": "Ф", "G": "Г", "H": "Ҳ",
        "I": "И", "J": "Ж", "K": "К", "L": "Л", "M": "М", "N": "Н", "O": "О",
        "P": "П", "Q": "Қ", "R": "Р", "S": "С", "T": "Т", "U": "У", "V": "В",
        "X": "Х", "Y": "Й", "Z": "З",
        "a": "а", "b": "б", "d": "д", "e": "е", "f": "ф", "g": "г", "h": "ҳ",
        "i": "и", "j": "ж", "k": "к", "l": "л", "m": "м", "n": "н", "o": "о",
        "p": "п", "q": "қ", "r": "р", "s": "с", "t": "т", "u": "у", "v": "в",
        "x": "х", "y": "й", "z": "з",
    })
    return s.translate(cmap)


def select_weekly_rubric(
    now_local: datetime,
    completed_today: Iterable[str] = (),
    completed_week: Iterable[str] = (),
    prime_hour_min: int = 19,
) -> str:
    """Return rubric clip_mode for evening prime slot (4/week) or 'scene' for daytime slots."""
    if now_local.hour < prime_hour_min:
        return "scene"
    today_set = {str(x).lower() for x in completed_today if x}
    if any(r in today_set for r in RUBRIC_MODES):
        return "scene"

    scheduled = WEEKLY_PRIME_SCHEDULE.get(now_local.weekday())
    if scheduled and scheduled not in today_set:
        return scheduled
    return "scene"


async def pick_rubric_media(db: AsyncSession, rubric: str) -> Optional[dict[str, Any]]:
    """Select an unpublished-to-SMM published movie matching the requested editorial rubric."""
    norm = (rubric or "").strip().lower()
    used_ids = select(SmmClipJobModel.media_id).where(
        SmmClipJobModel.media_type == "movie",
        SmmClipJobModel.media_id.isnot(None),
    )
    used_codes = select(SmmClipJobModel.movie_code)
    has_storage = exists(
        select(MovieTranslationModel.id).where(
            MovieTranslationModel.movie_id == MovieModel.id,
            MovieTranslationModel.storage_channel_message_id.isnot(None),
        )
    )
    filters = [
        MovieModel.publish_status == "published",
        has_storage,
        MovieModel.id.notin_(used_ids),
        func.coalesce(MovieModel.short_code, MovieModel.code).notin_(used_codes),
        MovieModel.code.notin_(used_codes),
    ]
    if norm in ("bilasizmi", "kadr_ortida", "tavsiya"):
        filters.append(or_(MovieModel.imdb_rating.is_(None), MovieModel.imdb_rating >= 6.8))
    if norm in ("bilasizmi", "kadr_ortida"):
        filters.append(MovieModel.tmdb_id.isnot(None))

    if norm == "yangiliklar":
        order = (MovieModel.release_year.isnot(None).desc(), func.coalesce(MovieModel.release_year, 0).desc(), MovieModel.id.desc())
    else:
        order = (
            MovieModel.release_year.isnot(None).desc(),
            func.coalesce(MovieModel.imdb_rating, 0.0).desc(),
            func.coalesce(MovieModel.release_year, 0).desc(),
            MovieModel.id.desc(),
        )

    movie = (await db.execute(select(MovieModel).where(*filters).order_by(*order).limit(1))).scalar_one_or_none()
    if not movie:
        return None
    pick_code = (getattr(movie, "short_code", None) or movie.code or "").strip()
    if not pick_code:
        return None
    return {
        "media_type": "movie",
        "media_id": movie.id,
        "movie_code": pick_code,
        "title": movie.title,
        "release_year": movie.release_year,
        "imdb_rating": movie.imdb_rating,
        "director": movie.director,
        "description": movie.description,
        "genres": movie.genres,
        "tmdb_id": movie.tmdb_id,
        "trailer_url": getattr(movie, "trailer_url", None),
        "poster_url": getattr(movie, "poster_url", None),
        "backdrop_url": getattr(movie, "backdrop_url", None),
    }
