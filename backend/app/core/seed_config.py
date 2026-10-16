"""
TMDb Top Seed Ingestor Configuration & Routing Module (S2).

Ushbu modul barcha konfiguratsion parametrlarni yagona manzil (backend app.core.config.settings)
orqali taqdim etadi va manbalarga yo'naltirish (routing) qoidalarini belgilaydi.
Anime routing: TMDb Animation genre (id 16 yoki nomi 'Animation'/'Мультфильм') + original_language 'ja'
bo'lsa -> AniToob / Animeelar manbalariga, aks holda -> Uzmovi / Asilmedia manbalariga yo'naltiriladi.
"""

from typing import List, Dict, Any, Union
from app.core.config import settings

# Barcha konfiguratsion parametrlar yagona manzil orqali
SEED_MOVIE_TARGET: int = settings.SEED_MOVIE_TARGET
SEED_TV_TARGET: int = settings.SEED_TV_TARGET
SEED_INCLUDE_SERIES: bool = settings.SEED_INCLUDE_SERIES
SEED_MIN_VOTE_COUNT: int = settings.SEED_MIN_VOTE_COUNT
SEED_MIN_RATING: float = settings.SEED_MIN_RATING
SEED_EXCLUDE_ADULT: bool = settings.SEED_EXCLUDE_ADULT
SEED_BATCH_SIZE: int = settings.SEED_BATCH_SIZE
SEED_NOT_FOUND_RETRY_DAYS: int = settings.SEED_NOT_FOUND_RETRY_DAYS
SEED_PRIORITY: int = settings.SEED_PRIORITY
SEED_SEARCH_DELAY_SECONDS: float = settings.SEED_SEARCH_DELAY_SECONDS
SEED_SEARCH_CONCURRENCY: int = settings.SEED_SEARCH_CONCURRENCY


def is_tmdb_anime(
    genres: Union[List[Dict[str, Any]], List[str], List[int], None],
    original_language: str | None
) -> bool:
    """
    TMDb elementi Yaponiya animatsiyasi (Anime) ekanligini aniqlaydi.
    Shart: TMDb Animation janri (id=16 yoki nomi 'Animation'/'Анимация'/'Мультфильм')
    HAMDA original_language == 'ja'.
    """
    if not original_language or str(original_language).strip().lower() != "ja":
        return False

    if not genres:
        return False

    for g in genres:
        if isinstance(g, dict):
            g_id = g.get("id")
            g_name = (g.get("name") or "").lower()
            if g_id == 16 or any(kw in g_name for kw in ("animation", "анимация", "мультфильм")):
                return True
        elif isinstance(g, int):
            if g == 16:
                return True
        elif isinstance(g, str):
            g_str = g.lower()
            if any(kw in g_str for kw in ("16", "animation", "анимация", "мультфильм")):
                return True

    return False


def get_target_sources_for_seed(is_anime: bool) -> List[str]:
    """
    Seed elementi uchun qaysi O'zbek manbalari qidirilishini belgilaydi.
    Anime bo'lsa: ['anitoob', 'animeelar']
    Kino/Serial bo'lsa: ['uzmovi', 'asilmedia']
    """
    if is_anime:
        return ["anitoob", "animeelar"]
    return ["uzmovi", "asilmedia"]
