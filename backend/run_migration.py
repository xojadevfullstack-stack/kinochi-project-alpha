import os
import sys
import asyncio
import asyncpg

DATABASE_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("XATO: DATABASE_URL yoki TEST_DATABASE_URL muhit o'zgaruvchisi o'rnatilmagan.")
    sys.exit(1)
DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

async def run_migration():
    with open('add_series_sources.sql', 'r') as f:
        sql = f.read()
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        for statement in sql.split(';'):
            statement = statement.strip()
            if statement:
                print(f"Executing: {statement}")
                await conn.execute(statement)
        print("Migration complete!")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
