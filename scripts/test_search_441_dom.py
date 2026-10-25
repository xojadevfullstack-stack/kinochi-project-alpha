import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx, re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def search_441():
    url = "https://uzmovi.net/serialar/441-qashqirlar-makoni-1-va-2-fasl-uzbek-ozbek-tilida-barcha-qismlari-toliq-qashqirlar-makoni-pusu-pistirma-uzbek-ozbek-tilida-toliq-onlayn-korish.html"
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=15.0)
    r = await client.get(url)

    for pattern in [r"Treyler", r"Telegram orqali", r"1-qism", r"Pusu"]:
        matches = [m.start() for m in re.finditer(pattern, r.text, re.IGNORECASE)]
        print(f"Pattern '{pattern}': {len(matches)} matches")
        for pos in matches[:4]:
            snippet = r.text[max(0, pos-80):min(len(r.text), pos+120)].replace("\n", " ")
            print("   ...", snippet, "...")

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(search_441())
