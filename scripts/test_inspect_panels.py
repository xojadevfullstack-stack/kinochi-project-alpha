import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def inspect_panels():
    url = "https://uzmovi.net/serialar/441-qashqirlar-makoni-1-va-2-fasl-uzbek-ozbek-tilida-barcha-qismlari-toliq-qashqirlar-makoni-pusu-pistirma-uzbek-ozbek-tilida-toliq-onlayn-korish.html"
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=15.0)
    r = await client.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    panels = soup.find_all(class_=lambda c: c and "episode-season-panel" in str(c))
    print(f"Found {len(panels)} episode-season-panel elements")
    for p in panels:
        print("Panel id:", p.get("id"), "class:", p.get("class"))
        links = p.find_all("a")
        print(f"  Has {len(links)} episode links!")
        for a in links[:5]:
            print(f"    {a.get_text(strip=True)} -> {a.get('href')} | data: {a.attrs}")

    # Also search for buttons with data-episode-season-target
    targets = soup.find_all(attrs={"data-episode-season-target": True})
    print(f"\nFound {len(targets)} targets:")
    for t in targets:
        print(f"  Target: {t.get_text(strip=True)} -> {t.get('data-episode-season-target')}")

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(inspect_panels())
