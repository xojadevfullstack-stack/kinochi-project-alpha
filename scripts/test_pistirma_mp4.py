import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def check_pistirma_video():
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=10.0)
    for ep in [1, 2, 50, 100, 300]:
        url = f"https://xmuzon.com/seriallar/Pistirma%20{ep}.mp4"
        try:
            r = await client.head(url)
            cl = r.headers.get("content-length")
            mb = round(int(cl)/1024/1024, 1) if cl else "unknown"
            print(f"Ep {ep} ({url}) -> Status: {r.status_code}, Size: {mb} MB")
        except Exception as e:
            print(f"Ep {ep} err: {e}")
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(check_pistirma_video())
