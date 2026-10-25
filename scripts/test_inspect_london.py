import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def inspect_london():
    url = "https://uzmovi.me/seriall/serial/256-qashqirlar-makoni-pistirma-kurtlar-vadisi-pusu-1-700-710-750-760-770-780-790-800-qism-uzbek-tilida-barcha-qismlari.html"
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=15.0, follow_redirects=True)
    r = await client.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    london = soup.find(id="London")
    if london:
        print("London snippet:")
        print(london.prettify()[:1000])
        # Find all buttons/options/links in London
        buttons = london.find_all(["button", "a", "option", "li", "span"])
        print(f"\nTotal elements in London: {len(buttons)}")
        for b in buttons[:20]:
            print(" ", b.name, b.get_text(strip=True), b.attrs)
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(inspect_london())
