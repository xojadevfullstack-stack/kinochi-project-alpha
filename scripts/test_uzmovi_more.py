import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def search_more_uzmovi():
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=15.0)

    for q in ["lanat", "nalet", "qashqir", "qashqirlar makoni", "falastin", "vatan"]:
        r = await client.get(f"https://uzmovi.net/search?q={q}")
        soup = BeautifulSoup(r.text, "html.parser")
        found = []
        for a in soup.find_all("a", href=True):
            if ".html" in a["href"] and "rules.html" not in a["href"]:
                txt = a.get_text(strip=True)
                if txt and len(txt) > 3:
                    found.append((txt, a["href"]))
        print(f"\nUzmovi query '{q}': {len(found)} results")
        for txt, href in found[:8]:
            print(f"  {txt} -> {href}")

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(search_more_uzmovi())
