import asyncio
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.series import SeriesModel
from sqlalchemy import select

async def main():
    async with async_session_factory() as session:
        result = await session.execute(select(SeriesModel))
        for s in result.scalars().all():
            print(f"ID: {s.id}, Title: {s.title}, Chat: {s.source_chat_id}, Topic: {s.source_topic_id}")

if __name__ == "__main__":
    asyncio.run(main())
