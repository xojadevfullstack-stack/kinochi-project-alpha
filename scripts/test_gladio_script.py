import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx, re
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def inspect_gladio_full():
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=15.0)
    url_gladio = "https://uzmovi.net/tarjima-kinolarri/6125-qashqirlar-makoni-gladio-premyera-uzbek-ozbek-tilida-onlayn-korish.html"
    r = await client.get(url_gladio)
    soup = BeautifulSoup(r.text, "html.parser")
    for s in soup.find_all("script"):
        c = s.string or ""
        if "story.uzmovi.net" in c or "file" in c or ".mp4" in c or ".m3u8" in c:
            print("Found script snippet:")
            print(c[:400])
            print("---")
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(inspect_gladio_full())
