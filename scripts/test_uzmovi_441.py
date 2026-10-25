import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx, json, re
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def inspect_uzmovi_441():
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=15.0)
    url = "https://uzmovi.net/serialar/441-qashqirlar-makoni-1-va-2-fasl-uzbek-ozbek-tilida-barcha-qismlari-toliq-qashqirlar-makoni-pusu-pistirma-uzbek-ozbek-tilida-toliq-onlayn-korish.html"
    r = await client.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    # find scripts with json playlist
    for s in soup.find_all("script"):
        c = s.string or ""
        if "story.uzmovi.net" in c and "file" in c:
            try:
                # find json array [ ... ]
                m = re.search(r'\[\s*\{.*\}\s*\]', c, re.DOTALL)
                if m:
                    arr = json.loads(m.group(0))
                    print(f"Uzmovi 441 has {len(arr)} episodes!")
                    for item in arr[:10]:
                        print(" ", item.get("id"), item.get("title"))
                    print("...")
                    for item in arr[-5:]:
                        print(" ", item.get("id"), item.get("title"))
            except Exception as e:
                print("Error parsing playlist:", e)

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(inspect_uzmovi_441())
