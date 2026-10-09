"""
Smart Title Cleaner for Kinochi Project Scraper.
Extracts clean, accurate movie & series titles, cleans SEO noise,
separates alternative translations/subtitles into variants, and recovers years.
"""

import re
from typing import Dict, Any, List, Optional


def clean_scraped_title(raw_title: str, url_or_slug: Optional[str] = None) -> Dict[str, Any]:
    """
    Tozalanadi:
    - Boshidagi reyting raqamlari (masalan '2 Ruxshunos' -> 'Ruxshunos')
    - Slash / pipe bo'yicha ajratish (birinchisini asosiy qilib, qolganini variantlar qilish)
    - SEO, janr, davlat, premyera, sifat, til axlatlarini tozalash
    - Qismlar, fasllar ko'rsatkichlarini tozalash
    - Takroriy sarlavhalarni ajratish (masalan 'Tungi Agent Tungi Qoriqchi' -> 'Tungi Agent')
    - Transliteratsiya dublikatlarini ajratish (masalan 'Venzdey Wednesday' -> 'Venzdey')
    """
    if not raw_title:
        return {"title": "", "variants": [], "year": None}

    text = str(raw_title).strip()
    slug = str(url_or_slug or "").strip()

    # 0. Yilni ajratib olish (sarlavhadan yoki slugdan)
    year = None
    y_match = re.search(r'\b(19\d{2}|20\d{2})\b', text)
    if y_match:
        year = int(y_match.group(1))
    elif slug:
        y_slug = re.search(r'\b(19\d{2}|20\d{2})\b', slug)
        if y_slug:
            year = int(y_slug.group(1))

    # 1. HTML va maxsus belgilarni tozalash
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&quot;', '"', text)
    text = re.sub(r'&#039;|&apos;', "'", text)
    text = re.sub(r'[\xa0\u200b\ufeff\ufffd]+', ' ', text)
    text = re.sub(r'[^\w\s\-\'\"`‘’,.:?!/|#+]', ' ', text)
    text = re.sub(r'\.{2,}|…', '', text)

    # 2. Boshidagi reyting raqamlari va badge larni tozalash (masalan "2 Ruxshunos", "+1085 1080p")
    text = re.sub(r'^\s*\+?\d{1,4}\s+(?:1080p|720p|480p|hd)?\s*', '', text, flags=re.I)
    text = re.sub(r'^\s*(?:top\s*)?\d{1,2}\s+(?=[A-ZА-ЯOʻGʻShCh])', '', text)
    text = re.sub(r'^\s*(\d{1,2})[-_]?(?:o[\'`]?rin|orin|top)\s*', '', text, flags=re.I)

    # 3. Fasllar va qismlar (masalan "Ajdar xonadoni uyi 3 mavsum fasl", "1-6-fasllar", "3-fasl 5-qism!")
    text = re.sub(r'\b\d+(?:-\d+)?\s*-(?:fasl|mavsum|qism)[lar]*\b!?', '', text, flags=re.I)
    text = re.sub(r'\b\d+-(?:fasl|mavsum)\s+\d+-qism\b!?', '', text, flags=re.I)
    text = re.sub(r'\b\d+\s+(?:mavsum|fasl|qism)\b.*$', '', text, flags=re.I)

    # 4. Sifat va formatlar
    text = re.sub(r'\b(?:1080p|720p|480p|4k|full\s*hd|hd)\b', '', text, flags=re.I)

    # 5. Standart SEO axlatlari
    noise_patterns = [
        r"\b(?:o['\"`‘’]?zbek|uzbek)\s+tilida\b",
        r"\b(?:o['\"`‘’]?zbekcha|uzbekcha)(?:\s+tarjima)?\b",
        r"\btarjima\s+(?:kino|film|serial|jangari)\b",
        r"\bpremyera!?\b", r"\byangi\s+premyera!?\b",
        r"\byangi\s+(?:kino|film|serial|dorama)\b",
        r"\bonlayn\s+ko['\"`‘’]?rish\b", r"\bko['\"`‘’]?rish\b",
        r"\btas[\s\-_]*ix\b", r"\bskachat\b", r"\byuklab\s+olish\b",
        r"\bbarcha\s+qismlar[i]?\b",
        r"\s*[\(\[]\s*(?:19\d{2}|20\d{2})\s*[\)\]]",
        r"\b(19\d{2}|20\d{2})\b",
        # Davlat va media turlari
        r"\b(?:koreys|xitoy|turk|hind|rus|aqsh|eron|yaponiya|sssr|qozoq|koreya|hindiston)\s+(?:dorama|seriali?|kinosi?|filmi?|multfilmi?|multiseriali?)\b",
        r"\b(?:koreys|xitoy|turk|hind|rus|aqsh|eron|yaponiya|sssr|qozoq)\s+(?:kino|film|serial)\b",
        r"\b(?:dorama|multiseriali?|multfilmi?|anime(?:si)?\s+seriali?|anime(?:si)?|hujjatli\s+film)\b",
        r"\bseriali?\b",
        r"\bkinosi?\b",
        r"\bfilmi?\b",
        r"\bkino\b",
        r"\bfilm\b",
        r"\btarjima\b",
        r"\b(?:to['\"`‘’]?liq|toliq)\b",
        r"\b(?:uzmovi|uzmovi\.com|uzmovi\.net)\b",
        r"\b(?:asilmedia|asilmedia\.net|asilmedia\.org)\b",
        r"\b(?:yuqori\s+sifa[dt](?:at|da)?|yangi\s+format(?:da)?)\b",
        r"\b(?:subtitr(?:da)?|subtitrli)\b",
        r"\b(?:marvel\s+kinolari|dc\s+kinolari)\b",
        r"\b(?:movie\s+free\s+download|free\s+download)\b",
        r"\b(?:ujas|komediya|jangari|fantastika)\b",
        r"\b(?:sssr|qozoq|koreys|hind|turk|xitoy|rus|aqsh)\b",
        r"\b(?:o['\"`‘’]?zbek|uzbek)\b",
        r"\b(?:og['\"`‘’]?ayni|oshna)\b",
    ]
    for p in noise_patterns:
        text = re.sub(p, ' ', text, flags=re.IGNORECASE)

    # 6. Slash yoki pipe bo'yicha ajratish
    raw_parts = [p.strip() for p in re.split(r'[/|]', text) if p.strip()]
    parts = []
    for p in raw_parts:
        p_clean = re.sub(r'[\(\)\[\]*~`#]', ' ', p)
        p_clean = re.sub(r'\s+', ' ', p_clean).strip(' -–—:,')
        if len(p_clean) >= 2:
            parts.append(p_clean)

    if not parts:
        return {"title": raw_title.strip(), "variants": [], "year": year}

    primary = parts[0]
    variants = parts[1:]

    # 7. Takroriy bosh so'z (masalan: "Tungi Agent Tungi Qoriqchi Tungi Tansoqchi")
    words = primary.split()
    if len(words) >= 4 and len(words[0]) >= 3:
        first_word = words[0].lower()
        repeat_indices = [i for i, w in enumerate(words) if i > 0 and w.lower() == first_word]
        if repeat_indices:
            first_repeat = repeat_indices[0]
            if first_repeat >= 2:
                clean_primary = " ".join(words[:first_repeat])
                alt = " ".join(words[first_repeat:])
                primary = clean_primary
                variants.append(alt)

    # 8. Transliteratsiya dublikatlari (masalan "Ruxshunos Ruhshunos Mentalist")
    p_words = primary.split()
    if len(p_words) >= 2:
        w0_norm = p_words[0].lower().replace('x', 'h')
        w1_norm = p_words[1].lower().replace('x', 'h')
        if w0_norm == w1_norm:
            clean_p = p_words[0]
            remainder = " ".join(p_words[2:])
            if remainder:
                primary = clean_p
                variants.append(remainder)
            else:
                primary = clean_p

    # 9. Venzdey / Wednesday / Uenzdey
    p_words = primary.split()
    if len(p_words) >= 2:
        w0, w1 = p_words[0].lower(), p_words[1].lower()
        if (w0.startswith("venzd") and w1.startswith("wednes")) or (w0.startswith("wednes") and w1.startswith("venzd")):
            primary = p_words[0].capitalize()
            variants.append("Wednesday")

    # 10. Ruscha qo'shimcha nomlar (masalan "Najot Shifoxonasi Uchitel Kim Doktor Romantik")
    m_ru = re.search(r'\b(uchitel|doktor\s+romantik|mentalist)\b', primary, re.I)
    if m_ru and m_ru.start() > 4:
        alt_ru = primary[m_ru.start():].strip()
        primary = primary[:m_ru.start()].strip(' -–—:,')
        if alt_ru:
            variants.append(alt_ru)

    # 11. Lotincha va Kirillcha aralash sarlavhalarni ajratish (masalan "Afsungar Merlin Мерлин")
    m_split = re.search(r'^([A-Za-z0-9\s\'\`\-\–]+?)\s+([А-Яа-яЁё0-9\s\'\`\-\–]+)$', primary)
    if m_split:
        p_lat = m_split.group(1).strip()
        p_cyr = m_split.group(2).strip()
        if len(p_lat) >= 3 and len(p_cyr) >= 3:
            primary = p_lat
            variants.append(p_cyr)

    primary = re.sub(r'\s+', ' ', primary).strip(' -–—:,')

    return {
        "title": primary or raw_title.strip(),
        "variants": variants,
        "year": year
    }


def clean_movie_title_simple(raw_title: str) -> str:
    """Faqat tozalangan qisqa sarlavhani qaytaradi."""
    res = clean_scraped_title(raw_title)
    return res["title"]
