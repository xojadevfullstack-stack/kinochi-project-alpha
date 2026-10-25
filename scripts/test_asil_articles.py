import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def inspect_articles():
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=15.0)

    for q in ["pistirma", "kurtlar"]:
        url = f"https://asilmedia.org/index.php?do=search&subaction=search&story={q}"
        r = await client.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        articles = soup.find_all("article") or soup.find_all(class_=lambda c: c and "short" in str(c))
        print(f"Query '{q}': found {len(articles)} article elements")
        for a in articles:
            h2 = a.find("h2") or a.find("a")
            print("  Article:", h2.get_text(strip=True) if h2 else a.get_text(strip=True)[:50])

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(inspect_articles())
