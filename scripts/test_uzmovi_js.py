import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx, re
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def inspect_uzmovi_js():
    url = "https://uzmovi.net/serialar/441-qashqirlar-makoni-1-va-2-fasl-uzbek-ozbek-tilida-barcha-qismlari-toliq-qashqirlar-makoni-pusu-pistirma-uzbek-ozbek-tilida-toliq-onlayn-korish.html"
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=15.0)
    r = await client.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    # find all script src
    for s in soup.find_all("script"):
        src = s.get("src", "")
        if src:
            print("Script src:", src)

    # find any inline js with ajax or fetch or player
    for s in soup.find_all("script"):
        c = s.string or ""
        if any(w in c for w in ["ajax", "playlist", "episodes", "qism", "serial", "pusu"]):
            print("Inline script snippet:")
            print(c[:300])
            print("---")

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(inspect_uzmovi_js())
