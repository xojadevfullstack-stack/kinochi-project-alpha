import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def check_domains():
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=10.0, follow_redirects=True)
    for domain in ["https://uzmovi.com", "https://uzmovi.net", "https://uzmovi.tv"]:
        try:
            r = await client.get(domain)
            print(f"{domain} -> final url: {r.url} (status: {r.status_code})")
        except Exception as e:
            print(f"{domain} -> error: {e}")
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(check_domains())
