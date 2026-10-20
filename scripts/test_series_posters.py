import asyncio
import httpx
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

POSTERS = {
    "Breaking Bad": "https://image.tmdb.org/t/p/w500/anFx9aTOOYqgS3v7x3R84Kz67ly.jpg",
    "The Boys": "https://image.tmdb.org/t/p/w500/in1R2dDc421JxsoRWaIIAqVI2KE.jpg",
    "Sherlock": "https://image.tmdb.org/t/p/w500/7WTsnHkbA0FaG6R9twfFde0I9hl.jpg",
    "The Continental": "https://image.tmdb.org/t/p/w500/eiJeWeCAEZAmRppnXHiTWDcCd3Q.jpg",
    "All of Us Are Dead": "https://image.tmdb.org/t/p/w500/pTEFqAjLd5YTsMD6NSUxV6Dq7A6.jpg",
    "Dark": "https://image.tmdb.org/t/p/w500/wSXJHO9WHLb0aCwvQrtco7vOmWA.jpg",
    "The Witcher": "https://image.tmdb.org/t/p/w500/AoGsDM02UVt0npBA8OvpDcZbaMi.jpg",
    "Vikings": "https://image.tmdb.org/t/p/w500/bQLrHIRNEkE3PdIWQrZHynQZazu.jpg",
    "Prison Break": "https://image.tmdb.org/t/p/w500/wnmNPaLvhnMeOqnWlhNkYCZxtda.jpg",
    "Teen Wolf": "https://image.tmdb.org/t/p/w500/wjKBTcNy1xihmExqJI8kM2qvavP.jpg"
}

async def check():
    async with httpx.AsyncClient(timeout=10) as client:
        for name, url in POSTERS.items():
            try:
                res = await client.get(url)
                print(f"{name}: {res.status_code} ({len(res.content)} bytes)")
            except Exception as e:
                print(f"{name}: ERROR {e}")

asyncio.run(check())
