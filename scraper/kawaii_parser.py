"""
Kawaii.uz / Bot.kawaii.uz anime parser for Kinochi Project.
Supports fetching anime metadata, batch async scraping from sitemap/catalog,
and resolving anime for queue processing.
"""

import re
import time
import urllib.request
import urllib.parse
import ssl
import logging
import asyncio
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any
import aiohttp
from bs4 import BeautifulSoup

from scraper.queue_manager import QueueItem
from scraper.title_cleaner import clean_scraped_title

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,uz;q=0.8,ru;q=0.7",
}

PAGE_SIZE = 20

# Memory cache for sitemap slugs
_SITEMAP_CACHE: List[str] = []
_SITEMAP_CACHE_TIME: float = 0.0
_SITEMAP_CACHE_TTL: float = 3600.0  # 1 hour


async def get_all_kawaii_slugs(session: Optional[aiohttp.ClientSession] = None) -> List[str]:
    """
    Fetches all anime slugs from https://bot.kawaii.uz/sitemap.xml with in-memory caching.
    """
    global _SITEMAP_CACHE, _SITEMAP_CACHE_TIME

    now = time.time()
    if _SITEMAP_CACHE and (now - _SITEMAP_CACHE_TIME) < _SITEMAP_CACHE_TTL:
        return _SITEMAP_CACHE

    sitemap_url = "https://bot.kawaii.uz/sitemap.xml"
    xml_data = ""

    if session:
        try:
            async with session.get(sitemap_url, headers=HEADERS, ssl=False, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    xml_data = await resp.text(errors="ignore")
        except Exception as e:
            logger.error(f"Error fetching kawaii sitemap via aiohttp: {e}")
    
    if not xml_data:
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(sitemap_url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
                xml_data = r.read().decode("utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Error fetching kawaii sitemap via urllib: {e}")

    slugs: List[str] = []
    if xml_data:
        try:
            root = ET.fromstring(xml_data)
            for child in root:
                loc = child.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                if loc is not None and loc.text and "/anime/" in loc.text:
                    slug = loc.text.split("/anime/")[-1].strip().strip("/")
                    if slug and slug not in slugs:
                        slugs.append(slug)
        except Exception as e:
            logger.error(f"Error parsing kawaii sitemap XML: {e}")

    if slugs:
        _SITEMAP_CACHE = slugs
        _SITEMAP_CACHE_TIME = now
        logger.info(f"Loaded {len(slugs)} anime slugs from Kawaii.uz sitemap.")
    return _SITEMAP_CACHE


def clean_kawaii_title(raw_title: str) -> str:
    """
    Cleans raw title text from kawaii.uz page.
    Example: "Faqat Tangriga ayon dunyo 2-fasl  O'zbek tilida onlayn tomosha qilish"
    -> "Faqat Tangriga ayon dunyo 2-fasl"
    """
    if not raw_title:
        return ""
    text = raw_title.strip()
    text = text.replace("\ufffd", " ")
    # Remove common separators like  or dashes
    text = re.sub(r'[\uFFFD\u2013\u2014]+', ' ', text)
    # Remove typical suffix
    text = re.sub(
        r'[\s\-\–\|]+(?:o[\'ʼ`]zbek\s+tilida|onlayn|tomosha\s+qilish|barcha\s+qismlar|tas-ix).*$',
        '',
        text,
        flags=re.IGNORECASE
    )
    # Remove trailing dashes or spaces
    text = re.sub(r'[\s\-\–\|]+$', '', text).strip()
    return text


def extract_rating_from_text(text: str) -> Optional[float]:
    """
    Extracts rating from text (e.g. ⭐️ 7.86, rating: 8.0, etc.)
    """
    if not text:
        return None
    m = re.search(r'(?:⭐|★|myanimelist|mal|rating|reyting)[:\s]*([1-9](?:\.\d{1,2})?)\b', text, re.I)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def parse_anime_html_to_item(slug: str, html: str, min_rating: float = 0.0) -> Optional[QueueItem]:
    """
    Parses a single anime page HTML from https://bot.kawaii.uz/anime/{slug}
    and constructs a QueueItem.
    """
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # 1. Title
    raw_title = ""
    h1 = soup.find("h1")
    if h1:
        raw_title = h1.get_text().strip()
    if not raw_title:
        og_t = soup.find("meta", {"property": "og:title"})
        if og_t and og_t.get("content"):
            raw_title = og_t["content"]

    cleaned_t = clean_kawaii_title(raw_title)
    cleaned_info = clean_scraped_title(cleaned_t, url_or_slug=slug)
    title = cleaned_info.get("title") or cleaned_t or slug

    # 2. Original / Alternative title from keywords
    original_title = None
    meta_keywords = soup.find("meta", {"name": "keywords"})
    if meta_keywords and meta_keywords.get("content"):
        kw_list = [k.strip() for k in meta_keywords["content"].split(",") if k.strip()]
        if len(kw_list) > 1:
            for candidate in kw_list[1:]:
                # Candidate should not be purely Cyrillic/Uzbek if possible
                if candidate.lower() != title.lower() and len(candidate) > 2:
                    original_title = candidate
                    break

    # 3. Year
    year = None
    # Look for year in title or HTML
    m_year_title = re.search(r'\b(19\d\d|20\d\d)\b', raw_title)
    if m_year_title:
        year = int(m_year_title.group(1))
    else:
        m_year = re.search(r'\b(19\d\d|20\d\d)\b', html)
        if m_year:
            year = int(m_year.group(1))

    # 4. Media type & Episodes
    lower_html = html.lower()
    is_movie = False
    if "1 / 1 epizod" in lower_html or "1 / 1" in lower_html or "🗂 film" in lower_html:
        is_movie = True
    elif re.search(r'\b(?:film|filmi|to\'liq metrajli)\b', title.lower()):
        is_movie = True

    media_type = "movie" if is_movie else "series"

    episodes_count = 1 if is_movie else None
    m_ep = re.search(r'(\d+)\s*/\s*(\d+)\s*epizod', lower_html)
    if m_ep:
        try:
            episodes_count = int(m_ep.group(2))
        except ValueError:
            pass

    # 5. Poster
    poster_url = None
    og_img = soup.find("meta", {"property": "og:image"}) or soup.find("meta", {"name": "twitter:image"})
    if og_img and og_img.get("content"):
        poster_url = og_img["content"].strip()
    if not poster_url:
        img_el = soup.find("img")
        if img_el and img_el.get("src"):
            src = img_el["src"]
            if "poster" in src:
                poster_url = src

    # 6. Rating check
    rating = extract_rating_from_text(html)
    if rating is not None and min_rating > 0.0 and rating < min_rating:
        return None

    full_url = f"https://bot.kawaii.uz/anime/{slug}"

    return QueueItem(
        id=f"kawaii_{slug}",
        source="kawaii",
        title=title,
        original_title=original_title,
        year=year,
        media_type=media_type,
        url=full_url,
        poster_url=poster_url,
        episodes_count=episodes_count
    )


async def parse_kawaii_page_async(
    session: aiohttp.ClientSession,
    page: int = 1,
    min_rating: float = 0.0,
    media_type: str = "all"
) -> List[QueueItem]:
    """
    Asynchronously parses a page of anime from Kawaii.uz.
    Uses sitemap indexing: page 1 -> first 20 items, page 2 -> next 20 items.
    """
    slugs = await get_all_kawaii_slugs(session)
    if not slugs:
        return []

    start_idx = max(0, (page - 1) * PAGE_SIZE)
    end_idx = start_idx + PAGE_SIZE
    page_slugs = slugs[start_idx:end_idx]

    if not page_slugs:
        return []

    tasks = [
        session.get(
            f"https://bot.kawaii.uz/anime/{slug}",
            headers=HEADERS,
            ssl=False,
            timeout=aiohttp.ClientTimeout(total=12)
        )
        for slug in page_slugs
    ]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    items: List[QueueItem] = []
    for slug, resp in zip(page_slugs, responses):
        if isinstance(resp, Exception) or getattr(resp, "status", 0) != 200:
            continue
        try:
            html = await resp.text(errors="ignore")
            item = parse_anime_html_to_item(slug, html, min_rating=min_rating)
            if item:
                if media_type != "all" and item.media_type != media_type:
                    continue
                items.append(item)
        except Exception as e:
            logger.warning(f"Error parsing kawaii anime {slug}: {e}")

    return items


def parse_kawaii_page(page: int = 1, min_rating: float = 0.0, media_type: str = "all") -> List[QueueItem]:
    """
    Synchronous wrapper for parse_kawaii_page_async.
    """
    async def _runner():
        conn = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=conn) as session:
            return await parse_kawaii_page_async(session, page=page, min_rating=min_rating, media_type=media_type)

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If in running loop (e.g. jupyter or nest_asyncio), run in executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                return executor.submit(asyncio.run, _runner()).result()
        return loop.run_until_complete(_runner())
    except RuntimeError:
        return asyncio.run(_runner())


async def search_kawaii_async(
    query: str,
    session: Optional[aiohttp.ClientSession] = None
) -> List[QueueItem]:
    """
    Searches anime on Kawaii using @kawaii_uz_bot inline query,
    or falls back to sitemap filtering.
    """
    clean_q = query.strip()
    if not clean_q or len(clean_q) < 2:
        return []

    # 1. Try inline query via Telethon
    try:
        from scraper.telethon_moderator_pipeline import create_telethon_client
        client = create_telethon_client()
        await client.connect()
        if await client.is_user_authorized():
            res = await client.inline_query("kawaii_uz_bot", clean_q)
            items = []
            for r in res:
                t = getattr(r, "title", "") or ""
                if t.startswith("📕"):
                    t = t[1:].strip()
                t_clean = t.split("/")[0].strip() if "/" in t else t.strip()
                orig_t = t.split("/")[1].strip() if "/" in t else None

                slug = None
                poster_url = None
                if hasattr(r, "result") and r.result:
                    b_res = r.result
                    if hasattr(b_res, "thumb") and b_res.thumb and hasattr(b_res.thumb, "url"):
                        poster_url = b_res.thumb.url
                    # Find slug from send_message entities or reply_markup
                    sm = getattr(b_res, "send_message", None)
                    if sm:
                        for e in getattr(sm, "entities", []):
                            if hasattr(e, "url") and e.url and "/anime/" in e.url:
                                slug = e.url.split("/anime/")[-1].strip("/")
                                break
                            elif hasattr(e, "url") and e.url and "start=a-" in e.url:
                                slug = e.url.split("start=a-")[-1].strip("/")
                                break
                        if not slug and hasattr(sm, "reply_markup") and sm.reply_markup:
                            for row in getattr(sm.reply_markup, "rows", []):
                                for b in getattr(row, "buttons", []):
                                    b_url = getattr(getattr(b, "type", None), "url", None)
                                    if b_url and "/anime/" in b_url:
                                        slug = b_url.split("/anime/")[-1].strip("/")
                                        break
                                if slug:
                                    break

                desc = getattr(r, "description", "") or ""
                year = None
                m_y = re.search(r'\b(19\d\d|20\d\d)\b', desc)
                if m_y:
                    year = int(m_y.group(1))

                is_movie = bool("film" in t_clean.lower() or "1 •" in desc)
                media_type = "movie" if is_movie else "series"

                item_id = f"kawaii_{slug}" if slug else f"kawaii_{abs(hash(t_clean)) % 100000}"
                full_url = f"https://bot.kawaii.uz/anime/{slug}" if slug else "https://bot.kawaii.uz"

                items.append(QueueItem(
                    id=item_id,
                    source="kawaii",
                    title=t_clean,
                    original_title=orig_t,
                    year=year,
                    media_type=media_type,
                    url=full_url,
                    poster_url=poster_url
                ))
            await client.disconnect()
            if items:
                return items
    except Exception as e:
        logger.debug(f"Kawaii inline search error: {e}")

    return []

