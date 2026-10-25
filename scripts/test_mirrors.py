import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def check_uzmovi_mirrors():
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=10.0, follow_redirects=True)
    for u in ["https://uzmovi.tv", "https://uzmovi.me", "https://uzmovi.net"]:
        try:
            r = await client.get(u)
            print(f"{u} -> status: {r.status_code}, url: {r.url}, title: {r.text[:100].replace(chr(10), ' ')}")
        except Exception as e:
            print(f"{u} -> err: {e}")
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(check_uzmovi_mirrors())
