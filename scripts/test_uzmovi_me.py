import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def search_uzmovi_me():
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=15.0, follow_redirects=True)
    r = await client.get("https://uzmovi.me/index.php?do=search&subaction=search&story=qashqirlar")
    print(f"uzmovi.me status: {r.status_code}")
    soup = BeautifulSoup(r.text, "html.parser")
    for a in soup.find_all("a", href=True):
        if ".html" in a["href"] and ("qashqir" in a["href"] or "qashqir" in a.get_text(strip=True).lower()):
            print(f"  {a.get_text(strip=True)} -> {a['href']}")
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(search_uzmovi_me())
