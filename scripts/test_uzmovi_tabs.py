import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx, re
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def inspect_441_tabs():
    url = "https://uzmovi.net/serialar/441-qashqirlar-makoni-1-va-2-fasl-uzbek-ozbek-tilida-barcha-qismlari-toliq-qashqirlar-makoni-pusu-pistirma-uzbek-ozbek-tilida-toliq-onlayn-korish.html"
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=15.0)
    r = await client.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    print("=== Buttons / Links with 'telegram' or 'yuklash' ===")
    for a in soup.find_all("a"):
        txt = a.get_text(strip=True)
        href = a.get("href", "")
        if any(w in txt.lower() or w in href.lower() for w in ["telegram", "yuklash", "pusu", "tanlash", "qism"]):
            print(f"Text: '{txt}' -> href: '{href}' | class: {a.get('class')}")

    print("\n=== Buttons with class or id ===")
    for b in soup.find_all("button"):
        print(f"Button: '{b.get_text(strip=True)}' | attrs: {b.attrs}")

    print("\n=== Tabs / Divs ===")
    for div in soup.find_all("div", class_=re.compile(r"tab|season|episode|series", re.I)):
        print(f"Div class: {div.get('class')} | id: {div.get('id')}")

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(inspect_441_tabs())
