import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, httpx
from dotenv import load_dotenv

load_dotenv(".env.local")
load_dotenv("backend/.env")

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

async def get_tmdb_posters():
    client = httpx.AsyncClient(timeout=10.0)

    # Movies
    for m_id, name in [(14197, "Iroq"), (54159, "Falastin"), (472093, "Vatan")]:
        url = f"https://api.themoviedb.org/3/movie/{m_id}?api_key={TMDB_API_KEY}"
        r = await client.get(url)
        data = r.json()
        poster = f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}" if data.get('poster_path') else None
        print(f"Movie {name} ({m_id}): {poster}")

    # Series
    url = f"https://api.themoviedb.org/3/tv/3122?api_key={TMDB_API_KEY}"
    r = await client.get(url)
    data = r.json()
    poster = f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}" if data.get('poster_path') else None
    print(f"Series Kurtlar Vadisi (3122): {poster}")

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(get_tmdb_posters())
