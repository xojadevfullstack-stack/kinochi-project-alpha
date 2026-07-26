import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        res = await client.get("http://localhost:8000/api/v1/movies/code/BRGRNS")
        print(res.status_code)
        print(res.text)

asyncio.run(main())
