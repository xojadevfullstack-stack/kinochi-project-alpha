import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx, re
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def inspect_uzmovi_pages():
    client = httpx.AsyncClient(headers=HEADERS, verify=False, timeout=15.0)

    # 1. Gladio
    url_gladio = "https://uzmovi.net/tarjima-kinolarri/6125-qashqirlar-makoni-gladio-premyera-uzbek-ozbek-tilida-onlayn-korish.html"
    print(f"=== Inspecting Gladio: {url_gladio} ===")
    r = await client.get(url_gladio)
    soup = BeautifulSoup(r.text, "html.parser")
    # find iframes, scripts, or download links
    for iframe in soup.find_all("iframe"):
        print("  Iframe src:", iframe.get("src"))
    for a in soup.find_all("a", href=True):
        if any(w in a["href"] for w in ["t.me", "telegram", "download", ".mp4", "bot"]):
            print("  Link:", a.get_text(strip=True), "->", a["href"])

    # 2. Serial 441
    url_serial = "https://uzmovi.net/serialar/441-qashqirlar-makoni-1-va-2-fasl-uzbek-ozbek-tilida-barcha-qismlari-toliq-qashqirlar-makoni-pusu-pistirma-uzbek-ozbek-tilida-toliq-onlayn-korish.html"
    print(f"\n=== Inspecting Serial 441: {url_serial} ===")
    r = await client.get(url_serial)
    soup = BeautifulSoup(r.text, "html.parser")
    for iframe in soup.find_all("iframe"):
        print("  Iframe src:", iframe.get("src"))
    for a in soup.find_all("a", href=True):
        if any(w in a["href"] for w in ["t.me", "telegram", "download", ".mp4", "bot"]):
            print("  Link:", a.get_text(strip=True), "->", a["href"])

    # Look for series episodes select or player scripts
    selects = soup.find_all("select")
    print(f"Select elements: {len(selects)}")
    for s in selects:
        opts = s.find_all("option")
        print(f"  Select with {len(opts)} options:")
        for o in opts[:5]:
            print(f"    Option: {o.get_text(strip=True)} -> value={o.get('value')}")

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(inspect_uzmovi_pages())
