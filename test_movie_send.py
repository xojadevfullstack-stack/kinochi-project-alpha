import asyncio
import os
import sys

# add backend and bot to path
sys.path.insert(0, os.path.abspath('bot'))

from bot.services.api_client import api_client
from bot.utils.movie_sender import send_movie_to_user

async def main():
    res = await api_client.search_movies(query="a", limit=1)
    movies = res.get("items", [])
    if not movies:
        print("no movies")
        return
    
    movie = movies[0]
    print(movie)
    
    class MockBot:
        async def send_video(self, **kwargs):
            print("send_video", kwargs)
        async def send_message(self, **kwargs):
            print("send_message", kwargs)
        async def copy_message(self, **kwargs):
            print("copy_message", kwargs)
            
    bot = MockBot()
    try:
        await send_movie_to_user(bot, 123, movie)
        print("Success")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
