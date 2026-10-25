import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx, re
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def dump_all_options():
    url = "https://uzmovi.me/seriall/serial/256-qashqirlar-makoni-pistirma-kurtlar-vadisi-pusu-1-700-710-750-760-770-780-790-800-qism-uzbek-tilida-barcha-qismlari.html"
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=15.0, follow_redirects=True)
    r = await client.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    select_tag = soup.find("select", id="series")
    if select_tag:
        options = select_tag.find_all("option")
        print(f"Total options: {len(options)}")
        for opt in options[:10]:
            print(f"  {opt.get_text(strip=True)} -> {opt.get('value')}")
        print("  ...")
        for opt in options[-10:]:
            print(f"  {opt.get_text(strip=True)} -> {opt.get('value')}")
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(dump_all_options())
