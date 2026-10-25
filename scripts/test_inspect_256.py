import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx, re
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def inspect_256():
    url = "https://uzmovi.me/seriall/serial/256-qashqirlar-makoni-pistirma-kurtlar-vadisi-pusu-1-700-710-750-760-770-780-790-800-qism-uzbek-tilida-barcha-qismlari.html"
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=15.0, follow_redirects=True)
    r = await client.get(url)
    print("Page 256 status:", r.status_code, "len:", len(r.text))
    soup = BeautifulSoup(r.text, "html.parser")

    # Check for tabs:
    # "QISMLARDAN TANLASH", "QISMLARDAN TANLASH (PUSU)", "TELEGRAM ORQALI YUKLASH"
    for btn in soup.find_all(class_=lambda c: c and any(k in str(c) for k in ["tab", "btn", "select", "qism"])):
        print("Btn:", btn.get_text(strip=True)[:50], btn.attrs)

    # Check all links
    print("\n--- Links with telegram, t.me, or qism ---")
    for a in soup.find_all("a", href=True):
        if any(k in a["href"] for k in ["t.me", "telegram", "qism", "serial"]) or "qism" in a.get_text(strip=True).lower():
            print(f"  {a.get_text(strip=True)[:60]} -> {a['href']}")

    # Check iframes
    for ifr in soup.find_all("iframe"):
        print("  Iframe src:", ifr.get("src"))

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(inspect_256())
