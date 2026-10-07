import re
import urllib.request
import logging
import asyncio
from typing import List, Optional
import aiohttp
from bs4 import BeautifulSoup
from .queue_manager import QueueItem, QueueManager

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

from .title_cleaner import clean_scraped_title, clean_movie_title_simple

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_clean_title(raw_text: str, slug: str = "") -> str:
    res = clean_scraped_title(raw_text, url_or_slug=slug)
    return res["title"]

def _extract_uzmovi_items_from_html(html: str) -> List[QueueItem]:
    items: List[QueueItem] = []
    soup = BeautifulSoup(html, "html.parser")
    articles = soup.find_all("article", class_=lambda c: c and "shortstory" in c)
    seen_ids = set()

    # Agar article lar mavjud bo'lsa - aniq katalog kartalarini olamiz (sidebar reyting raqamlari tushmaydi)
    if articles:
        for art in articles:
            link = art.find("a", class_="short-images-link") or (art.find("h4").find("a") if art.find("h4") else None)
            if not link or not link.get("href"):
                continue

            href = link["href"]
            m = re.search(r'/(\d+)-([a-zA-Z0-9_\-]+)\.html', href)
            if not m:
                continue

            item_id_num = m.group(1)
            if item_id_num in seen_ids:
                continue
            seen_ids.add(item_id_num)

            raw_title = link.get("title") or link.get_text().strip()
            cleaned = clean_scraped_title(raw_title, url_or_slug=m.group(2))
            if not cleaned["title"] or len(cleaned["title"]) < 2:
                continue

            is_series = bool(re.search(r'(serial|barcha qismlar|mavsum|fasl|dorama|multiserial)', href + " " + raw_title, re.IGNORECASE))
            media_type = "series" if is_series else "movie"

            img = art.find("img")
            poster_url = None
            if img:
                src = img.get("src") or img.get("data-src")
                if src and not any(skip in src.lower() for skip in ["icon", "logo", "avatar", "blank"]):
                    poster_url = src if src.startswith("http") else f"https://uzmovi.net{src}"

            full_url = href if href.startswith("http") else f"https://uzmovi.net{href}"
            items.append(QueueItem(
                id=f"uzmovi_{item_id_num}",
                source="uzmovi",
                title=cleaned["title"],
                original_title=None,
                year=cleaned["year"],
                media_type=media_type,
                url=full_url,
                poster_url=poster_url
            ))
        return items

    # Fallback: oddiy linklar bo'yicha
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.endswith(".html"):
            continue

        m = re.search(r'/(\d+)-([a-zA-Z0-9_\-]+)\.html', href)
        if not m:
            continue

        item_id_num = m.group(1)
        if item_id_num in seen_ids:
            continue

        # Sidebar va TOP reyting bloklarini chetlab o'tish
        parents_str = " ".join(p.get("class", []) if isinstance(p.get("class"), list) else [str(p.get("class", ""))] for p in a.parents)
        if any(skip in parents_str.lower() for skip in ["sidebar", "top-", "rating"]):
            continue

        raw_title = a.get("title") or a.get_text().strip()
        if not raw_title or len(raw_title) < 2 or raw_title.lower() in ["bosh sahifa", "aloqa", "sayt qoidasi"]:
            continue

        cleaned = clean_scraped_title(raw_title, url_or_slug=m.group(2))
        if not cleaned["title"] or len(cleaned["title"]) < 2:
            continue

        seen_ids.add(item_id_num)
        is_series = bool(re.search(r'(serial|barcha qismlar|mavsum|fasl|dorama)', href + " " + raw_title, re.IGNORECASE))
        media_type = "series" if is_series else "movie"

        poster_url = None
        img = a.find("img") or (a.parent.find("img") if a.parent else None)
        if img:
            src = img.get("src") or img.get("data-src")
            if src and not any(skip in src.lower() for skip in ["icon", "logo", "avatar", "blank"]):
                poster_url = src if src.startswith("http") else f"https://uzmovi.net{src}"

        full_url = href if href.startswith("http") else f"https://uzmovi.net{href}"
        items.append(QueueItem(
            id=f"uzmovi_{item_id_num}",
            source="uzmovi",
            title=cleaned["title"],
            original_title=None,
            year=cleaned["year"],
            media_type=media_type,
            url=full_url,
            poster_url=poster_url
        ))
    return items

def _extract_asilmedia_items_from_html(html: str) -> List[QueueItem]:
    items: List[QueueItem] = []
    soup = BeautifulSoup(html, "html.parser")
    seen_ids = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.endswith(".html"):
            continue

        m = re.search(r'/(\d+)-([a-zA-Z0-9_\-]+)\.html', href)
        if not m:
            continue

        item_id_num = m.group(1)
        if item_id_num in seen_ids:
            continue

        card = a.find_parent(["article", "div"], class_=lambda c: c and "card" in c)
        title_el = card.find(class_=lambda x: x and "title" in x) if card else None
        img = (card.find("img") if card else None) or a.find("img")

        raw_title = (
            (title_el.get_text().strip() if title_el else None)
            or (img.get("alt") if img else None)
            or a.get("title")
            or a.get_text().strip()
        )

        if not raw_title or len(raw_title) < 2 or raw_title.lower() in ["tomosha qilish", "bosh sahifa", "aloqa", "qoidalar"]:
            raw_title = m.group(2).replace("-", " ").title()

        cleaned = clean_scraped_title(raw_title, url_or_slug=m.group(2))
        if not cleaned["title"] or len(cleaned["title"]) < 2:
            continue

        seen_ids.add(item_id_num)

        is_series = bool(re.search(r'(serial|barcha qismlar|mavsum|fasl|dorama|multiserial)', href + " " + raw_title, re.IGNORECASE))
        media_type = "series" if is_series else "movie"

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
                    poster_url = f"https://asilmedia.org{src if src.startswith('/') else '/' + src}"

        full_url = href if href.startswith("http") else f"https://asilmedia.org{href}"
        items.append(QueueItem(
            id=f"asilmedia_{item_id_num}",
            source="asilmedia",
            title=cleaned["title"],
            original_title=None,
            year=cleaned["year"],
            media_type=media_type,
            url=full_url,
            poster_url=poster_url
        ))
    return items

def parse_uzmovi_page(page_url: str) -> List[QueueItem]:
    import ssl
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        target_url = page_url.replace("uzmovi.com", "uzmovi.net")
        req = urllib.request.Request(target_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        return _extract_uzmovi_items_from_html(html)
    except Exception as e:
        logger.error(f"Error scraping Uzmovi page {page_url}: {e}")
        return []

def parse_asilmedia_page(page_url: str) -> List[QueueItem]:
    import ssl
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(page_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        return _extract_asilmedia_items_from_html(html)
    except Exception as e:
        logger.error(f"Error scraping Asilmedia page {page_url}: {e}")
        return []

async def parse_uzmovi_page_async(session: aiohttp.ClientSession, page_url: str) -> List[QueueItem]:
    target_url = page_url.replace("uzmovi.com", "uzmovi.net")
    if "/tarjima-kinolar/" in target_url:
        target_url = target_url.replace("/tarjima-kinolar/", "/tarjima-kinolarri/")
    elif target_url.endswith("/tarjima-kinolar"):
        target_url = target_url.replace("/tarjima-kinolar", "/tarjima-kinolarri")

    try:
        async with session.get(target_url, headers=HEADERS, ssl=False, timeout=aiohttp.ClientTimeout(total=12)) as resp:
            if resp.status == 200:
                html = await resp.text(errors="ignore")
                return _extract_uzmovi_items_from_html(html)
            else:
                logger.warning(f"Uzmovi HTTP {resp.status} for {target_url}")
    except Exception as e:
        logger.error(f"Async error scraping Uzmovi {target_url}: {e}")
        # Agar uzmovi.net xato bersa, uzmovi.com orqali sinab ko'rish
        if "uzmovi.net" in target_url:
            fb_url = target_url.replace("uzmovi.net", "uzmovi.com")
            try:
                async with session.get(fb_url, headers=HEADERS, ssl=False, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                    if resp.status == 200:
                        html = await resp.text(errors="ignore")
                        return _extract_uzmovi_items_from_html(html)
            except Exception as e2:
                logger.error(f"Fallback Uzmovi error: {e2}")
    return []

async def parse_asilmedia_page_async(session: aiohttp.ClientSession, page_url: str) -> List[QueueItem]:
    try:
        async with session.get(page_url, headers=HEADERS, ssl=False, timeout=aiohttp.ClientTimeout(total=12)) as resp:
            if resp.status == 200:
                html = await resp.text(errors="ignore")
                return _extract_asilmedia_items_from_html(html)
            else:
                logger.warning(f"Asilmedia HTTP {resp.status} for {page_url}")
    except Exception as e:
        logger.error(f"Async error scraping Asilmedia {page_url}: {e}")
    return []
