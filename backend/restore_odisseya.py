import asyncio
from app.infrastructure.db.session import async_session_factory
from sqlalchemy import text

async def check_and_restore():
    async with async_session_factory() as session:
        # Check if 807 exists
        res807 = await session.execute(text("SELECT id FROM movies WHERE id = 807"))
        if res807.fetchone():
            print("Movie 807 already exists!")
            return

        # Insert Movie 807
        insert_movie = text("""
            INSERT INTO movies (
                id, code, title, original_title, description, release_year,
                runtime, genres, poster_url, tmdb_rating, created_at, updated_at,
                tmdb_id, director, "cast", trailer_url, publish_status, is_18_plus
            ) VALUES (
                807, :code, :title, :original_title, :description, :release_year,
                :runtime, :genres, :poster_url, :tmdb_rating, NOW(), NOW(),
                :tmdb_id, :director, :cast, :trailer_url, 'published', false
            )
        """)

        movie_data = {
            "code": "8P6XNL",
            "title": "Odisseya",
            "original_title": "The Odyssey",
            "description": "Troya urushidan so‘ng Itaka qiroli Odissey kichik qo‘shini bilan rafiqasi Penelopaning oldiga — uyiga qaytish uchun yo‘lga chiqadi. Safar davomida u ko‘plab sinovlarga duch kelib, sikloplar, sirenalar va odamxo‘r devlar bilan to‘qnashadi.",
            "release_year": 2026,
            "runtime": 173,
            "genres": "Sarguzasht, Jangari, Fantastika",
            "poster_url": "https://image.tmdb.org/t/p/w500/5rhTDKUhPYvpdQIijFIs5VoWsON.jpg",
            "tmdb_rating": 8.0,
            "tmdb_id": 1368337,
            "director": "Кристофер Нолан",
            "cast": "Мэтт Деймон, Том Холланд, Энн Хэтэуэй, Роберт Паттинсон, Химеш Патель",
            "trailer_url": "https://www.youtube.com/watch?v=xjLLXdYldzA"
        }

        await session.execute(insert_movie, movie_data)
        print("Inserted movie 807!")

        # Insert movie_translation for 807
        # Storage msg is 1637
        insert_trans = text("""
            INSERT INTO movie_translations (
                movie_id, language, telegram_file_id, storage_channel_message_id, created_at
            ) VALUES (
                807, 'O''zbekcha', NULL, 1637, NOW()
            )
        """)
        await session.execute(insert_trans)
        print("Inserted movie_translation for 807 (storage msg 1637)!")

        await session.commit()
        print("Transaction committed successfully!")

if __name__ == "__main__":
    asyncio.run(check_and_restore())
