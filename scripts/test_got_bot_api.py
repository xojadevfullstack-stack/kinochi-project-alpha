import asyncio
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('.env')

BASE_DIR = os.path.abspath('.')
BOT_DIR = os.path.join(BASE_DIR, 'bot')
if BOT_DIR not in sys.path:
    sys.path.insert(0, BOT_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from bot.services.api_client import api_client

async def main():
    try:
        print("1. Testing search_series('Taxtlar')...")
        res = await api_client.search_series('Taxtlar')
        items = res.get('items', [])
        print(f"Search results: {len(items)} items")
        for it in items:
            print(f"  ID: {it.get('id')} | Title: {it.get('title')} | Year: {it.get('release_year')}")

        if items:
            sid = items[0]['id']
            series = await api_client.get_series_by_id(sid)
            print(f"\n2. Series details for ID {sid}:")
            print(f"  Title: {series.get('title')}")
            print(f"  Rating: {series.get('imdb_rating')}")
            print(f"  Total seasons: {len(series.get('seasons', []))}")

        print("\n3. Testing get_episode_by_code('S1-CH1')...")
        ep1 = await api_client.get_episode_by_code('S1-CH1')
        if ep1:
            print(f"  Episode found! Title: {ep1.get('title')}, Code: {ep1.get('code')}, Display: {ep1.get('display_code')}")
            print(f"  Translations: {ep1.get('translations')}")
        else:
            print("  Episode S1-CH1 not found!")

        print("\n4. Testing get_episode_by_code('S8-CH6')...")
        ep8 = await api_client.get_episode_by_code('S8-CH6')
        if ep8:
            print(f"  Episode found! Title: {ep8.get('title')}, Code: {ep8.get('code')}, Display: {ep8.get('display_code')}")
            print(f"  Translations: {ep8.get('translations')}")
        else:
            print("  Episode S8-CH6 not found!")

        print("\n5. Testing live_search('Taxtlar')...")
        ls = await api_client.live_search('Taxtlar')
        print(f"  Live search returned {len(ls.get('results', []))} results:")
        for r in ls.get('results', []):
            print(f"    Type: {r.get('type')} | Title: {r.get('title')}")

    finally:
        await api_client.close()

if __name__ == '__main__':
    asyncio.run(main())
