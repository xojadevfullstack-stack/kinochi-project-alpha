import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx, re
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def inspect_players():
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=15.0)

    for name, url in [
        ("Gladio", "https://uzmovi.net/tarjima-kinolarri/6125-qashqirlar-makoni-gladio-premyera-uzbek-ozbek-tilida-onlayn-korish.html"),
        ("Serial 441", "https://uzmovi.net/serialar/441-qashqirlar-makoni-1-va-2-fasl-uzbek-ozbek-tilida-barcha-qismlari-toliq-qashqirlar-makoni-pusu-pistirma-uzbek-ozbek-tilida-toliq-onlayn-korish.html")
    ]:
        print(f"\n================ {name} ================")
        r = await client.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        # search for player divs or scripts
        player = soup.find(id=re.compile(r"player|video", re.I)) or soup.find(class_=re.compile(r"player|video", re.I))
        if player:
            print("Player tag:", player.name, player.attrs)
            print("Player inner HTML snippet:", player.prettify()[:500])

        for s in soup.find_all("script"):
            src = s.get("src", "")
            content = s.string or ""
            if any(k in content for k in ["file:", "player", "series", "playlist", "mp4", "m3u8"]):
                print(f"Script (src={src}):")
                for line in content.splitlines():
                    if any(k in line for k in ["file:", "file", "playlist", "sources", "url"]):
                        print("  ", line.strip()[:150])

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(inspect_players())
