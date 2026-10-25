import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx, re
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def find_uzmovi_pusu_page():
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=15.0)

    # Let's check page 441 first
    url = "https://uzmovi.net/serialar/441-qashqirlar-makoni-1-va-2-fasl-uzbek-ozbek-tilida-barcha-qismlari-toliq-qashqirlar-makoni-pusu-pistirma-uzbek-ozbek-tilida-toliq-onlayn-korish.html"
    r = await client.get(url)
    print("Page 441 length:", len(r.text))
    if "QISMLARDAN TANLASH" in r.text or "qismlardan tanlash" in r.text.lower():
        print("Found 'QISMLARDAN TANLASH' on page 441!")
    if "300-qism" in r.text or "96-qism" in r.text:
        print("Found '300-qism' or '96-qism' on page 441!")

    # Let's search all scripts or divs for 'pusu' or '96' or '300'
    matches = re.findall(r'[^\n]+(?:qismlardan tanlash|pusu|300-qism|telegram orqali yuklash)[^\n]+', r.text, re.IGNORECASE)
    print(f"Matches on page 441 ({len(matches)}):")
    for m in matches[:10]:
        print("  ", m.strip()[:120])

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(find_uzmovi_pusu_page())
