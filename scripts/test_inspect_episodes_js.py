import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def inspect_episodes_js():
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=15.0)
    r = await client.get("https://uzmovi.net/js/episodes.js?v=1792540318")
    print("episodes.js length:", len(r.text))
    # print snippets containing endpoint or url or ajax or qism
    for line in r.text.splitlines():
        if any(w in line.lower() for w in ["fetch", "ajax", "endpoint", "url", "telegram", "pusu", "season"]):
            print("  ", line.strip()[:140])
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(inspect_episodes_js())
