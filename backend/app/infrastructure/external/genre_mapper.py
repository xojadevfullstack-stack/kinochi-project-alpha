"""
Genre and Category Mapping from TMDb to MediaPlus Uzbek categories.
"""
from typing import Any

# TMDb Genre ID -> (Uzbek Genre Name, Slug/Match Name)
TMDB_GENRE_MAP_UZ: dict[int, dict[str, Any]] = {
    28: {"name_uz": "Jangari", "slug": "action"},
    12: {"name_uz": "Sarguzasht", "slug": "Adventure"},
    16: {"name_uz": "Animatsiya", "slug": "Animation"},
    35: {"name_uz": "Komediya", "slug": "Comedy"},
    80: {"name_uz": "Kriminal", "slug": "Crime"},
    99: {"name_uz": "Hujjatli", "slug": "Documentary"},
    18: {"name_uz": "Drama", "slug": "Drama"},
    10751: {"name_uz": "Oilaviy", "slug": "Family"},
    14: {"name_uz": "Fantastika", "slug": "Fantasy"},
    36: {"name_uz": "Tarixiy", "slug": "Historical"},
    27: {"name_uz": "Dahshatli", "slug": "Horror"},
    10402: {"name_uz": "Musiqiy", "slug": "Musical"},
    9648: {"name_uz": "Sirli", "slug": "Mystery"},
    10749: {"name_uz": "Romantika", "slug": "Romance"},
    878: {"name_uz": "Ilmiy fantastika", "slug": "Science Fiction (Sci-Fi)"},
    53: {"name_uz": "Triller", "slug": "Thriller"},
    10752: {"name_uz": "Urush", "slug": "War"},
    37: {"name_uz": "Vestern", "slug": "Western"},
    # TV Show genres
    10759: {"name_uz": "Jangari", "slug": "action"}, # Action & Adventure
    10762: {"name_uz": "Bolalar uchun", "slug": "Family"}, # Kids
    10763: {"name_uz": "Yangiliklar", "slug": "Documentary"}, # News
    10764: {"name_uz": "Realiti-shou", "slug": "Popular"}, # Reality
    10765: {"name_uz": "Ilmiy fantastika", "slug": "Science Fiction (Sci-Fi)"}, # Sci-Fi & Fantasy
    10766: {"name_uz": "Drama", "slug": "Drama"}, # Soap
    10767: {"name_uz": "Tok-shou", "slug": "Popular"}, # Talk
    10768: {"name_uz": "Urush", "slug": "War"}, # War & Politics
}

# Name fallback in case TMDb ID is not present or name-based
NAME_FALLBACK_MAP: dict[str, str] = {
    "action": "Jangari",
    "adventure": "Sarguzasht",
    "animation": "Animatsiya",
    "anime": "Anime",
    "comedy": "Komediya",
    "crime": "Kriminal",
    "documentary": "Hujjatli",
    "drama": "Drama",
    "family": "Oilaviy",
    "fantasy": "Fantastika",
    "history": "Tarixiy",
    "horror": "Dahshatli",
    "music": "Musiqiy",
    "musical": "Musiqiy",
    "mystery": "Sirli",
    "romance": "Romantika",
    "science fiction": "Ilmiy fantastika",
    "sci-fi": "Ilmiy fantastika",
    "thriller": "Triller",
    "war": "Urush",
    "western": "Vestern",
    "боевик": "Jangari",
    "приключения": "Sarguzasht",
    "мультфильм": "Animatsiya",
    "комедия": "Komediya",
    "криминал": "Kriminal",
    "документальный": "Hujjatli",
    "драма": "Drama",
    "семейный": "Oilaviy",
    "фэнтези": "Fantastika",
    "история": "Tarixiy",
    "ужасы": "Dahshatli",
    "музыка": "Musiqiy",
    "детектив": "Detektiv",
    "мелодрама": "Romantika",
    "фантастика": "Ilmiy fantastika",
    "триллер": "Triller",
    "военный": "Urush",
    "вестерн": "Vestern",
    "erotic": "18+",
    "erotica": "18+",
    "эротика": "18+",
    "adult": "18+",
    "hentai": "18+",
    "хентай": "18+",
    "ecchi": "18+",
    "этти": "18+",
}


def map_tmdb_genres(genres_raw: list[dict[str, Any]]) -> list[str]:
    """
    Takes TMDb raw genres list [{'id': 28, 'name': 'Боевик'}]
    Returns clean list of Uzbek genre names: ['Jangari']
    """
    res = []
    seen = set()
    for g in genres_raw:
        g_id = g.get("id")
        g_name = (g.get("name") or "").strip().lower()
        mapped = None
        if g_id and g_id in TMDB_GENRE_MAP_UZ:
            mapped = TMDB_GENRE_MAP_UZ[g_id]["name_uz"]
        elif g_name in NAME_FALLBACK_MAP:
            mapped = NAME_FALLBACK_MAP[g_name]
        
        if mapped and mapped not in seen:
            seen.add(mapped)
            res.append(mapped)

    return res
