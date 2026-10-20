import asyncio
import os
import sys
from dotenv import load_dotenv

BASE_DIR = r"c:\Users\Администратор\Desktop\kino bot project\kinochi project"
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)
load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.infrastructure.db.session import async_session_factory
from sqlalchemy import text

async def check():
    async with async_session_factory() as session:
        # Check translations for movies 128, 134, 139, 143, 147, 156, 160, 168, 172, 176, 182, 187, 191, 196
        sample_ids = [128, 134, 139, 143, 147, 156, 160, 168, 172, 176, 182, 187, 191, 196]
        sql = """
            SELECT m.id, m.title, m.code, m.source_chat_id, m.source_topic_id, 
                   mt.id, mt.language, mt.telegram_file_id, mt.storage_channel_message_id
            FROM movies m
            LEFT JOIN movie_translations mt ON mt.movie_id = m.id
            WHERE m.id = ANY(:ids)
            ORDER BY m.id
        """
        res = await session.execute(text(sql), {"ids": sample_ids})
        rows = res.fetchall()
        for r in rows:
            t = r[1].encode('ascii', 'replace').decode()
            chat_id = r[3]
            topic_id = r[4]
            trans_id = r[5]
            lang = r[6]
            has_file = bool(r[7])
            st_msg = r[8]
            print(f"Movie {r[0]}: {t} | ChatID={chat_id}, TopicID={topic_id} | TransID={trans_id}, Lang={lang}, StMsgID={st_msg}, HasFileID={has_file}")

if __name__ == "__main__":
    asyncio.run(check())
