import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://neondb_owner:npg_2eToVwtng7Os@ep-frosty-cherry-aitqstf5-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require')
    res = await conn.fetch("SELECT * FROM movies WHERE code = 'BRGRNS'")
    print(res)
    await conn.close()

asyncio.run(main())
