import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def check_range():
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=10.0)
    for code in range(6120, 6170):
        url = f"https://uzmovi.net/tarjima-kinolarri/{code}-test.html"
        try:
            r = await client.get(url, follow_redirects=True)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                title_tag = soup.find("title") or soup.find("h1")
                t_text = title_tag.get_text(strip=True) if title_tag else ""
                if "404" not in t_text and "topilmadi" not in t_text.lower():
                    print(f"Code {code}: {t_text}")
        except Exception:
            pass
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(check_range())
