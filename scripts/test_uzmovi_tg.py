import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def check_uzmovi_tg():
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=10.0, follow_redirects=False)
    r = await client.get("https://uzmovi.net/go/telegram/main-channel")
    print("Redirect location:", r.headers.get("location"))
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(check_uzmovi_tg())
