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
    res = await search_sites('Qashqirlar makoni')
    print(f"Found items count: {len(res)}")
    for r in res:
        print(f"Title: {r.get('title')} | Source: {r.get('source')} | URL: {r.get('source_url')}")

if __name__ == '__main__':
    asyncio.run(main())
