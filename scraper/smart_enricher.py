import os
import sys
import re
import json
import logging
from typing import Optional, Dict, Any, List
import httpx
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))

from app.core.config import settings
from app.infrastructure.external.tmdb_client import tmdb_client
from app.infrastructure.external.translator import translator_service, GEMINI_MODELS
from app.infrastructure.external.genre_mapper import map_tmdb_genres
from app.infrastructure.db.session import async_session_factory
from sqlalchemy import select
from app.infrastructure.db.models.category import CategoryModel

logger = logging.getLogger(__name__)


async def get_all_categories_map() -> Dict[str, int]:
    """Bazadagi barcha kategoriyalarni nom -> id shaklida qaytaradi."""
    cat_map = {}
    try:
        async with async_session_factory() as session:
            stmt = select(CategoryModel.id, CategoryModel.name)
            res = await session.execute(stmt)
            for cid, cname in res.all():
                cat_map[cname.strip().lower()] = cid
    except Exception as e:
        logger.warning(f"Kategoriyalarni olishda xatolik: {e}")
    return cat_map


async def gemini_identify_movie(
    raw_title: str,
    year_hint: Optional[int] = None,
    caption: Optional[str] = None,
    media_type: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Gemini AI orqali film/serialning original nomi, yili va to'liq detallarini aniqlaydi."""
    api_key = (settings.GEMINI_API_KEY or "").strip()
    if not api_key:
        return None

    type_hint_str = "Bu ko'p qismli serial yoki dorama." if media_type == "series" else "Bu film yoki serial."
    default_type = "series" if media_type == "series" else "movie"

    prompt = f"""
Senga o'zbek tilidagi film yoki serial nomi va qo'shimcha ma'lumot (caption/tavsif) beriladi. {type_hint_str}
QAT'IY QOIDALAR:
1. Agar qo'shimcha matnda (caption) haqiqiy syujet/tavsif yozilgan bo'lsa, uni O'ZGARTIRMA! Filmni boshqa mashhur Gollivud kinosi (masalan: Bad Boys, Agent X, Under Paris) deb o'ylab xato qilib yuborma!
2. Agar davlat (masalan: Qozog'iston, Hindiston, Rossiya, O'zbekiston, Ispaniya) ko'rsatilgan bo'lsa, o'sha davlat kinosi deb tahlil qil.
3. Agar filmning original xorijiy nomi 100% aniq bo'lmasa, taxminiy noto'g'ri nom to'qish o'rniga original_title ni null qil yoki o'zbekcha nomini qoldir.
4. "description" maydoniga albatta berilgan filmning HAQIQIY syujetini o'zbek tilida to'liq va ravon yoz.

Film/Serial nomi: '{raw_title}'
Yil taxmini: {year_hint or 'Noma\'lum'}
Qo'shimcha matn/caption:
{caption or 'Mavjud emas'}

Faqat va faqat quyidagi JSON formatida javob ber:
```json
{{
  "clean_uz_title": "Toza O'zbekcha Nomi",
  "original_title": null,
  "search_title_en": null,
  "search_title_ru": null,
  "media_type": "{default_type}",
  "release_year": {year_hint or 2024},
  "description": "Berilgan haqiqiy kino syujetiga asoslangan o'zbekcha qiziqarli tavsif...",
  "genres": ["Janr 1", "Janr 2"],
  "director": "Rejissyor ismi",
  "cast": "Aktyorlar",
  "runtime": 100,
  "imdb_rating": 6.5,
  "trailer_query": null
}}
```
"""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1}
    }

    for model in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                    json_m = re.search(r"\{.*\}", text, re.DOTALL)
                    if json_m:
                        return json.loads(json_m.group(0))
        except Exception as e:
            logger.warning(f"Gemini {model} identify error: {e}")

    return None


def clean_movie_title(raw_title: str) -> str:
    """Film nomidagi barcha ortiqcha SEO, reklama, qavslar va markdown simvollarni tozalaydi."""
    if not raw_title:
        return ""
    # 1. Markdown va maxsus belgilarni tozalash (*, _, ~, `, #)
    t = re.sub(r'[*_~`#]', '', raw_title)
    
    # 2. Qavslar ichidagi yozuvlarni tozalash [ ... ] va ( ... )
    t = re.sub(r'\[.*?\]', '', t)
    t = re.sub(r'\(.*?\)', '', t)
    
    # 3. Ajratuvchilar bo'yicha faqat birinchi asosiy qismini olish ( / yoki | )
    t = re.split(r'\s*[|/]\s*', t)[0]
    
    # 4. Uzbek saytlari va botlaridagi SEO/reklama iboralari
    noise_patterns = [
        r'\bpremyera\b', r'\bprimyera\b',
        r'\byangi\s+(?:premyera|primyera|kino|film|serial|mavsum|qism)\b',
        r"\b(?:o['\"`‘’]?zbek|uzbek)\s+tilida\b",
        r"\b(?:o['\"`‘’]?zbekcha|uzbekcha)\b",
        r'\btarjima\s+kino\b', r'\btarjima\s+film\b', r'\btarjima\b',
        r'\bfull\s*hd\b', r'\bhd\b', r'\b4k\b', r'\b1080p\b', r'\b720p\b', r'\b480p\b',
        r'\btas-?ix\b', r'\bskachat\b', r'\byuklab\s+olish\b',
        r'\b(?:koreys|xitoy|turk|hind|rus|aqsh|eron)\s+(?:jangari\s+)?(?:filmi|kino|seriali)\b',
        r'\b(?:badiiy|hujjatli|jangari|qiziqarli)\s+(?:filmi|kino)\b',
        r'\b(?:tarjima\s+)?filmi\b',
        r'\b(19\d{2}|20\d{2})\b',
        r'\bbarcha\s+qismlar\b', r'\bqism\b', r'\bseriya\b'
    ]
    for p in noise_patterns:
        t = re.sub(p, '', t, flags=re.IGNORECASE)
        
    t = re.sub(r'\s+', ' ', t).strip(' -–—:,')
    return t or raw_title.strip()


def clean_synopsis_text(raw_text: Optional[str], fallback_title: str = "", media_type: str = "movie") -> str:
    """
    Telegram botlaridagi barcha ortiqcha axlatlarni tozalaydi:
    - Emojilar va sarlavhalar (🎬, ➖➖, Davlat:, Til:, IMDb:, Janr:, Sifat:, Kino kodi:, Bot orqali:)
    - Pastki tugma va menyu yozuvlari (1-fasl qismni tanlang, Sifatni tanlang, t.me/, kanalimiz)
    - Ruscha takroriy matnlar (Uzbek matnidan keyin ruscha kelgan qismlarni qirqib tashlaydi)
    - Markdown simvollari (**, __, `, ~)
    Natijada faqat sof o'zbek tilidagi chiroyli tavsif qoladi.
    """
    if not raw_text or not str(raw_text).strip():
        return f"🍿 {fallback_title} {'seriali' if media_type == 'series' else 'kinofilmi'} o'zbek tilida."

    lines = str(raw_text).strip().split("\n")
    cleaned_lines = []
    
    header_keywords = [
        "davlat:", "til:", "yil:", "imdb:", "janr:", "sifat:", "davomiyligi:",
        "kino kodi:", "film kodi:", "kod:", "bot orqali", "premyera!", "premyera",
        "yuklangan:", "ovoz beruvchilar:", "format:", "barcha qismlar", "rejissyor:"
    ]
    footer_keywords = [
        "qismni tanlang", "sifatni tanlang", "kino videosi", "yuklanmoqda",
        "kanalimiz", "botimiz", "do'stlarga ulashing", "t.me/", "fasl", "qism"
    ]

    for line in lines:
        l_str = line.strip()
        if not l_str:
            continue
        
        # Ajratuvchi chiziqlar (➖➖, – –, ---, ===)
        if re.search(r'[\u2796\u2500\u2014\u2013\-_*=]{3,}', l_str):
            continue

        # Sarlavha yoki ost-sarlavha qatorlari (__Original Title__, **Title**)
        if re.match(r'^(__|\*\*).+(__|\*\*)$', l_str) and len(l_str) < 60:
            continue
        
        lower = l_str.lower()
        if any(lower.startswith(emoji) for emoji in ["🎬", "🌐", "🎙", "📅", "⭐", "🎭", "⏱", "🆔", "📥", "📺", "📀", "💿", "🗣", "🎞", "🖥", "🔥", "👇", "👉", "⬇️"]):
            continue
        if any(hk in lower for hk in header_keywords if len(lower) < 100):
            continue
        if any(fk in lower for fk in footer_keywords if len(lower) < 100):
            continue

        cleaned_lines.append(l_str)

    synopsis = " ".join(cleaned_lines).strip()
    synopsis = re.sub(r'[*_~`#]', '', synopsis)

    # Ruscha qismini ajratib qirqish (odatda o'zbekcha matndan keyin ruscha matn takrorlanadi)
    cyrillic_match = re.search(r'([А-Яа-яЁё]{4,})', synopsis)
    if cyrillic_match:
        start_pos = cyrillic_match.start()
        latin_prefix = synopsis[:start_pos].strip()
        if len(latin_prefix) > 30:
            synopsis = latin_prefix.rstrip(' .–—,;:') + "."

    synopsis = re.sub(r'\s+', ' ', synopsis).strip()
    if len(synopsis) < 25:
        return f"🍿 {fallback_title} {'seriali' if media_type == 'series' else 'kinofilmi'} o'zbek tilida."

    return synopsis


def normalize_title_tokens(t: Optional[str]) -> set:
    if not t:
        return set()
    t = t.lower()
    t = re.sub(r'[^\w\s]', ' ', t)
    stop_words = {'the', 'a', 'an', 'and', 'of', 'in', 'on', 'at', 'to', 'for', 'va', 'kino', 'film', 'uzbek', 'tilida', 'hd', 'rus'}
    return {w for w in t.split() if len(w) >= 2 and w not in stop_words}


def is_valid_tmdb_match(
    candidate: Dict[str, Any],
    query: str,
    target_year: Optional[int] = None,
    expected_original_title: Optional[str] = None
) -> bool:
    cand_title = candidate.get("title") or candidate.get("name") or ""
    cand_orig = candidate.get("original_title") or candidate.get("original_name") or ""
    cand_year = candidate.get("release_year") or candidate.get("year")

    # 1. Year check: If target_year is known, difference must not exceed 2 years.
    # (Prevents 1924 silent films from matching 2024 films!)
    if target_year and cand_year:
        try:
            if abs(int(cand_year) - int(target_year)) > 2:
                return False
        except (ValueError, TypeError):
            pass

    # 2. Title similarity check
    query_tokens = normalize_title_tokens(query)
    orig_tokens = normalize_title_tokens(expected_original_title)
    cand_tokens = normalize_title_tokens(cand_title) | normalize_title_tokens(cand_orig)

    if not cand_tokens:
        return False

    for target_set in [orig_tokens, query_tokens]:
        if not target_set:
            continue
        overlap = target_set.intersection(cand_tokens)
        if len(overlap) / len(target_set) >= 0.5:
            return True

    # Exact or substring check on compact strings (min 4 chars)
    q_clean = re.sub(r'[^\w]', '', query.lower())
    orig_clean = re.sub(r'[^\w]', '', (expected_original_title or '').lower())
    c_clean = re.sub(r'[^\w]', '', cand_title.lower())
    co_clean = re.sub(r'[^\w]', '', cand_orig.lower())

    for t in [q_clean, orig_clean]:
        if len(t) >= 4:
            if t in c_clean or t in co_clean or c_clean in t or co_clean in t:
                return True

    return False


async def enrich_movie_smart(
    raw_title: str,
    year: Optional[int] = None,
    source_poster: Optional[str] = None,
    source_desc: Optional[str] = None,
    source_genres: Optional[str] = None,
    caption: Optional[str] = None,
    media_type: str = "movie",
    item_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    AI (Gemini) + TMDb orqali film/serialni to'liq ma'lumotlar, poster, treyler,
    rejissyor, aktyorlar va kategoriyalar bilan to'ldirish.
    Xatolik va begona kinolarga almashtirilib ketishining oldi olingan.
    """
    clean_title = clean_movie_title(raw_title)

    # Normalize source_poster URL
    if source_poster and source_poster.startswith("/"):
        source_poster = f"https://asilmedia.org{source_poster}"
    if source_poster and not source_poster.startswith("http"):
        source_poster = None

    detected_type = "series" if (media_type == "series" or any(w in raw_title.lower() for w in ["serial", "dorama", "mavsum"])) else "movie"

    # Default description: if source_desc or caption contains full synopsis, clean it!
    clean_default_desc = ""
    if source_desc and len(source_desc.strip()) > 30:
        clean_default_desc = clean_synopsis_text(source_desc, clean_title, detected_type)
    elif caption and len(caption.strip()) > 30:
        clean_default_desc = clean_synopsis_text(caption, clean_title, detected_type)
    else:
        clean_default_desc = f"🍿 {clean_title} {'seriali' if detected_type == 'series' else 'kinofilmi'} o'zbek tilida."

    metadata: Dict[str, Any] = {
        "title": clean_title or raw_title,
        "original_title": None,
        "description": clean_default_desc,
        "poster_url": source_poster,
        "trailer_url": None,
        "release_year": year,
        "imdb_rating": None,
        "tmdb_rating": None,
        "tmdb_id": None,
        "genres": source_genres or ("Serial" if detected_type == "series" else "Tarjima kino"),
        "cast": None,
        "director": None,
        "runtime": 120,
        "category_ids": [],
        "source_used": "source",
        "media_type": detected_type
    }

    # Kategoriyalar xaritasi
    cat_map = await get_all_categories_map()
    matched_cat_names = set()

    # 1. Gemini orqali kinoni tanib olish
    ai_info = await gemini_identify_movie(raw_title=clean_title, year_hint=year, caption=caption or source_desc, media_type=detected_type)
    if ai_info:
        logger.info(f"🤖 Gemini tahlili: '{ai_info.get('search_title_en') or ai_info.get('clean_uz_title')}' ({ai_info.get('release_year')})")
        if ai_info.get("clean_uz_title"):
            clean_ai = ai_info["clean_uz_title"].strip()
            if clean_ai:
                metadata["title"] = clean_ai
        if ai_info.get("original_title"):
            metadata["original_title"] = ai_info["original_title"]
        if ai_info.get("release_year") and not year:
            metadata["release_year"] = ai_info["release_year"]
        if ai_info.get("description") and len(ai_info["description"].strip()) > 20:
            cleaned_ai_desc = clean_synopsis_text(ai_info["description"], clean_title, detected_type)
            if cleaned_ai_desc and not cleaned_ai_desc.startswith("🍿"):
                metadata["description"] = cleaned_ai_desc
        if ai_info.get("genres"):
            metadata["genres"] = ", ".join(ai_info["genres"])
            for g in ai_info["genres"]:
                matched_cat_names.add(g.strip().lower())
        if ai_info.get("director"):
            metadata["director"] = ai_info["director"]
        if ai_info.get("cast"):
            metadata["cast"] = ai_info["cast"]
        if ai_info.get("runtime"):
            metadata["runtime"] = ai_info["runtime"]
        if ai_info.get("imdb_rating"):
            metadata["imdb_rating"] = float(ai_info["imdb_rating"])
        if ai_info.get("media_type"):
            metadata["media_type"] = "series" if "series" in ai_info["media_type"] or "tv" in ai_info["media_type"] else "movie"

    # 2. TMDb qidiruv ro'yxatini shakllantirish
    default_tmdb_type = "tv" if metadata["media_type"] == "series" else "movie"
    search_queries = []
    if ai_info and ai_info.get("search_title_en"):
        search_queries.append((ai_info["search_title_en"], default_tmdb_type))
    if ai_info and ai_info.get("search_title_ru"):
        search_queries.append((ai_info["search_title_ru"], default_tmdb_type))
    if clean_title not in [q[0] for q in search_queries]:
        search_queries.append((clean_title, default_tmdb_type))

    matched_tmdb = None
    target_year = metadata["release_year"] or year
    expected_orig = ai_info.get("original_title") if ai_info else None

    for query, ctype in search_queries:
        if not query or len(query.strip()) < 2:
            continue
        for search_type in [ctype, "movie" if ctype == "tv" else "tv"]:
            try:
                results = await tmdb_client.search(query=query, content_type=search_type)
                if results:
                    for res in results:
                        if is_valid_tmdb_match(candidate=res, query=query, target_year=target_year, expected_original_title=expected_orig):
                            matched_tmdb = res
                            break
            except Exception as e:
                logger.warning(f"TMDb search error query '{query}' ({search_type}): {e}")
            if matched_tmdb:
                break
        if matched_tmdb:
            break

    # 3. TMDb tafsilotlarini yuklash (Faqatgina 100% mos kelgandagina!)
    if matched_tmdb and matched_tmdb.get("id"):
        tmdb_id = matched_tmdb["id"]
        tmdb_type = matched_tmdb.get("content_type", "movie")
        try:
            details = await tmdb_client.get_details(tmdb_id=tmdb_id, content_type=tmdb_type)
            if details:
                metadata["tmdb_id"] = tmdb_id
                # TMDb posteri faqat mavjud bo'lsa olinadi, lekin source_poster bor bo'lsa uni yo'qotmaymiz
                if details.get("poster_url"):
                    metadata["poster_url"] = details["poster_url"]
                metadata["trailer_url"] = details.get("trailer_url") or metadata["trailer_url"]
                metadata["release_year"] = details.get("release_year") or metadata["release_year"]
                metadata["runtime"] = details.get("runtime") or metadata["runtime"]
                metadata["tmdb_rating"] = details.get("tmdb_rating")
                if details.get("imdb_rating"):
                    metadata["imdb_rating"] = details["imdb_rating"]
                elif details.get("vote_average") and not metadata["imdb_rating"]:
                    metadata["imdb_rating"] = round(details["vote_average"], 1)

                if details.get("director") and not metadata["director"]:
                    metadata["director"] = details["director"]
                if details.get("cast") and not metadata["cast"]:
                    metadata["cast"] = details["cast"]

                # Janrlar
                tmdb_uz_genres = map_tmdb_genres(details.get("genres_raw", []))
                if tmdb_uz_genres:
                    metadata["genres"] = ", ".join(tmdb_uz_genres)
                    for g in tmdb_uz_genres:
                        matched_cat_names.add(g.strip().lower())

                # Tavsifni o'zbekchaga tarjima qilish (faqat tavsif juda qisqa bo'lsa yoki shablon bo'lsa)
                if not metadata.get("description") or len(metadata["description"]) < 50 or metadata["description"].startswith("🍿"):
                    raw_overview = details.get("overview") or ""
                    if raw_overview:
                        trans_desc, _ = await translator_service.translate_to_uzbek(raw_overview)
                        if trans_desc:
                            metadata["description"] = clean_synopsis_text(trans_desc, clean_title, detected_type)

                metadata["source_used"] = "tmdb"
                logger.info(f"✅ TMDb tasdiqlangan ma'lumot berdi (ID: {tmdb_id}, Poster: {metadata['poster_url']})")
        except Exception as e:
            logger.warning(f"TMDb get_details error: {e}")
    else:
        logger.info("ℹ️ TMDb dan to'g'ri keluvchi kino topilmadi. Sayt/botning asl ma'lumotlari va posteri saqlanadi.")

    # 4. Agar poster topilmagan bo'lsa va item_url mavjud bo'lsa, saytdagi og:image ni olamiz
    if not metadata["poster_url"] and item_url:
        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                resp = await client.get(item_url, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    og_m = re.search(r'property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', resp.text)
                    if not og_m:
                        og_m = re.search(r'content=["\']([^"\']+)["\']\s+property=["\']og:image["\']', resp.text)
                    if og_m and og_m.group(1).startswith("http"):
                        metadata["poster_url"] = og_m.group(1)
                        logger.info(f"✅ Saytdan og:image posteri muvaffaqiyatli olindi: {metadata['poster_url']}")
        except Exception as e:
            logger.debug(f"Saytdan og:image olishda xatolik: {e}")

    # Treyler topilmagan bo'lsa, YouTube qidiruv linki
    if not metadata["trailer_url"] and ai_info and ai_info.get("trailer_query"):
        import urllib.parse
        q = urllib.parse.quote_plus(ai_info["trailer_query"])
        metadata["trailer_url"] = f"https://www.youtube.com/results?search_query={q}"

    # Kategoriyalarni ID lar bilan boyitish
    final_cat_ids = []
    for gname in matched_cat_names:
        if gname in cat_map:
            final_cat_ids.append(cat_map[gname])
    metadata["category_ids"] = list(set(final_cat_ids))

    # Poster URL sini tekshirish va to'liq HTTPS qilib formatlash
    if metadata.get("poster_url"):
        p = str(metadata["poster_url"]).strip()
        if p.startswith("//"):
            metadata["poster_url"] = f"https:{p}"
        elif p.startswith("/"):
            metadata["poster_url"] = f"https://asilmedia.org{p}"

    # Yakuniy tavsifni to'liq tozalash va standartlashtirish
    metadata["description"] = clean_synopsis_text(metadata.get("description", ""), clean_title, detected_type)

    return metadata


if __name__ == "__main__":
    import asyncio
    async def main():
        res = await enrich_movie_smart(
            raw_title="Deraza qarshisidagi ayol",
            caption="🎬 Deraza qarshisidagi ayol [Primyera O'zbek tilida]\n– – – – – – – – – – – – – – –\n💿 Sifat: mavjud emas\n⭐ IMDb: 0/10\n🗣 Til: O’zbek | 📅 Yil: kiritilmagan\n🎭 Janr: kiritilmagan\n🎞 Film kodi: 15"
        )
        print("\n=== YAKUNIY BOYITILGAN NATIJA ===")
        print(json.dumps(res, indent=2, ensure_ascii=False))

    asyncio.run(main())
