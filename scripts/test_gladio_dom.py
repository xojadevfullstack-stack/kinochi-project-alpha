import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def inspect_full_gladio_page():
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=15.0)
    url_gladio = "https://uzmovi.net/tarjima-kinolarri/6125-qashqirlar-makoni-gladio-premyera-uzbek-ozbek-tilida-onlayn-korish.html"
    r = await client.get(url_gladio)
    soup = BeautifulSoup(r.text, "html.parser")

    # Let's see what is inside the main content / player area
    for tag in soup.find_all(True):
        t_id = tag.get("id", "")
        t_cls = " ".join(tag.get("class", []))
        if any(w in t_id.lower() or w in t_cls.lower() for w in ["player", "video", "serial", "film", "kino"]):
            print(f"<{tag.name} id='{t_id}' class='{t_cls}'>: {tag.get_text(strip=True)[:100]}")

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(inspect_full_gladio_page())
