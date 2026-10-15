import os
import sys
import asyncio
import asyncpg

DATABASE_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("XATO: DATABASE_URL yoki TEST_DATABASE_URL muhit o'zgaruvchisi o'rnatilmagan.")
    sys.exit(1)
DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

async def main():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        res = await conn.fetch("SELECT * FROM movies WHERE code = 'BRGRNS'")
        print(res)
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
