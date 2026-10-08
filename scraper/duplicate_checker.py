"""
Duplicate Checker for Kinochi Scraper & Grabber.
Directly connects to PostgreSQL (Neon DB) to detect existing movies and series,
preventing duplicate downloads, duplicate topic creation, and duplicate indexing.
"""

import re
import time
import logging
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
import asyncpg

from .config import DATABASE_URL

logger = logging.getLogger(__name__)

# List of common Uzbek noise words and phrases to strip for clean comparison
NOISE_PATTERNS = [
    r'\b(?:premyera|premyera\s*\d{4})\b',
    r'\b(?:uzbek|o[\'ʻ`’]zbek|ozbek)\s*tilida\b',
    r'\b(?:tarjima|tarjima\s*kino|tarjima\s*film|tarjima\s*serial)\b',
    r'\b(?:koreys|hind|turk|xitoy|rus|amerika)\s*(?:filmi|kino|seriali)\b',
    r'\b(?:barcha\s*qismlar|barcha\s*fasllar)\b',
    r'\b(?:onlayn\s*ko[\'ʻ`’]rish|onlayn\s*korish)\b',
    r'\b(?:hd\s*formatda|full\s*hd|1080p|720p|480p)\b',
    r'\b(?:treyler|trailer)\b',
    r'\b(?:multfilm|multik|multfilmi)\b',
    r'\b(?:kino|film|serial)\b',
]

def normalize_uzbek_text(text: Optional[str]) -> str:
    """
    O'zbekcha matnni solishtirish uchun normalizatsiya qiladi:
    - Kichik harflarga o'tkazadi
    - Barcha apostrof turlarini (', ʻ, ’, `, ´) birxillashtiradi yoki olib tashlaydi
    - Belgilar, tinish belgilari va ortiqcha so'zlarni tozalaydi
    """
    if not text:
        return ""
    
    t = text.lower().strip()
    
    # Apostroflarni standartlashtirish
    t = re.sub(r'[\u02bb\u02bc\u2018\u2019\u0060\u00b4\']', "'", t)
    
    # Shovqin iboralarni tozalash
    for pat in NOISE_PATTERNS:
        t = re.sub(pat, " ", t, flags=re.IGNORECASE)
        
    # Tinish belgilari va keraksiz belgilarni bo'shliq bilan almashtirish
    t = re.sub(r'[\.,:;!\?_\-\[\]\(\)\{\}\"\'\\\/~@#\$%\^&\*\+=]', " ", t)
    
    # Ortiqcha bo'shliqlarni qisqartirish
    t = re.sub(r'\s+', " ", t).strip()
    return t

def to_slug(text: Optional[str]) -> str:
    """
    Faqat harf va raqamlarni qoldiradi (barcha bo'shliq va belgilarsiz).
    Masalan: "O'rgimchak-Odam" -> "orgimchakodam"
    x va h harflari o'zbek tilida tez-tez adashtirilgani sababli birxillashtiriladi:
    "Ruxshunos" -> "ruhshunos", "Ruhshunos" -> "ruhshunos"
    (sh va ch harf birikmalari buzilmaydi)
    """
    if not text:
        return ""
    norm = normalize_uzbek_text(text)
    norm = re.sub(r'(?<![sc])x', 'h', norm)
    return re.sub(r'[^a-z0-9]', '', norm)

def extract_title_variants(raw_title: str) -> List[str]:
    """
    Sarlavhadan bir nechta variantlarni ajratib oladi:
    Masalan:
    'Odisseya / Odisey' -> ['Odisseya', 'Odisey', 'Odisseya / Odisey']
    'Shelbilar oilasi (Peaky Blinders)' -> ['Shelbilar oilasi', 'Peaky Blinders']
    'Akulalar orasida / Qo\'rquv changalida' -> ['Akulalar orasida', 'Qo\'rquv changalida']
    'Ruxshunos' -> ['Ruxshunos', 'Ruhshunos']
    """
    variants = set()
    cleaned_raw = raw_title.strip()
    variants.add(cleaned_raw)

    # x va h harflarini almashtirish varianti (sh va ch digraphlariga tegmasdan)
    if 'x' in cleaned_raw.lower() or 'h' in cleaned_raw.lower():
        v_h = re.sub(r'(?<![scSC])[xX]', lambda m: 'H' if m.group(0).isupper() else 'h', cleaned_raw)
        v_x = re.sub(r'(?<![scSC])[hH]', lambda m: 'X' if m.group(0).isupper() else 'x', cleaned_raw)
        variants.add(v_h)
        variants.add(v_x)

    try:
        from scraper.title_cleaner import clean_scraped_title
        smart_clean = clean_scraped_title(raw_title)
        if smart_clean.get("title"):
            variants.add(smart_clean["title"])
            if 'x' in smart_clean["title"].lower() or 'h' in smart_clean["title"].lower():
                variants.add(smart_clean["title"].replace('x', 'h').replace('X', 'H'))
                variants.add(smart_clean["title"].replace('h', 'x').replace('H', 'X'))
        for v in smart_clean.get("variants", []):
            if v and len(v) >= 2:
                variants.add(v)
    except Exception:
        pass
    
    # Qavs ichidagi nomni ajratib olish (masalan, original nom)
    bracket_match = re.findall(r'\((.*?)\)', cleaned_raw)
    for b in bracket_match:
        b_clean = b.strip()
        # Agar qism/mavsum ko'rsatkichi bo'lmasa
        if not re.search(r'\b(?:\d+[\s\-_]*(?:qism|seriya|mavsum))\b', b_clean, re.I):
            variants.add(b_clean)
            
    # Qavssiz qism
    without_brackets = re.sub(r'\(.*?\)', ' ', cleaned_raw).strip()
    if without_brackets:
        variants.add(without_brackets)
        
    # / yoki | bo'yicha bo'lish
    for part in re.split(r'[/|]', cleaned_raw):
        part_clean = part.strip()
        if part_clean:
            variants.add(part_clean)

    # Ko'p tilli aralash sarlavhalar uchun birinchi 1-2 so'zni variant qilish (masalan "Yengilmas Nepobedimyj Invincible" -> "Yengilmas")
    words = [w for w in cleaned_raw.split() if len(w) >= 2]
    if words:
        variants.add(words[0])
        if len(words) >= 2:
            variants.add(f"{words[0]} {words[1]}")
            
    return [v for v in variants if len(v) >= 2]


def extract_part_number(title: Optional[str]) -> Optional[int]:
    """
    Filmlardagi qism raqamini aniqlaydi (masalan: 'Karib dengizi 2', 'Forsaj 5', 'Terminator 3', '2-qism', 'Part 2').
    """
    if not title:
        return None
    t = str(title).lower().strip()
    # 1. '2-qism', '3 qism', 'qism 4', 'part 2', 'chast 3'
    m_part = re.search(r'\b(?:qism|part|chast)\s*[-_]?\s*(\d+)\b', t)
    if m_part:
        return int(m_part.group(1))
    m_part2 = re.search(r'\b(\d+)\s*[-_]?\s*(?:qism|part|chast)\b', t)
    if m_part2:
        return int(m_part2.group(1))

    # 2. Rim raqamlari (I, II, III, IV, V, VI, VII, VIII)
    roman_map = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6, 'vii': 7, 'viii': 8}
    for rom, val in sorted(roman_map.items(), key=lambda x: -len(x[0])):
        if re.search(rf'\b{rom}\b', t):
            return val

    # 3. Yakka raqam: masalan 'Karib dengizi qaroqchilari 2', 'Shrek 4', 'Forsaj 9'
    m_num = re.search(r'\b([1-9]|1[0-5])\b', t)
    if m_num:
        val = int(m_num.group(1))
        if not re.search(r'\b(?:3d|4k|1080p|720p)\b', t):
            return val
    return None


@dataclass
class DuplicateCheckResult:
    is_duplicate: bool
    match_type: str = "none"  # "exact_slug", "title_variant", "original_title", "token_overlap", "none"
    matched_id: Optional[int] = None
    matched_title: Optional[str] = None
    matched_year: Optional[int] = None
    matched_type: Optional[str] = None  # "movie" or "series"
    matched_code: Optional[str] = None
    reason: str = ""


class DuplicateChecker:
    """
    PostgreSQL bazasiga ulanib filmlar va seriallar dublikatini tekshiruvchi sinf.
    Operativ xotirada tezkor kesh tutadi va bir necha bosqichli aniq filtrlashni amalga oshiradi.
    """
    def __init__(self, db_url: str = DATABASE_URL, cache_ttl: int = 300):
        self.raw_db_url = db_url
        self.db_url = db_url.replace("postgresql+asyncpg://", "postgresql://") if db_url else ""
        self.cache_ttl = cache_ttl
        self._last_cache_time = 0.0
        
        # Keshlangan ma'lumotlar
        self._movies: List[Dict[str, Any]] = []
        self._series: List[Dict[str, Any]] = []
        
        # Tezkor qidiruv xaritalari (slug -> item)
        self._movie_slug_map: Dict[str, Dict[str, Any]] = {}
        self._series_slug_map: Dict[str, Dict[str, Any]] = {}

    async def get_connection(self) -> Optional[asyncpg.Connection]:
        if not self.db_url:
            logger.warning("[DUPLICATE_CHECKER] DATABASE_URL sozlanmagan!")
            return None
        try:
            return await asyncpg.connect(self.db_url)
        except Exception as e:
            logger.error(f"[DUPLICATE_CHECKER] Bazaga ulanishda xatolik: {e}")
            return None

    async def refresh_cache(self, force: bool = False):
        """
        Bazadagi mavjud barcha kino va seriallar ro'yxatini xotiraga yuklaydi.
        """
        now = time.time()
        if not force and (now - self._last_cache_time < self.cache_ttl) and self._movies:
            return  # Kesh hali yangi

        conn = await self.get_connection()
        if not conn:
            return

        try:
            raw_movies = await conn.fetch(
                """
                SELECT m.id, m.title, m.original_title, m.release_year, m.code, m.tmdb_id 
                FROM movies m
                """
            )
            raw_series = await conn.fetch(
                """
                SELECT s.id, s.title, s.release_year, s.tmdb_id 
                FROM series s
                """
            )

            self._movies = []
            self._movie_slug_map = {}
            for m in raw_movies:
                m_dict = dict(m)
                m_dict["type"] = "movie"
                slug = to_slug(m_dict["title"])
                m_dict["slug"] = slug
                m_dict["variants_slugs"] = [to_slug(v) for v in extract_title_variants(m_dict["title"])]
                if m_dict.get("original_title"):
                    m_dict["orig_slug"] = to_slug(m_dict["original_title"])
                
                self._movies.append(m_dict)
                if slug:
                    self._movie_slug_map[slug] = m_dict

            self._series = []
            self._series_slug_map = {}
            for s in raw_series:
                s_dict = dict(s)
                s_dict["type"] = "series"
                slug = to_slug(s_dict["title"])
                s_dict["slug"] = slug
                s_dict["variants_slugs"] = [to_slug(v) for v in extract_title_variants(s_dict["title"])]
                
                self._series.append(s_dict)
                if slug:
                    self._series_slug_map[slug] = s_dict

            self._last_cache_time = now
            logger.info(
                f"[DUPLICATE_CHECKER] Kesh yangilandi: {len(self._movies)} filmlar, {len(self._series)} seriallar."
            )
        except Exception as e:
            logger.error(f"[DUPLICATE_CHECKER] Keshni yuklashda xatolik: {e}")
        finally:
            await conn.close()

    async def check(
        self,
        title: str,
        year: Optional[int] = None,
        original_title: Optional[str] = None,
        media_type: Optional[str] = None,
        tmdb_id: Optional[int] = None,
        **kwargs
    ) -> DuplicateCheckResult:
        """
        Berilgan kino yoki serial bazada mavjudligini tekshiradi.
        """
        await self.refresh_cache()

        if not self._movies and not self._series:
            # Agar kesh bo'sh bo'lsa (masalan baza ulanmagan bo'lsa)
            return DuplicateCheckResult(is_duplicate=False)

        candidate_variants = extract_title_variants(title)
        candidate_slugs = [to_slug(v) for v in candidate_variants if to_slug(v)]
        cand_orig_slug = to_slug(original_title) if original_title else ""

        # Qaysi ro'yxatlarni tekshiramiz?
        db_items: List[Dict[str, Any]] = []
        if media_type == "movie":
            db_items = self._movies
        elif media_type == "series":
            db_items = self._series
        else:
            db_items = self._movies + self._series

        cand_part = extract_part_number(title)

        # ── 0. TMDb ID bo'yicha tekshirish (100% aniq moslik) ──
        if tmdb_id:
            try:
                target_tmdb = int(tmdb_id)
                for item in db_items:
                    db_tmdb = item.get("tmdb_id")
                    if db_tmdb and int(db_tmdb) == target_tmdb:
                        return DuplicateCheckResult(
                            is_duplicate=True,
                            match_type="tmdb_id",
                            matched_id=item["id"],
                            matched_title=item["title"],
                            matched_year=item.get("release_year"),
                            matched_type=item["type"],
                            matched_code=item.get("code"),
                            reason=f"TMDb ID to'liq mos keldi (ID: {tmdb_id})"
                        )
            except (ValueError, TypeError):
                pass

        # ── 1. To'g'ridan-to'g'ri Slug bo'yicha tekshirish (Variantlar bilan) ──
        for cand_slug in candidate_slugs:
            for item in db_items:
                db_part = extract_part_number(item.get("title"))
                if cand_part is not None and db_part is not None and cand_part != db_part:
                    continue
                if cand_part is not None and cand_part > 1 and db_part is None:
                    continue

                # Agar itemning asosiy slugi yoki variantlaridan biriga to'liq teng bo'lsa
                is_slug_match = (
                    cand_slug == item.get("slug") or
                    cand_slug in item.get("variants_slugs", [])
                )

                if is_slug_match:
                    # Yil tekshiruvi:
                    db_year = item.get("release_year")
                    if year and db_year:
                        # Yillari 2 yildan ko'p farq qilsa, turli xil film bo'lishi mumkin (masalan 1994 vs 2019)
                        if abs(year - db_year) > 2:
                            continue
                    
                    return DuplicateCheckResult(
                        is_duplicate=True,
                        match_type="exact_slug",
                        matched_id=item["id"],
                        matched_title=item["title"],
                        matched_year=item.get("release_year"),
                        matched_type=item["type"],
                        matched_code=item.get("code"),
                        reason=f"Nomi to'liq mos keldi ('{item['title']}', Yili: {db_year})"
                    )

        # ── 2. Original title (Inglizcha/Ruscha nomi) bo'yicha tekshirish ──
        if cand_orig_slug:
            for item in db_items:
                db_part = extract_part_number(item.get("title"))
                if cand_part is not None and db_part is not None and cand_part != db_part:
                    continue

                db_orig_slug = item.get("orig_slug")
                if db_orig_slug and cand_orig_slug == db_orig_slug:
                    db_year = item.get("release_year")
                    if year and db_year and abs(year - db_year) > 2:
                        continue
                    return DuplicateCheckResult(
                        is_duplicate=True,
                        match_type="original_title",
                        matched_id=item["id"],
                        matched_title=item["title"],
                        matched_year=item.get("release_year"),
                        matched_type=item["type"],
                        matched_code=item.get("code"),
                        reason=f"Original nomi mos keldi ('{item.get('original_title')}')"
                    )

        # ── 3. So'zlar to'plami (Token Overlap) bo'yicha tekshirish ──
        # Agar sarlavha 3 yoki undan ko'p so'zdan iborat bo'lsa
        cand_norm = normalize_uzbek_text(title)
        cand_words = set(w for w in cand_norm.split() if len(w) > 2)

        if len(cand_words) >= 3:
            for item in db_items:
                db_part = extract_part_number(item.get("title"))
                if cand_part is not None and db_part is not None and cand_part != db_part:
                    continue
                if cand_part is not None and cand_part > 1 and db_part is None:
                    continue

                db_norm = normalize_uzbek_text(item["title"])
                db_words = set(w for w in db_norm.split() if len(w) > 2)
                if not db_words:
                    continue

                intersection = cand_words.intersection(db_words)
                overlap_ratio = len(intersection) / max(len(cand_words), len(db_words))

                # 80% dan yuqori moslik va yil bir xil bo'lsa
                if overlap_ratio >= 0.8:
                    db_year = item.get("release_year")
                    if year and db_year and abs(year - db_year) > 2:
                        continue
                    return DuplicateCheckResult(
                        is_duplicate=True,
                        match_type="token_overlap",
                        matched_id=item["id"],
                        matched_title=item["title"],
                        matched_year=db_year,
                        matched_type=item["type"],
                        matched_code=item.get("code"),
                        reason=f"Nomi o'xshash ({int(overlap_ratio * 100)}% mos keldi: '{item['title']}')"
                    )

        # ── 4. Containment / Prefix match (Aralash tilli sarlavhalar uchun) ──
        for item in db_items:
            item_slug = item.get("slug")
            if not item_slug or len(item_slug) < 3:
                continue

            db_part = extract_part_number(item.get("title"))
            if cand_part is not None and db_part is not None and cand_part != db_part:
                continue
            if cand_part is not None and cand_part > 1 and db_part is None:
                continue

            for cand_slug in candidate_slugs:
                if not cand_slug:
                    continue

                # Oxirgi raqamlar mos kelmasa (masalan 1 vs 2)
                if cand_slug[-1:].isdigit() and item_slug[-1:].isdigit() and cand_slug[-1:] != item_slug[-1:]:
                    continue

                is_match = False
                if cand_slug == item_slug:
                    is_match = True
                elif cand_slug.startswith(item_slug) and (len(cand_slug) - len(item_slug) <= 4):
                    is_match = True
                elif item_slug.startswith(cand_slug) and (len(item_slug) - len(cand_slug) <= 4):
                    is_match = True

                if is_match:
                    db_year = item.get("release_year")
                    if year and db_year and abs(year - db_year) > 2:
                        continue
                    return DuplicateCheckResult(
                        is_duplicate=True,
                        match_type="prefix_match",
                        matched_id=item["id"],
                        matched_title=item["title"],
                        matched_year=db_year,
                        matched_type=item["type"],
                        matched_code=item.get("code"),
                        reason=f"Nomi mos keldi ('{item['title']}', Yili: {db_year})"
                    )

        return DuplicateCheckResult(is_duplicate=False)

    async def check_series_episode_exists(
        self,
        series_id: int,
        season_number: int,
        episode_number: int
    ) -> bool:
        """
        Bazada ushbu serialning mavsumi va qismi allaqachon mavjudligini tekshiradi.
        """
        conn = await self.get_connection()
        if not conn:
            return False

        try:
            query = """
                SELECT e.id
                FROM episodes e
                JOIN seasons s ON s.id = e.season_id
                WHERE s.series_id = $1 AND s.season_number = $2 AND e.episode_number = $3
                LIMIT 1
            """
            row = await conn.fetchrow(query, series_id, season_number, episode_number)
            return row is not None
        except Exception as e:
            logger.error(f"[DUPLICATE_CHECKER] Qismni tekshirishda xatolik: {e}")
            return False
        finally:
            await conn.close()
