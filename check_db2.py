import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://neondb_owner:npg_2eToVwtng7Os@ep-frosty-cherry-aitqstf5-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require')
    res = await conn.fetch('SELECT * FROM seasons WHERE id = 7')
    print('Season 7:', res)
    if res:
        series_id = res[0]['series_id']
        res2 = await conn.fetch('SELECT * FROM series WHERE id = $1', series_id)
        print('Series:', res2)
        
    # Also check episode translations
    trans = await conn.fetch('SELECT * FROM episode_translations WHERE episode_id = 9')
    print('Translations:', trans)
    
    await conn.close()

asyncio.run(main())
