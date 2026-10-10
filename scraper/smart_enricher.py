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
import urllib.parse

logger = logging.getLogger(__name__)

# Mashhur o'zbekcha tarjima qilingan anime nomlari xaritasi (TMDb / Shikimori uchun)
ANIME_TITLE_MAP: Dict[str, Dict[str, str]] = {
    "meni oyga olib ket": {"en": "Fly Me to the Moon", "orig": "Tonikaku Kawaii", "ru": "Унеси меня на Луну"},
    "iblislar qotili": {"en": "Demon Slayer: Kimetsu no Yaiba", "orig": "Kimetsu no Yaiba", "ru": "Клинок, рассекающий демонов"},
    "qahramon x": {"en": "To Be Hero X", "orig": "To Be Hero X", "ru": "Быть героем Икс"},
    "metal alximik aka uka": {"en": "Fullmetal Alchemist: Brotherhood", "orig": "Hagane no Renkinjutsushi", "ru": "Стальной алхимик"},
    "metal alximik": {"en": "Fullmetal Alchemist", "orig": "Hagane no Renkinjutsushi", "ru": "Стальной алхимик"},
    "kelajak kundaligi": {"en": "The Future Diary", "orig": "Mirai Nikki", "ru": "Дневник будущего"},
    "tabiat farzandi": {"en": "Weathering with You", "orig": "Tenki no Ko", "ru": "Дитя погоды"},
    "arra odam": {"en": "Chainsaw Man", "orig": "Chainsaw Man", "ru": "Человек-бензопила"},
    "qilich sanati online": {"en": "Sword Art Online", "orig": "Sword Art Online", "ru": "Мастера Меча Онлайн"},
    "olim kundaligi": {"en": "Death Note", "orig": "Death Note", "ru": "Тетрадь смерти"},
    "salom dunyo": {"en": "Hello World", "orig": "Hello World", "ru": "Здравствуй, мир"},
    "jodugarlar jangi": {"en": "Jujutsu Kaisen", "orig": "Jujutsu Kaisen", "ru": "Магическая битва"},
    "yetti o'lim gunohlari": {"en": "The Seven Deadly Sins", "orig": "Nanatsu no Taizai", "ru": "Семь смертных грехов"},
    "yetti olim gunohlari": {"en": "The Seven Deadly Sins", "orig": "Nanatsu no Taizai", "ru": "Семь смертных грехов"},
    "yolg'izlikda daraja ko'tarish": {"en": "Solo Leveling", "orig": "Ore dake Level Up na Ken", "ru": "Поднятие уровня в одиночку"},
    "yolgizlikda daraja kotarish": {"en": "Solo Leveling", "orig": "Ore dake Level Up na Ken", "ru": "Поднятие уровня в одиночку"},
    "tungi boyqush kuyi": {"en": "Call of the Night", "orig": "Yofukashi no Uta", "ru": "Песнь ночных сов"},
    "jahannam jannati": {"en": "Hell's Paradise", "orig": "Jigokuraku", "ru": "Адский рай"},
    "mushuk niqobi": {"en": "A Whisker Away", "orig": "Nakitai Watashi wa Neko wo Kaburu", "ru": "Сквозь слёзы я притворяюсь кошкой"},
    "soyada kotarilish": {"en": "The Eminence in Shadow", "orig": "Kage no Jitsuryokusha ni Naritakute!", "ru": "Восхождение в тени!"},
    "yulduz farzandlari": {"en": "Oshi no Ko", "orig": "Oshi no Ko", "ru": "Звёздное дитя"},
    "ovoz shakli": {"en": "A Silent Voice", "orig": "Koe no Katachi", "ru": "Форма голоса"},
    "tokio qasoskorlari": {"en": "Tokyo Revengers", "orig": "Tokyo Revengers", "ru": "Токийские мстители"},
    "tokio gul": {"en": "Tokyo Ghoul", "orig": "Tokyo Ghoul", "ru": "Токийский гуль"},
    "kok zindon": {"en": "Blue Lock", "orig": "Blue Lock", "ru": "Синяя тюрьма: Блю Лок"},
    "aprel yolgoni": {"en": "Your Lie in April", "orig": "Shigatsu wa Kimi no Uso", "ru": "Твоя апрельская ложь"},
    "zombi 100": {"en": "Zom 100: Bucket List of the Dead", "orig": "Zom 100", "ru": "Предсмертный список зомби"},
    "frieren songi yolga kuzatuvchi": {"en": "Frieren: Beyond Journey's End", "orig": "Sousou no Frieren", "ru": "Провожающая в последний путь Фрирен"},
    "frieren": {"en": "Frieren: Beyond Journey's End", "orig": "Sousou no Frieren", "ru": "Провожающая в последний путь Фрирен"},
    "vinland haqida afsona": {"en": "Vinland Saga", "orig": "Vinland Saga", "ru": "Сага о Винланде"},
    "zanjirli qul": {"en": "Chained Soldier", "orig": "Mato Seihei no Slave", "ru": "Раб спецотряда демонического города"},
    "mob psixo 100": {"en": "Mob Psycho 100", "orig": "Mob Psycho 100", "ru": "Моб Психо 100"},
    "yoz arvohi": {"en": "Summer Ghost", "orig": "Summer Ghost", "ru": "Летний призрак"},
    "zindonda qizlar bilan uchrashish yomonmi": {"en": "Is It Wrong to Try to Pick Up Girls in a Dungeon?", "orig": "Dungeon ni Deai wo Motomeru no wa Machigatteiru Darou ka", "ru": "Может, я встречу тебя в подземелье?"},
    "qamoqxona maktabi": {"en": "Prison School", "orig": "Kangoku Gakuen", "ru": "Школа строгого режима"},
    "seni oshqozon osti bezingni yemoqchiman": {"en": "I Want to Eat Your Pancreas", "orig": "Kimi no Suizou wo Tabetai", "ru": "Я хочу съесть твою поджелудочную"},
    "shamol kotariladi": {"en": "The Wind Rises", "orig": "Kaze Tachinu", "ru": "Ветер крепчает"},
    "sen uchun olmas": {"en": "To Your Eternity", "orig": "Fumetsu no Anata e", "ru": "Для тебя, Бессмертный"},
    "nier avtomatlari": {"en": "NieR:Automata Ver1.1a", "orig": "NieR:Automata Ver1.1a", "ru": "Ниер: Автомата — Версия 1.1а"},
    "bir soatlik qizcha": {"en": "Rent-a-Girlfriend", "orig": "Kanojo, Okarishimasu", "ru": "Девушка напрокат"},
    "qora klever": {"en": "Black Clover", "orig": "Black Clover", "ru": "Чёрный клевер"},
    "dandadan": {"en": "Dan Da Dan", "orig": "Dandadan", "ru": "Дандадан"},
    "dororo": {"en": "Dororo", "orig": "Dororo", "ru": "Дороро"},
    "kaiju 8": {"en": "Kaiju No. 8", "orig": "Kaijuu 8-gou", "ru": "Кайдзю номер восемь"},
    "songi telba boss paydo boldi": {"en": "A Wild Last Boss Appeared!", "orig": "Yasei no Last Boss ga Arawareta!", "ru": "Дикий последний босс появился!"},
    "so'nggi telba boss paydo bo'ldi": {"en": "A Wild Last Boss Appeared!", "orig": "Yasei no Last Boss ga Arawareta!", "ru": "Дикий последний босс появился!"},
    "oxirgi telba boss paydo boldi": {"en": "A Wild Last Boss Appeared!", "orig": "Yasei no Last Boss ga Arawareta!", "ru": "Дикий последний босс появился!"},
    "ozga dunyoda ruhsatsiz": {"en": "No Longer Allowed in Another World", "orig": "Isekai Shikkaku", "ru": "Дисквалифицирован по жизни"},
    "o'zga dunyoda ruxsatsiz": {"en": "No Longer Allowed in Another World", "orig": "Isekai Shikkaku", "ru": "Дисквалифицирован по жизни"},
    "ozga dunyoda ruxsatsiz": {"en": "No Longer Allowed in Another World", "orig": "Isekai Shikkaku", "ru": "Дисквалифицирован по жизни"},
}





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
2. Agar bu Anime yoki Yaponiya/Koreya animatsiyasi bo'lsa (yoki o'zbekcha tarjima qilingan bo'lsa, masalan: "Meni oyga olib ket" -> "Tonikaku Kawaii", "Iblislar qotili" -> "Kimetsu no Yaiba", "Qahramon x" -> "To Be Hero X"), "original_title" ga rasmiy yaponcha Romaji nomini, "search_title_en" ga rasmiy inglizcha nomini, "search_title_ru" ga ruscha nomini yoz. Janrlariga albatta "Anime" qo'sh.
3. Agar davlat (masalan: Qozog'iston, Hindiston, Rossiya, O'zbekiston, Ispaniya) ko'rsatilgan bo'lsa, o'sha davlat kinosi deb tahlil qil.
4. Agar filmning original xorijiy nomi 100% aniq bo'lmasa, taxminiy noto'g'ri nom to'qish o'rniga original_title ni null qil yoki o'zbekcha nomini qoldir.
5. "description" maydoniga albatta berilgan filmning HAQIQIY syujetini o'zbek tilida to'liq va ravon yoz.

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
    try:
        from scraper.title_cleaner import clean_movie_title_simple
        return clean_movie_title_simple(raw_title)
    except Exception:
        # Fallback
        t = re.sub(r'[*_~`#\[\]\(\)]', '', raw_title)
        t = re.split(r'\s*[|/]\s*', t)[0]
        return re.sub(r'\s+', ' ', t).strip(' -–—:,')


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

def latin_to_cyrillic(text: Optional[str]) -> str:
    """O'zbekcha/ruscha lotin matnni kirillga o'giradi (TMDb ru-RU qidiruvi uchun)."""
    if not text:
        return ""
    table = {
        'sh': 'ш', 'ch': 'ч', 'yo': 'ё', 'yu': 'ю', 'ya': 'я', 'ye': 'е', 'oʻ': 'ў', "o'": 'ў', "o`": 'ў', "gʻ": 'ғ', "g'": 'ғ',
        'a': 'а', 'b': 'б', 'v': 'в', 'g': 'г', 'd': 'д', 'e': 'е', 'z': 'з', 'i': 'и',
        'j': 'ж', 'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н', 'o': 'о', 'p': 'п', 'r': 'р',
        's': 'с', 't': 'т', 'u': 'у', 'f': 'ф', 'x': 'х', 'y': 'й', 'q': 'қ', 'h': 'ҳ',
        'ts': 'ц'
    }
    t = text.lower()
    for k, v in table.items():
        t = t.replace(k, v)
    return t


def score_tmdb_candidate(
    candidate: Dict[str, Any],
    query: str,
    target_year: Optional[int] = None,
    expected_original_title: Optional[str] = None
) -> float:
    """
    TMDb nomzodini baholaydi (yuqori ball = aniq moslik).
    Posteri bor, yili mos kelgan va nomi to'liq tushgan filmlar ustunlikka ega bo'ladi.
    """
    cand_title = candidate.get("title") or candidate.get("name") or ""
    cand_orig = candidate.get("original_title") or candidate.get("original_name") or ""
    cand_year = candidate.get("release_year") or candidate.get("year")
    poster_url = candidate.get("poster_url")

    # 1. Yil tekshiruvi: Agar target_year berilgan bo'lsa, oraliq 2 yildan oshmasligi shart (agar anime/original nom aniq ko'rsatilmagan bo'lsa)
    if target_year and cand_year:
        try:
            diff = abs(int(cand_year) - int(target_year))
            if diff > 2 and not expected_original_title:
                return -1.0
        except (ValueError, TypeError):
            pass


    # 2. Sarlavha o'xshashligi
    query_tokens = normalize_title_tokens(query)
    orig_tokens = normalize_title_tokens(expected_original_title)
    cand_tokens = normalize_title_tokens(cand_title) | normalize_title_tokens(cand_orig)

    if not cand_tokens:
        return -1.0

    match_found = False
    title_overlap = 0.0
    for target_set in [orig_tokens, query_tokens]:
        if not target_set:
            continue
        overlap = target_set.intersection(cand_tokens)
        ratio = len(overlap) / len(target_set)
        if ratio >= 0.4:
            match_found = True
            title_overlap = max(title_overlap, ratio)

    # Substring tekshiruvi (kamida 4 ta belgi)
    q_clean = re.sub(r'[^\w]', '', query.lower())
    orig_clean = re.sub(r'[^\w]', '', (expected_original_title or '').lower())
    c_clean = re.sub(r'[^\w]', '', cand_title.lower())
    co_clean = re.sub(r'[^\w]', '', cand_orig.lower())

    for t in [q_clean, orig_clean]:
        if len(t) >= 4:
            if t in c_clean or t in co_clean or c_clean in t or co_clean in t:
                match_found = True
                title_overlap = max(title_overlap, 0.8)

    # Agar nomzod Kanji/Kirill bo'lsa va TMDb qidiruvida topilgan bo'lsa (yapon animelari uchun)
    if not match_found and (expected_original_title or query):
        has_non_latin = any(ord(c) > 1200 or 0x4E00 <= ord(c) <= 0x9FFF for c in cand_title + cand_orig)
        if has_non_latin and poster_url:
            match_found = True
            title_overlap = max(title_overlap, 0.75)

    if not match_found:
        return -1.0

    # Asosiy ball
    score = title_overlap * 50.0

    # Poster tekshiruvi: posteri bor nomzodlarga katta bonus, posteri yo'q nomzodlarga jazo
    if poster_url:
        score += 30.0
    else:
        score -= 40.0

    # Yil balli
    if target_year and cand_year:
        try:
            diff = abs(int(cand_year) - int(target_year))
            if diff == 0:
                score += 30.0
            elif diff == 1:
                score += 15.0
            elif diff == 2:
                score += 5.0
            elif diff > 2 and expected_original_title:
                score -= 10.0
        except (ValueError, TypeError):

            pass
    elif target_year and not cand_year:
        score -= 15.0

    # Original nomning to'liq mos kelishi
    if expected_original_title and cand_orig:
        if expected_original_title.strip().lower() == cand_orig.strip().lower():
            score += 40.0

    # Reyting bonusi
    vote_avg = candidate.get("vote_average") or 0.0
    score += min(float(vote_avg), 10.0)

    return score


def is_valid_tmdb_match(
    candidate: Dict[str, Any],
    query: str,
    target_year: Optional[int] = None,
    expected_original_title: Optional[str] = None
) -> bool:
    return score_tmdb_candidate(candidate, query, target_year, expected_original_title) > 0.0


async def enrich_movie_smart(
    raw_title: str,
    year: Optional[int] = None,
    source_poster: Optional[str] = None,
    source_desc: Optional[str] = None,
    source_genres: Optional[str] = None,
    caption: Optional[str] = None,
    media_type: str = "movie",
    item_url: Optional[str] = None,
    original_title: Optional[str] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """
    AI (Gemini) + TMDb orqali film/serialni to'liq ma'lumotlar, poster, treyler,
    rejissyor, aktyorlar va kategoriyalar bilan to'ldirish.
    Xatolik va begona kinolarga almashtirilib ketishining oldi olingan.
    """
    clean_title = clean_movie_title(raw_title)

    # Normalize source_poster URL - AniToob img_proxy linklari ishlamaydi (HTML 340KB qaytaradi)
    if source_poster and source_poster.startswith("/"):
        source_poster = f"https://asilmedia.org{source_poster}"
    if source_poster and not source_poster.startswith("http"):
        source_poster = None
    if source_poster and ("img_proxy=" in source_poster or "anitoobtv.uz" in source_poster):
        source_poster = None

    detected_type = "series" if (media_type == "series" or any(w in raw_title.lower() for w in ["serial", "dorama", "mavsum"])) else "movie"

    # Anime nomini lug'atdan tekshirish
    norm_clean = clean_title.lower().strip()
    matched_anime_dict = None
    for a_key, a_val in ANIME_TITLE_MAP.items():
        if a_key in norm_clean or norm_clean in a_key:
            matched_anime_dict = a_val
            break

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
        "original_title": original_title or (matched_anime_dict.get("orig") if matched_anime_dict else None),
        "description": clean_default_desc,
        "poster_url": source_poster,
        "trailer_url": None,
        "release_year": year,
        "imdb_rating": None,
        "tmdb_rating": None,
        "tmdb_id": None,
        "genres": source_genres or ("Anime, Serial" if matched_anime_dict else ("Serial" if detected_type == "series" else "Tarjima kino")),
        "cast": None,
        "director": None,
        "runtime": 120,
        "is_18_plus": False,
        "category_ids": [],
        "source_used": "source",
        "media_type": detected_type
    }

    # Kategoriyalar xaritasi
    cat_map = await get_all_categories_map()
    matched_cat_names = set()
    if matched_anime_dict:
        matched_cat_names.add("anime")

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
    if matched_anime_dict:
        if matched_anime_dict.get("orig"):
            search_queries.append((matched_anime_dict["orig"], default_tmdb_type))
        if matched_anime_dict.get("en"):
            search_queries.append((matched_anime_dict["en"], default_tmdb_type))
        if matched_anime_dict.get("ru"):
            search_queries.append((matched_anime_dict["ru"], default_tmdb_type))

    if ai_info and ai_info.get("original_title") and (ai_info["original_title"], default_tmdb_type) not in search_queries:
        search_queries.append((ai_info["original_title"], default_tmdb_type))
    if ai_info and ai_info.get("search_title_en") and (ai_info["search_title_en"], default_tmdb_type) not in search_queries:
        search_queries.append((ai_info["search_title_en"], default_tmdb_type))
    if ai_info and ai_info.get("search_title_ru") and (ai_info["search_title_ru"], default_tmdb_type) not in search_queries:
        search_queries.append((ai_info["search_title_ru"], default_tmdb_type))
    if clean_title not in [q[0] for q in search_queries]:
        search_queries.append((clean_title, default_tmdb_type))

    # Ruscha/O'zbekcha kirillcha transliteratsiyasini ham qo'shamiz (masalan "Adrenalin" -> "адреналин")
    cyr_clean = latin_to_cyrillic(clean_title)
    if cyr_clean and cyr_clean not in [q[0] for q in search_queries]:
        search_queries.append((cyr_clean, default_tmdb_type))

    matched_tmdb = None
    best_score = 0.0
    target_year = metadata["release_year"] or year
    expected_orig = ai_info.get("original_title") if ai_info else None

    # Avval asosiy ctype (masalan serial uchun faqat tv) orqali barcha qidiruvlarni tekshiramiz
    for query, ctype in search_queries:
        if not query or len(query.strip()) < 2:
            continue
        try:
            results = await tmdb_client.search(query=query, content_type=ctype)
            if results:
                for res in results:
                    score = score_tmdb_candidate(
                        candidate=res,
                        query=query,
                        target_year=target_year,
                        expected_original_title=expected_orig
                    )
                    if score > best_score:
                        best_score = score
                        matched_tmdb = res
                        if score >= 90.0:
                            break
        except Exception as e:
            logger.warning(f"TMDb search error query '{query}' ({ctype}): {e}")
        if best_score >= 90.0:
            break

    # Faqat mos natija topilmagan bo'lsagina muqobil turdan qidiramiz
    if not matched_tmdb or best_score < 60.0:
        for query, ctype in search_queries:
            alt_type = "movie" if ctype == "tv" else "tv"
            try:
                results = await tmdb_client.search(query=query, content_type=alt_type)
                if results:
                    for res in results:
                        score = score_tmdb_candidate(
                            candidate=res,
                            query=query,
                            target_year=target_year,
                            expected_original_title=expected_orig
                        )
                        if score > best_score:
                            best_score = score
                            matched_tmdb = res
                            if score >= 90.0:
                                break
            except Exception as e:
                logger.warning(f"TMDb alt search error query '{query}' ({alt_type}): {e}")
            if best_score >= 90.0:
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

    # 4.1 Agar poster hali ham yo'q bo'lsa, Shikimori Anime API orqali qidiramiz
    if not metadata.get("poster_url"):
        shikimori_queries = []
        if matched_anime_dict:
            for k in ["orig", "en", "ru"]:
                if matched_anime_dict.get(k) and matched_anime_dict[k] not in shikimori_queries:
                    shikimori_queries.append(matched_anime_dict[k])
        if ai_info:
            for k in ["original_title", "search_title_en", "search_title_ru"]:
                if ai_info.get(k) and ai_info[k] not in shikimori_queries:
                    shikimori_queries.append(ai_info[k])
        if clean_title not in shikimori_queries:
            shikimori_queries.append(clean_title)

        for sq in shikimori_queries:
            if not sq or len(sq.strip()) < 2:
                continue
            try:
                async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                    shiki_url = f"https://shikimori.one/api/animes?search={urllib.parse.quote(sq.strip())}&limit=1"
                    shiki_resp = await client.get(shiki_url, headers={"User-Agent": "Kinochi/1.0"})
                    if shiki_resp.status_code == 200:
                        shiki_data = shiki_resp.json()
                        if shiki_data and isinstance(shiki_data, list) and len(shiki_data) > 0:
                            img_path = shiki_data[0].get("image", {}).get("original")
                            if img_path:
                                metadata["poster_url"] = f"https://shikimori.one{img_path}"
                                if not metadata.get("original_title"):
                                    metadata["original_title"] = shiki_data[0].get("name")
                                logger.info(f"✅ Shikimori orqali anime posteri muvaffaqiyatli topildi ({sq}): {metadata['poster_url']}")
                                break
            except Exception as e:
                logger.debug(f"Shikimori search error '{sq}': {e}")

    # Treyler topilmagan bo'lsa, YouTube qidiruv linki
    if not metadata["trailer_url"] and ai_info and ai_info.get("trailer_query"):
        import urllib.parse
        q = urllib.parse.quote_plus(ai_info["trailer_query"])
        metadata["trailer_url"] = f"https://www.youtube.com/results?search_query={q}"

    # 18+ (kattalar uchun) kontentni aniqlash
    is_adult = False
    if matched_tmdb and matched_tmdb.get("adult"):
        is_adult = True
    check_text = f"{raw_title} {clean_title} {metadata.get('genres', '')} {caption or ''} {source_desc or ''}".lower()
    adult_keywords = ["18+", "erotika", "hentai", "ecchi", "kattalar uchun", "erotic", "adult", "porn", "r18", "порно", "эротика"]
    if any(kw in check_text for kw in adult_keywords):
        is_adult = True

    metadata["is_18_plus"] = is_adult
    if is_adult:
        for cname in cat_map:
            if "18+" in cname:
                matched_cat_names.add(cname)
                break

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
