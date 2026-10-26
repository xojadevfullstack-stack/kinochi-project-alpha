"""
Kinochilar (kinochilar.com / @kinochilar_fast_bot) parser for Kinochi Project.
Parses movie/series cards, handles deep-links, ratings, posters, and quality indicators.
"""

import re
import ssl
import logging
import urllib.request
from typing import List, Optional
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

BASE_URL = "https://kinochilar.com"


def extract_rating(text: str) -> Optional[float]:
    if not text:
        return None
    m = re.search(r'(?:imdb|kp|kinopoisk|rating|reyting)\s*[:\-–]?\s*([1-9](?:\.\d)?)\b', text, re.I)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    m_star = re.search(r'[⭐★]\s*([1-9](?:\.\d)?)\b', text)
    if m_star:
        try:
            return float(m_star.group(1))
        except ValueError:
            pass
    return None


def _extract_kinochilar_items_from_html(html: str, min_rating: float = 0.0) -> List[QueueItem]:
    items: List[QueueItem] = []
    soup = BeautifulSoup(html, "html.parser")
    seen_ids = set()

    # Find movie cards
    cards = soup.find_all(class_=lambda c: c and any(k in str(c).lower() for k in ["movie-card", "shortstory", "card", "film-card"]))
    if not cards:
        cards = soup.find_all("article")

    for c in cards:
        # Find detail link
        title_a = None
        for a in c.find_all("a", href=True):
            href = a["href"]
            if re.search(r'/(\d+)-([a-zA-Z0-9_\-]+)\.html', href):
                title_a = a
                # Prefer the anchor with text length > 3
                t = a.get_text().strip()
                if t and len(t) > 3 and not any(bad in t.lower() for bad in ["tomosha", "fhd", "4k", "hd", "qilish"]):
                    break

        if not title_a:
            continue

        href = title_a["href"]
        m = re.search(r'/(\d+)-([a-zA-Z0-9_\-]+)\.html', href)
        if not m:
            continue

        item_id_num = m.group(1)
        slug = m.group(2)
        if item_id_num in seen_ids:
            continue

        img = c.find("img")
        raw_title = (
            (img.get("alt") if img else None)
            or title_a.get("title")
            or title_a.get_text().strip()
        )

        if not raw_title or len(raw_title) < 2 or raw_title.lower() in ["tomosha qilish", "bosh sahifa", "aloqa"]:
            raw_title = slug.replace("-", " ").title()

        card_text = c.get_text().lower() + " " + href.lower() + " " + raw_title.lower()
        if any(unrel in card_text for unrel in [
            "tez kunda", "kutilmoqda", "premyera kutilmoqda", "faqat treyler"
        ]):
            continue

        rating = extract_rating(card_text)
        if rating is not None and min_rating > 0.0 and rating < min_rating:
            continue

        cleaned = clean_scraped_title(raw_title, url_or_slug=slug)
        if not cleaned["title"] or len(cleaned["title"]) < 2:
            continue

        seen_ids.add(item_id_num)

        # Detect media type
        combined_text = (href + " " + raw_title).lower()
        is_series = bool(re.search(r'(tarjima-seriallar|serial|barcha qismlar|mavsum|fasl|dorama)', combined_text))
        if "anime" in combined_text or "/anime" in href.lower():
            media_type = "anime"
        elif "dorama" in combined_text or "/dorama" in href.lower() or (is_series and any(w in combined_text for w in ["koreys", "xitoy"])):
            media_type = "dorama"
        elif any(w in combined_text for w in ["multfilm", "multik", "/multfilm"]):
            media_type = "multfilm"
        elif is_series:
            media_type = "series"
        else:
            media_type = "movie"

        # Poster URL
        poster_url = None
        if img:
            src = img.get("src") or img.get("data-src")
            if src and not any(skip in src.lower() for skip in ["icon", "logo", "avatar", "blank"]):
                src = src.strip()
                if src.startswith("//"):
                    poster_url = f"https:{src}"
                elif src.startswith("http"):
                    poster_url = src
                else:
                    poster_url = f"{BASE_URL}{src if src.startswith('/') else '/' + src}"

        full_url = href if href.startswith("http") else f"{BASE_URL}{href if href.startswith('/') else '/' + href}"

        # Quality indicator if present in card
        detected_quality = None
        if "4k" in card_text:
            detected_quality = "4K"
        elif any(k in card_text for k in ["1080", "fhd"]):
            detected_quality = "1080p"
        elif any(k in card_text for k in ["720", "hd"]):
            detected_quality = "720p"

        items.append(QueueItem(
            id=f"kinochilar_{item_id_num}",
            source="kinochilar",
            title=cleaned["title"],
            original_title=None,
            year=cleaned["year"],
            media_type=media_type,
            url=full_url,
            poster_url=poster_url,
            payload={"quality_tag": detected_quality} if detected_quality else None
        ))

    return items


def fetch_kinochilar_start_hash(page_url: str) -> Optional[str]:
    """
    Fetches the movie/series detail page and extracts the Telegram bot start hash:
    https://t.me/kinochilar_fast_bot?start=<HASH> -> returns <HASH>
    """
    import ssl
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(page_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        m = re.search(r'kinochilar_fast_bot\?start=([a-zA-Z0-9_\-]+)', html)
        if m:
            return m.group(1)
    except Exception as e:
        logger.error(f"Error fetching kinochilar start hash for {page_url}: {e}")
    return None


async def fetch_kinochilar_start_hash_async(session: aiohttp.ClientSession, page_url: str) -> Optional[str]:
    try:
        async with session.get(page_url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                html = await resp.text(errors="ignore")
                m = re.search(r'kinochilar_fast_bot\?start=([a-zA-Z0-9_\-]+)', html)
                if m:
                    return m.group(1)
    except Exception as e:
        logger.error(f"Async error fetching kinochilar start hash for {page_url}: {e}")
    return None


def parse_kinochilar_page(page_url: str, min_rating: float = 0.0) -> List[QueueItem]:
    import ssl
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(page_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        return _extract_kinochilar_items_from_html(html, min_rating=min_rating)
    except Exception as e:
        logger.error(f"Error scraping Kinochilar page {page_url}: {e}")
        return []


async def parse_kinochilar_page_async(session: aiohttp.ClientSession, page_url: str, min_rating: float = 0.0) -> List[QueueItem]:
    try:
        async with session.get(page_url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=12)) as resp:
            if resp.status == 200:
                html = await resp.text(errors="ignore")
                return _extract_kinochilar_items_from_html(html, min_rating=min_rating)
            else:
                logger.warning(f"Kinochilar HTTP {resp.status} for {page_url}")
    except Exception as e:
        logger.error(f"Async error scraping Kinochilar {page_url}: {e}")
    return []
