import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx, re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def inspect_ajax_calls():
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=15.0)

    for js_name in ["episodes.js", "app.js", "playerjs.js", "movie-media-switch.js"]:
        url = f"https://uzmovi.net/js/{js_name}"
        r = await client.get(url)
        print(f"\n=== {js_name} (status {r.status_code}) ===")
        # search for /ajax/ or /engine/ or /api/
        matches = set(re.findall(r'["\'](/[^"\']*(?:ajax|episode|serial|engine|api)[^"\']*)["\']', r.text, re.IGNORECASE))
        for m in matches:
            print("  Endpoint:", m)

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(inspect_ajax_calls())
