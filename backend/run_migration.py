import asyncio
import asyncpg

async def run_migration():
    with open('add_series_sources.sql', 'r') as f:
        sql = f.read()
    
    conn = await asyncpg.connect('postgresql://neondb_owner:npg_2eToVwtng7Os@ep-frosty-cherry-aitqstf5-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require')
    
    for statement in sql.split(';'):
        statement = statement.strip()
        if statement:
            print(f"Executing: {statement}")
            await conn.execute(statement)
            
    print("Migration complete!")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
