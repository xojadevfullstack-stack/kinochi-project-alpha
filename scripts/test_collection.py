import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def inspect_collection():
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=15.0)

    print("=== Checking Asilmedia Collection ===")
    r = await client.get("https://asilmedia.org/kolleksiya/qashqirlar-makoni-barcha-qismlari/")
    soup = BeautifulSoup(r.text, "html.parser")
    for a in soup.find_all("a", href=True):
        if "/1" in a["href"]:
            print(f"  {a.get_text(strip=True)} -> {a['href']}")

    print("\n=== Searching Asilmedia for Gladio ===")
    r = await client.get("https://asilmedia.org/index.php?do=search&subaction=search&story=gladio")
    soup = BeautifulSoup(r.text, "html.parser")
    for a in soup.find_all("a", href=True):
        if "gladio" in a.get_text(strip=True).lower() or "gladio" in a["href"].lower():
            print(f"  {a.get_text(strip=True)} -> {a['href']}")

    print("\n=== Searching Asilmedia for Muro ===")
    r = await client.get("https://asilmedia.org/index.php?do=search&subaction=search&story=muro")
    soup = BeautifulSoup(r.text, "html.parser")
    for a in soup.find_all("a", href=True):
        if "muro" in a.get_text(strip=True).lower() or "muro" in a["href"].lower():
            print(f"  {a.get_text(strip=True)} -> {a['href']}")

    print("\n=== Searching Uzmovi for Gladio, Muro, Pistirma ===")
    for q in ["gladio", "muro", "pistirma", "pusu", "kurtlar"]:
        r = await client.get(f"https://uzmovi.net/search?q={q}")
        soup = BeautifulSoup(r.text, "html.parser")
        found = [a for a in soup.find_all("a", href=True) if ".html" in a["href"]]
        print(f"Uzmovi query '{q}': {len(found)} results")
        for a in found[:3]:
            print(f"  {a.get_text(strip=True)} -> {a['href']}")

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(inspect_collection())
