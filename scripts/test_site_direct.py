import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def search_sites():
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=15.0)

    # Search uzmovi
    print("=== Searching uzmovi.net for 'qashqirlar' ===")
    try:
        r = await client.get("https://uzmovi.net/search?q=qashqirlar")
        print(f"Uzmovi status: {r.status_code}")
        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.find_all("div", class_="short-story") or soup.find_all("a")
        found = []
        for a in soup.find_all("a", href=True):
            if "qashqirlar" in a["href"] or "qashqirlar" in (a.get_text() or "").lower() or "kurtlar" in (a.get_text() or "").lower():
                found.append((a.get_text(strip=True), a["href"]))
        print(f"Found {len(found)} links:")
        for title, href in found[:15]:
            print(f"  {title} -> {href}")
    except Exception as e:
        print(f"Uzmovi error: {e}")

    # Search asilmedia
    print("\n=== Searching asilmedia.org for 'qashqirlar' ===")
    try:
        r = await client.get("https://asilmedia.org/index.php?do=search&subaction=search&story=qashqirlar")
        print(f"Asilmedia status: {r.status_code}")
        soup = BeautifulSoup(r.text, "html.parser")
        found = []
        for a in soup.find_all("a", href=True):
            txt = a.get_text(strip=True)
            if "qashqirlar" in a["href"] or "qashqirlar" in txt.lower() or "kurtlar" in txt.lower():
                found.append((txt, a["href"]))
        print(f"Found {len(found)} links:")
        for title, href in found[:15]:
            print(f"  {title} -> {href}")
    except Exception as e:
        print(f"Asilmedia error: {e}")

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(search_sites())
