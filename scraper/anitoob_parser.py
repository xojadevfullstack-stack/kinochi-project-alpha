"""
AniToob (@ANITOOBUZ_BOT / bot.anitoobtv.uz) anime parser for Kinochi Project.
Manages anime catalog, metadata scraping from sitemap/web pages,
pagination, search, and queue items.
"""

import os
import re
import json
import ssl
import logging
import asyncio
import urllib.request
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any
import aiohttp
from bs4 import BeautifulSoup

from scraper.queue_manager import QueueItem
from scraper.title_cleaner import clean_scraped_title

logger = logging.getLogger(__name__)

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "anitoob_catalog.json")
PAGE_SIZE = 20

_CATALOG_CACHE: Optional[Dict[str, Dict[str, Any]]] = None

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "uz,en-US,en;q=0.9",
}


def get_anitoob_catalog() -> Dict[str, Dict[str, Any]]:
    """Loads and caches anime catalog mapping {str(code): dict}."""
    global _CATALOG_CACHE
    if _CATALOG_CACHE is not None:
        return _CATALOG_CACHE

    if os.path.exists(CATALOG_PATH):
        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                norm: Dict[str, Dict[str, Any]] = {}
                for k, v in raw_data.items():
                    if isinstance(v, str):
                        norm[str(k)] = {
                            "code": str(k),
                            "title": v,
                            "url": f"https://t.me/ANITOOBUZ_BOT?start={k}",
                            "poster_url": None,
                            "site_url": f"https://bot.anitoobtv.uz/?anime={k}"
                        }
                    elif isinstance(v, dict):
                        norm[str(k)] = v
                _CATALOG_CACHE = norm
                return _CATALOG_CACHE
        except Exception as e:
            logger.warning(f"Error loading anitoob_catalog.json: {e}")

    _CATALOG_CACHE = {}
    return _CATALOG_CACHE


def save_anitoob_catalog(catalog: Dict[str, Dict[str, Any]]) -> None:
    """Saves updated catalog to JSON file."""
    global _CATALOG_CACHE
    _CATALOG_CACHE = catalog
    try:
        with open(CATALOG_PATH, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving anitoob_catalog.json: {e}")


async def fetch_anitoob_sitemap_async(session: Optional[aiohttp.ClientSession] = None) -> Dict[str, Dict[str, Any]]:
    """
    Fetches the latest sitemap from https://bot.anitoobtv.uz/sitemap.xml
    and refreshes the catalog cache.
    """
    sitemap_url = "https://bot.anitoobtv.uz/sitemap.xml"
    xml_data = ""

    if session:
        try:
            async with session.get(sitemap_url, headers=HEADERS, ssl=False, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    xml_data = await resp.text(errors="ignore")
        except Exception as e:
            logger.warning(f"Error fetching anitoob sitemap via aiohttp: {e}")

    if not xml_data:
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(sitemap_url, headers=HEADERS)
            loop = asyncio.get_event_loop()
            xml_data = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, context=ctx, timeout=15).read().decode("utf-8", errors="ignore"))
        except Exception as e:
            logger.warning(f"Error fetching anitoob sitemap via urllib: {e}")

    if not xml_data:
        return get_anitoob_catalog()

    catalog = get_anitoob_catalog()
    try:
        root = ET.fromstring(xml_data)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "img": "http://www.google.com/schemas/sitemap-image/1.1"}
        for u in root.findall("s:url", ns):
            loc = u.find("s:loc", ns).text if u.find("s:loc", ns) is not None else ""
            m = re.search(r"anime=(\d+)", loc)
            if not m:
                continue
            code = m.group(1)
            img_elem = u.find("img:image", ns)
            img_title = img_elem.find("img:title", ns).text if img_elem is not None and img_elem.find("img:title", ns) is not None else ""
            img_loc = img_elem.find("img:loc", ns).text if img_elem is not None and img_elem.find("img:loc", ns) is not None else ""

            clean_t = re.sub(r"\s+o['ʼ`]zbek\s+tilida.*$", "", img_title, flags=re.IGNORECASE).strip()
            if code not in catalog:
                catalog[code] = {
                    "code": code,
                    "title": clean_t or f"Anime #{code}",
                    "url": f"https://t.me/ANITOOBUZ_BOT?start={code}",
                    "poster_url": img_loc,
                    "site_url": loc
                }
            else:
                if not catalog[code].get("poster_url") and img_loc:
                    catalog[code]["poster_url"] = img_loc
                if not catalog[code].get("site_url") and loc:
                    catalog[code]["site_url"] = loc
        save_anitoob_catalog(catalog)
    except Exception as e:
        logger.error(f"Error parsing anitoob sitemap XML: {e}")

    return catalog


async def fetch_anitoob_metadata_async(code: str, session: Optional[aiohttp.ClientSession] = None) -> Optional[Dict[str, Any]]:
    """
    Fetches rich metadata from https://bot.anitoobtv.uz/?anime={code} by parsing JSON-LD Schema.
    Returns dict with title, description, numberOfEpisodes, datePublished, genre, image, etc.
    """
    page_url = f"https://bot.anitoobtv.uz/?anime={code}"
    html_text = ""

    if session:
        try:
            async with session.get(page_url, headers=HEADERS, ssl=False, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                if resp.status == 200:
                    html_text = await resp.text(errors="ignore")
        except Exception as e:
            logger.debug(f"Error fetching anitoob page {page_url} via aiohttp: {e}")

    if not html_text:
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(page_url, headers=HEADERS)
            loop = asyncio.get_event_loop()
            html_text = await loop.run_in_executor(None, lambda: urllib.request.urlopen(req, context=ctx, timeout=12).read().decode("utf-8", errors="ignore"))
        except Exception as e:
            logger.debug(f"Error fetching anitoob page {page_url} via urllib: {e}")

    if not html_text:
        return None

    try:
        soup = BeautifulSoup(html_text, "html.parser")
        for script in soup.find_all("script", type="application/ld+json"):
            if not script.string:
                continue
            data = json.loads(script.string)
            graph = data.get("@graph", [])
            for node in graph:
                ntype = node.get("@type")
                if ntype in ("TVSeries", "Movie", "VideoObject"):
                    res: Dict[str, Any] = {
                        "title": node.get("name"),
                        "description": node.get("description"),
                        "episodes_count": node.get("numberOfEpisodes"),
                        "genres": node.get("genre", []),
                        "poster_url": node.get("image") or (node.get("thumbnailUrl", [None])[0] if isinstance(node.get("thumbnailUrl"), list) else None),
                        "site_url": node.get("url") or page_url,
                    }
                    raw_year = node.get("datePublished")
                    if raw_year:
                        ym = re.search(r"\b(19\d\d|20\d\d)\b", str(raw_year))
                        if ym:
                            res["year"] = int(ym.group(1))
                    
                    if ntype == "Movie" or res.get("episodes_count") == 1:
                        res["media_type"] = "movie"
                    else:
                        res["media_type"] = "series"
                    return res
    except Exception as e:
        logger.debug(f"Error parsing JSON-LD for anitoob #{code}: {e}")

    return None


async def parse_anitoob_page_async(
    session: Optional[Any] = None,
    page: int = 1,
    min_rating: float = 0.0,
    media_type: str = "all"
) -> List[QueueItem]:
    """
    Returns a page of QueueItem objects for AniToob.
    Page 1: items 0..20, Page 2: items 20..40, etc.
    """
    catalog = get_anitoob_catalog()
    
    # Sort codes numerically
    sorted_codes = sorted(catalog.keys(), key=lambda x: int(x) if x.isdigit() else 999999)
    if not sorted_codes:
        # Fallback to refreshing from sitemap
        catalog = await fetch_anitoob_sitemap_async(session)
        sorted_codes = sorted(catalog.keys(), key=lambda x: int(x) if x.isdigit() else 999999)

    start_idx = max(0, (page - 1) * PAGE_SIZE)
    end_idx = start_idx + PAGE_SIZE

    items: List[QueueItem] = []

    if start_idx < len(sorted_codes):
        page_codes = sorted_codes[start_idx:end_idx]
        for c in page_codes:
            info = catalog.get(c, {})
            title = info.get("title") or f"AniToob Anime #{c}"
            cleaned_info = clean_scraped_title(title)
            cleaned_title = cleaned_info["title"] if isinstance(cleaned_info, dict) else str(cleaned_info)
            item_year = info.get("year") or (cleaned_info.get("year") if isinstance(cleaned_info, dict) else None)

            # Check if title indicates film
            is_film = bool(re.search(r"\b(film|kino|filmi)\b", title, re.IGNORECASE))
            m_type = "movie" if is_film else "series"
            if media_type != "all" and m_type != media_type:
                continue

            poster = info.get("poster_url")
            items.append(QueueItem(
                id=f"anitoob_{c}",
                source="anitoob",
                title=cleaned_title,
                original_title=None,
                year=item_year,
                media_type=m_type,
                url=f"https://t.me/ANITOOBUZ_BOT?start={c}",
                poster_url=poster,
                episodes_count=1 if m_type == "movie" else info.get("episodes_count")
            ))

    return items


def parse_anitoob_page(
    page: int = 1,
    min_rating: float = 0.0,
    media_type: str = "all"
) -> List[QueueItem]:
    """Synchronous wrapper for parse_anitoob_page_async."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(parse_anitoob_page_async(None, page, min_rating, media_type))
        return loop.run_until_complete(parse_anitoob_page_async(None, page, min_rating, media_type))
    except Exception:
        return asyncio.run(parse_anitoob_page_async(None, page, min_rating, media_type))


async def search_anitoob_async(
    query: str,
    session: Optional[aiohttp.ClientSession] = None
) -> List[QueueItem]:
    """
    Searches AniToob catalog for query matching anime titles or codes.
    Returns List of QueueItem.
    """
    clean_q = query.strip().lower()
    if not clean_q:
        return []

    catalog = get_anitoob_catalog()
    results: List[QueueItem] = []

    # If query is direct number/code
    if clean_q.isdigit() and clean_q in catalog:
        item = catalog[clean_q]
        t = item.get("title") or f"Anime #{clean_q}"
        cleaned_info = clean_scraped_title(t)
        cl_t = cleaned_info["title"] if isinstance(cleaned_info, dict) else str(cleaned_info)
        is_film = bool(re.search(r"\b(film|kino|filmi)\b", t, re.IGNORECASE))
        return [QueueItem(
            id=f"anitoob_{clean_q}",
            source="anitoob",
            title=cl_t,
            url=f"https://t.me/ANITOOBUZ_BOT?start={clean_q}",
            poster_url=item.get("poster_url"),
            media_type="movie" if is_film else "series"
        )]

    q_words = [w for w in re.split(r"\s+", clean_q) if len(w) > 1]

    for code, item in catalog.items():
        title = (item.get("title") or "").lower()
        if not title:
            continue

        match = False
        if clean_q in title:
            match = True
        elif q_words and all(w in title for w in q_words):
            match = True

        if match:
            raw_t = item.get("title") or f"Anime #{code}"
            cleaned_info = clean_scraped_title(raw_t)
            cl_t = cleaned_info["title"] if isinstance(cleaned_info, dict) else str(cleaned_info)
            is_film = bool(re.search(r"\b(film|kino|filmi)\b", raw_t, re.IGNORECASE))
            results.append(QueueItem(
                id=f"anitoob_{code}",
                source="anitoob",
                title=cl_t,
                url=f"https://t.me/ANITOOBUZ_BOT?start={code}",
                poster_url=item.get("poster_url"),
                media_type="movie" if is_film else "series"
            ))

    return results[:30]


def resolve_anitoob_item(code_or_url: str) -> Optional[QueueItem]:
    """
    Resolves code or URL into a QueueItem.
    Supports '123', 'anitoob_123', 'https://t.me/ANITOOBUZ_BOT?start=123', etc.
    """
    code_match = re.search(r"(?:start=|anime=|_|^)(\d+)$", code_or_url.strip())
    if not code_match:
        return None

    code = code_match.group(1)
    catalog = get_anitoob_catalog()
    info = catalog.get(code, {})

    title = info.get("title") or f"AniToob Anime #{code}"
    cleaned_info = clean_scraped_title(title)
    cleaned = cleaned_info["title"] if isinstance(cleaned_info, dict) else str(cleaned_info)
    item_year = info.get("year") or (cleaned_info.get("year") if isinstance(cleaned_info, dict) else None)
    is_film = bool(re.search(r"\b(film|kino|filmi)\b", title, re.IGNORECASE))

    return QueueItem(
        id=f"anitoob_{code}",
        source="anitoob",
        title=cleaned,
        media_type="movie" if is_film else "series",
        url=f"https://t.me/ANITOOBUZ_BOT?start={code}",
        poster_url=info.get("poster_url"),
        year=item_year,
        episodes_count=1 if is_film else info.get("episodes_count")
    )
