import sys
import os
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))
from app.utils.trailer import validate_and_normalize_trailer_url

async def main():
    urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://t.me/kinochi_uz/1234",
        "https://t.me/c/123456789/100",
        "https://www.w3schools.com/html/mov_bbb.mp4", # reliable small mp4
        "https://example.com/not_a_video_link"
    ]
    
    print("Trailer Normalization Test\n" + "="*50)
    for url in urls:
        print(f"Input:  {url}")
        try:
            res = await validate_and_normalize_trailer_url(url)
            print(f"Output: {res}")
        except Exception as e:
            print(f"Error:  {type(e).__name__} - {getattr(e, 'detail', str(e))}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
