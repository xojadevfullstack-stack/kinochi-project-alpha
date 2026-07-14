import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        r = await client.get('https://kinochi-project.onrender.com/api/series/by-source?chat_id=-1004498937122&topic_id=2')
        print(r.status_code, r.text)

if __name__ == "__main__":
    asyncio.run(main())
