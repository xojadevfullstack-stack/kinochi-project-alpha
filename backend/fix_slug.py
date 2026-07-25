import asyncio
from app.infrastructure.db.session import engine
from sqlalchemy import text

async def fix():
    async with engine.connect() as conn:
        await conn.execute(text("UPDATE pages SET slug = 'cartoon-animated-movie' WHERE id = 3"))
        await conn.commit()
        print("Updated successfully")

if __name__ == "__main__":
    asyncio.run(fix())
