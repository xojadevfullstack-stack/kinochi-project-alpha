import asyncio
from app.infrastructure.db.session import async_session_factory
from sqlalchemy import text

async def check():
    async with async_session_factory() as session:
        # Check columns of movie_translations
        cols = await session.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'movie_translations'"))
        print('movie_translations columns:', cols.fetchall())

        # Check Odisseya
        res = await session.execute(text("SELECT id, title, original_title, tmdb_id, release_year, poster_url FROM movies WHERE title ILIKE '%odisseya%' OR original_title ILIKE '%odyssey%'"))
        print('Odisseya in DB:', res.fetchall())
        
        # Check Interstellar
        res2 = await session.execute(text("SELECT m.id, m.title, mt.id as trans_id, mt.storage_channel_message_id, mt.telegram_file_id FROM movies m LEFT JOIN movie_translations mt ON m.id = mt.movie_id WHERE m.title ILIKE '%interstellar%' ORDER BY m.id"))
        print('Interstellar:', res2.fetchall())

        # Check Titanik
        res3 = await session.execute(text("SELECT m.id, m.title, mt.id as trans_id, mt.storage_channel_message_id, mt.telegram_file_id FROM movies m LEFT JOIN movie_translations mt ON m.id = mt.movie_id WHERE m.title ILIKE '%titanik%' ORDER BY m.id"))
        print('Titanik:', res3.fetchall())

        # Check Uzuklar
        res4 = await session.execute(text("SELECT m.id, m.title, mt.id as trans_id, mt.storage_channel_message_id, mt.telegram_file_id FROM movies m LEFT JOIN movie_translations mt ON m.id = mt.movie_id WHERE m.title ILIKE '%uzuklar%' ORDER BY m.id"))
        print('Uzuklar:', res4.fetchall())

        # Total movies
        res5 = await session.execute(text("SELECT count(*) FROM movies"))
        print('Total movies:', res5.scalar())

        # Recent 20 movies
        res6 = await session.execute(text("SELECT id, code, title, release_year FROM movies ORDER BY id DESC LIMIT 20"))
        print('Recent 20 movies:')
        for r in res6.fetchall():
            print(r)

if __name__ == '__main__':
    asyncio.run(check())
