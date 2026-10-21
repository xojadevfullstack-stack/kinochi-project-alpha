import asyncio
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv('.env.local')
load_dotenv('.env')

from scraper.site_search import search_sites

async def main():
    queries = ["Qashqirlar makoni", "Muro", "Pistirma"]
    for q in queries:
        print(f"\n=== SEARCH: {q} ===")
        res = await search_sites(q)
        for r in res:
            print(f"  {r.get('title')} [{r.get('source')}] -> {r.get('source_url')}")

if __name__ == '__main__':
    asyncio.run(main())
